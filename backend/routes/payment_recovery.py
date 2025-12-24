#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Payment Recovery Admin Routes
Handles payment mismatch detection and manual recovery
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc

from backend.database.connection import get_db_session
from backend.models.subscription_models import (
    Transaction, Subscription,
    PaymentStatus, SubscriptionStatus, SubscriptionPlan
)
from backend.routes.payment_confirmation import PaymentConfirmation, PaymentConfirmStatus
from backend.utils.auth_utils import require_admin

payment_recovery_bp = Blueprint('payment_recovery', __name__, url_prefix='/api/admin/payment-recovery')


@payment_recovery_bp.route('/mismatches', methods=['GET'])
@require_admin
def get_payment_mismatches():
    """
    Detect payment-plan mismatches

    Scenarios detected:
    1. Payment SUCCESS but subscription still PENDING/CANCELLED
    2. Payment SUCCESS but subscription plan doesn't match
    3. Payment SUCCESS but subscription period not extended
    4. Approved PaymentConfirmation but subscription not active

    Returns:
        {
            "mismatches": [
                {
                    "type": "payment_success_plan_not_active",
                    "transaction_id": "...",
                    "user_id": 123,
                    "payment_amount": 50000,
                    "payment_plan": "basic",
                    "current_plan": "free",
                    "payment_date": "2025-12-24T10:00:00",
                    "subscription_status": "pending",
                    "can_auto_fix": true,
                    "reason": "Payment succeeded but plan not activated"
                },
                ...
            ],
            "total": 5,
            "by_type": {
                "payment_success_plan_not_active": 3,
                "approved_transfer_not_applied": 2
            }
        }
    """
    session = get_db_session()
    mismatches = []

    try:
        # Type 1: Card payments (SUCCESS) but subscription not active
        successful_transactions = session.query(Transaction).filter(
            Transaction.status == PaymentStatus.SUCCESS,
            Transaction.payment_method.in_(['CARD', 'BILLING_KEY'])
        ).all()

        for txn in successful_transactions:
            # Find latest subscription for this user
            subscription = session.query(Subscription).filter(
                Subscription.user_id == txn.user_id
            ).order_by(desc(Subscription.created_at)).first()

            # Check if plan matches and is active
            if not subscription:
                mismatches.append({
                    'type': 'payment_success_no_subscription',
                    'transaction_id': txn.transaction_id,
                    'user_id': txn.user_id,
                    'payment_amount': txn.amount,
                    'payment_plan': txn.metadata.get('plan') if txn.metadata else 'unknown',
                    'current_plan': None,
                    'payment_date': txn.created_at.isoformat(),
                    'subscription_status': None,
                    'can_auto_fix': True,
                    'reason': 'Payment succeeded but no subscription exists'
                })
            elif subscription.status != SubscriptionStatus.ACTIVE:
                mismatches.append({
                    'type': 'payment_success_plan_not_active',
                    'transaction_id': txn.transaction_id,
                    'user_id': txn.user_id,
                    'payment_amount': txn.amount,
                    'payment_plan': txn.metadata.get('plan') if txn.metadata else 'unknown',
                    'current_plan': subscription.plan.value if subscription.plan else None,
                    'payment_date': txn.created_at.isoformat(),
                    'subscription_status': subscription.status.value,
                    'subscription_id': subscription.id,
                    'can_auto_fix': True,
                    'reason': f'Payment succeeded but subscription is {subscription.status.value}'
                })
            elif txn.metadata and subscription.plan.value != txn.metadata.get('plan'):
                mismatches.append({
                    'type': 'payment_success_plan_mismatch',
                    'transaction_id': txn.transaction_id,
                    'user_id': txn.user_id,
                    'payment_amount': txn.amount,
                    'payment_plan': txn.metadata.get('plan'),
                    'current_plan': subscription.plan.value,
                    'payment_date': txn.created_at.isoformat(),
                    'subscription_status': subscription.status.value,
                    'subscription_id': subscription.id,
                    'can_auto_fix': True,
                    'reason': f'Payment for {txn.metadata.get("plan")} but subscription is {subscription.plan.value}'
                })

        # Type 2: Approved bank transfers but subscription not active
        approved_confirmations = session.query(PaymentConfirmation).filter(
            PaymentConfirmation.status == PaymentConfirmStatus.APPROVED
        ).all()

        for confirm in approved_confirmations:
            subscription = session.query(Subscription).filter(
                Subscription.user_id == confirm.user_id
            ).order_by(desc(Subscription.created_at)).first()

            if not subscription or subscription.status != SubscriptionStatus.ACTIVE:
                mismatches.append({
                    'type': 'approved_transfer_not_applied',
                    'confirmation_id': confirm.id,
                    'user_id': confirm.user_id,
                    'payment_amount': confirm.amount,
                    'payment_plan': confirm.plan,
                    'current_plan': subscription.plan.value if subscription else None,
                    'payment_date': confirm.payment_date.isoformat(),
                    'subscription_status': subscription.status.value if subscription else None,
                    'subscription_id': subscription.id if subscription else None,
                    'can_auto_fix': True,
                    'reason': 'Bank transfer approved but subscription not activated'
                })

        # Count by type
        by_type = {}
        for mismatch in mismatches:
            mtype = mismatch['type']
            by_type[mtype] = by_type.get(mtype, 0) + 1

        return jsonify({
            'success': True,
            'mismatches': mismatches,
            'total': len(mismatches),
            'by_type': by_type
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@payment_recovery_bp.route('/<transaction_id>/apply', methods=['POST'])
@require_admin
def apply_payment_manually(transaction_id):
    """
    Manually apply a successful payment to user's subscription

    Args:
        transaction_id: Transaction ID or PaymentConfirmation ID

    Body:
        {
            "type": "transaction" | "confirmation",
            "plan": "basic" | "pro" | "expert" | "enterprise",
            "billing_period": "monthly" | "yearly",
            "reason": "Manual recovery due to webhook failure"
        }

    Returns:
        {
            "success": true,
            "subscription_id": 123,
            "plan": "basic",
            "expires_at": "2025-01-24T10:00:00"
        }
    """
    session = get_db_session()

    try:
        data = request.get_json()
        record_type = data.get('type', 'transaction')
        plan_str = data.get('plan')
        billing_period = data.get('billing_period', 'monthly')
        reason = data.get('reason', 'Manual recovery by admin')

        if not plan_str:
            return jsonify({'success': False, 'error': 'Plan is required'}), 400

        # Validate plan
        try:
            plan_enum = SubscriptionPlan[plan_str.upper()]
        except KeyError:
            return jsonify({'success': False, 'error': f'Invalid plan: {plan_str}'}), 400

        # Find the payment record
        if record_type == 'transaction':
            transaction = session.query(Transaction).filter(
                Transaction.transaction_id == transaction_id
            ).first()

            if not transaction:
                return jsonify({'success': False, 'error': 'Transaction not found'}), 404

            if transaction.status != PaymentStatus.SUCCESS:
                return jsonify({'success': False, 'error': 'Transaction is not successful'}), 400

            user_id = transaction.user_id
            amount = transaction.amount

        else:  # confirmation
            confirmation = session.query(PaymentConfirmation).filter(
                PaymentConfirmation.id == int(transaction_id)
            ).first()

            if not confirmation:
                return jsonify({'success': False, 'error': 'Payment confirmation not found'}), 404

            if confirmation.status != PaymentConfirmStatus.APPROVED:
                return jsonify({'success': False, 'error': 'Payment confirmation is not approved'}), 400

            user_id = confirmation.user_id
            amount = confirmation.amount

        # Find or create subscription
        subscription = session.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(desc(Subscription.created_at)).first()

        # Calculate period dates
        period_days = 365 if billing_period == 'yearly' else 30
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=period_days)

        if subscription:
            # Update existing subscription
            subscription.plan = plan_enum
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.billing_period = billing_period
            subscription.amount = amount
            subscription.current_period_start = start_date
            subscription.current_period_end = end_date
            subscription.updated_at = datetime.utcnow()
        else:
            # Create new subscription
            subscription = Subscription(
                user_id=user_id,
                plan=plan_enum,
                status=SubscriptionStatus.ACTIVE,
                billing_period=billing_period,
                amount=amount,
                current_period_start=start_date,
                current_period_end=end_date,
                created_at=datetime.utcnow()
            )
            session.add(subscription)

        # Add metadata about manual recovery
        if record_type == 'transaction' and transaction:
            if not transaction.metadata:
                transaction.metadata = {}
            transaction.metadata['manual_recovery'] = True
            transaction.metadata['recovery_reason'] = reason
            transaction.metadata['recovered_at'] = datetime.utcnow().isoformat()
            transaction.metadata['recovered_by'] = request.admin_email

        session.commit()

        return jsonify({
            'success': True,
            'subscription_id': subscription.id,
            'user_id': user_id,
            'plan': subscription.plan.value,
            'status': subscription.status.value,
            'amount': subscription.amount,
            'billing_period': subscription.billing_period,
            'current_period_start': subscription.current_period_start.isoformat(),
            'current_period_end': subscription.current_period_end.isoformat(),
            'recovery_info': {
                'type': record_type,
                'id': transaction_id,
                'reason': reason,
                'recovered_by': request.admin_email,
                'recovered_at': datetime.utcnow().isoformat()
            }
        })

    except Exception as e:
        session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@payment_recovery_bp.route('/transactions', methods=['GET'])
@require_admin
def get_all_transactions():
    """
    Get all transactions with filters

    Query params:
        - status: SUCCESS, FAILED, PENDING, CANCELLED
        - payment_method: CARD, BANK_TRANSFER, BILLING_KEY
        - user_id: Filter by user
        - limit: Max results (default 100)
        - offset: Pagination offset

    Returns:
        {
            "transactions": [...],
            "total": 150,
            "limit": 100,
            "offset": 0
        }
    """
    session = get_db_session()

    try:
        # Parse query params
        status = request.args.get('status')
        payment_method = request.args.get('payment_method')
        user_id = request.args.get('user_id', type=int)
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)

        # Build query
        query = session.query(Transaction)

        if status:
            try:
                status_enum = PaymentStatus[status.upper()]
                query = query.filter(Transaction.status == status_enum)
            except KeyError:
                return jsonify({'success': False, 'error': f'Invalid status: {status}'}), 400

        if payment_method:
            query = query.filter(Transaction.payment_method == payment_method)

        if user_id:
            query = query.filter(Transaction.user_id == user_id)

        # Get total count
        total = query.count()

        # Apply pagination
        transactions = query.order_by(desc(Transaction.created_at)).limit(limit).offset(offset).all()

        return jsonify({
            'success': True,
            'transactions': [txn.to_dict() for txn in transactions],
            'total': total,
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()
