"""
CoinPulse Payment Confirmation Admin API
Admin endpoints for reviewing bank transfer confirmations
"""

import os
import sys
from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime, timedelta
import jwt

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.connection import get_db_session
from payment_confirmation import PaymentConfirmation, PaymentConfirmStatus
from models.subscription_models import Subscription, SubscriptionPlan, SubscriptionStatus, BillingPeriod

# Create Blueprint
payment_confirm_admin_bp = Blueprint('payment_confirm_admin', __name__, url_prefix='/api/admin/payment-confirmations')

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '7DfH2jzRD4lCfQ_llC4CObochoaGzaBBZLeODoftgWk')
ADMIN_EMAILS = ['ln9swrd@gmail.com']


def verify_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, 'Token has expired'
    except jwt.InvalidTokenError:
        return None, 'Invalid token'


def get_current_user(request):
    """Get current user from Authorization header"""
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return None, None, 'Authorization header missing or invalid'

    token = auth_header.split(' ')[1]
    payload, error = verify_token(token)

    if error:
        return None, None, error

    return payload.get('user_id'), payload.get('email'), None


def require_admin(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id, email, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        if email not in ADMIN_EMAILS:
            return jsonify({
                'success': False,
                'error': 'Admin access required',
                'code': 'FORBIDDEN'
            }), 403

        request.admin_id = user_id
        request.admin_email = email
        return f(*args, **kwargs)

    return decorated_function


@payment_confirm_admin_bp.route('/pending', methods=['GET'])
@require_admin
def get_pending_confirmations():
    """
    Get all pending payment confirmations

    Query params:
    - limit: Number of results (default: 50)
    - offset: Offset for pagination (default: 0)

    Response:
    {
        "success": true,
        "confirmations": [...],
        "total": 10,
        "pending_count": 10
    }
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        session = get_db_session()

        # Get pending confirmations
        pending = session.query(PaymentConfirmation).filter(
            PaymentConfirmation.status == PaymentConfirmStatus.PENDING
        ).order_by(PaymentConfirmation.created_at.asc()).limit(limit).offset(offset).all()

        # Get total count
        total = session.query(PaymentConfirmation).filter(
            PaymentConfirmation.status == PaymentConfirmStatus.PENDING
        ).count()

        return jsonify({
            'success': True,
            'confirmations': [c.to_dict() for c in pending],
            'total': total,
            'pending_count': total,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@payment_confirm_admin_bp.route('/all', methods=['GET'])
@require_admin
def get_all_confirmations():
    """
    Get all payment confirmations (all statuses)

    Query params:
    - status: Filter by status (pending, approved, rejected)
    - limit: Number of results (default: 50)
    - offset: Offset for pagination (default: 0)

    Response:
    {
        "success": true,
        "confirmations": [...],
        "total": 100,
        "stats": {
            "pending": 10,
            "approved": 85,
            "rejected": 5
        }
    }
    """
    try:
        status_filter = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        session = get_db_session()

        query = session.query(PaymentConfirmation)

        if status_filter:
            try:
                status_enum = PaymentConfirmStatus(status_filter)
                query = query.filter(PaymentConfirmation.status == status_enum)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid status: {status_filter}'
                }), 400

        confirmations = query.order_by(
            PaymentConfirmation.created_at.desc()
        ).limit(limit).offset(offset).all()

        # Get statistics
        stats = {}
        for status in PaymentConfirmStatus:
            count = session.query(PaymentConfirmation).filter(
                PaymentConfirmation.status == status
            ).count()
            stats[status.value] = count

        total = sum(stats.values())

        return jsonify({
            'success': True,
            'confirmations': [c.to_dict() for c in confirmations],
            'total': total,
            'stats': stats,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@payment_confirm_admin_bp.route('/<int:confirmation_id>/approve', methods=['POST'])
@require_admin
def approve_payment(confirmation_id):
    """
    Approve payment confirmation and activate subscription

    Request JSON (optional):
    {
        "admin_notes": "입금 확인 완료"
    }

    Response:
    {
        "success": true,
        "confirmation": {...},
        "subscription": {...},
        "message": "Payment approved and subscription activated"
    }
    """
    try:
        data = request.get_json() or {}
        admin_notes = data.get('admin_notes', '')

        session = get_db_session()

        # Get confirmation
        confirmation = session.query(PaymentConfirmation).filter(
            PaymentConfirmation.id == confirmation_id
        ).first()

        if not confirmation:
            return jsonify({
                'success': False,
                'error': 'Payment confirmation not found'
            }), 404

        if confirmation.status != PaymentConfirmStatus.PENDING:
            return jsonify({
                'success': False,
                'error': f'Payment confirmation already {confirmation.status.value}'
            }), 400

        # Update confirmation status
        confirmation.status = PaymentConfirmStatus.APPROVED
        confirmation.reviewed_by_admin = request.admin_email
        confirmation.reviewed_at = datetime.utcnow()
        confirmation.admin_notes = admin_notes

        # Create or update subscription
        plan_enum = SubscriptionPlan(confirmation.plan)
        billing_enum = BillingPeriod(confirmation.billing_period)

        subscription = session.query(Subscription).filter(
            Subscription.user_id == confirmation.user_id
        ).order_by(Subscription.created_at.desc()).first()

        if subscription:
            # Update existing subscription
            subscription.plan = plan_enum
            subscription.billing_period = billing_enum
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.amount = confirmation.amount
            subscription.started_at = datetime.utcnow()
            subscription.current_period_start = datetime.utcnow()

            if billing_enum == BillingPeriod.MONTHLY:
                subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
            else:
                subscription.current_period_end = datetime.utcnow() + timedelta(days=365)

            subscription.updated_at = datetime.utcnow()
        else:
            # Create new subscription
            period_end = datetime.utcnow() + timedelta(
                days=30 if billing_enum == BillingPeriod.MONTHLY else 365
            )

            subscription = Subscription(
                user_id=confirmation.user_id,
                user_email=confirmation.user_email,
                plan=plan_enum,
                billing_period=billing_enum,
                status=SubscriptionStatus.ACTIVE,
                amount=confirmation.amount,
                started_at=datetime.utcnow(),
                current_period_start=datetime.utcnow(),
                current_period_end=period_end
            )
            session.add(subscription)

        session.commit()

        # TODO: Send email notification to user
        # send_approval_email(confirmation, subscription)

        return jsonify({
            'success': True,
            'confirmation': confirmation.to_dict(),
            'subscription': subscription.to_dict(),
            'message': 'Payment approved and subscription activated'
        }), 200

    except Exception as e:
        session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@payment_confirm_admin_bp.route('/<int:confirmation_id>/reject', methods=['POST'])
@require_admin
def reject_payment(confirmation_id):
    """
    Reject payment confirmation

    Request JSON:
    {
        "admin_notes": "입금 금액이 일치하지 않습니다"
    }

    Response:
    {
        "success": true,
        "confirmation": {...},
        "message": "Payment confirmation rejected"
    }
    """
    try:
        data = request.get_json()

        if 'admin_notes' not in data:
            return jsonify({
                'success': False,
                'error': 'admin_notes is required for rejection'
            }), 400

        session = get_db_session()

        confirmation = session.query(PaymentConfirmation).filter(
            PaymentConfirmation.id == confirmation_id
        ).first()

        if not confirmation:
            return jsonify({
                'success': False,
                'error': 'Payment confirmation not found'
            }), 404

        if confirmation.status != PaymentConfirmStatus.PENDING:
            return jsonify({
                'success': False,
                'error': f'Payment confirmation already {confirmation.status.value}'
            }), 400

        # Update confirmation status
        confirmation.status = PaymentConfirmStatus.REJECTED
        confirmation.reviewed_by_admin = request.admin_email
        confirmation.reviewed_at = datetime.utcnow()
        confirmation.admin_notes = data['admin_notes']

        session.commit()

        # TODO: Send email notification to user
        # send_rejection_email(confirmation)

        return jsonify({
            'success': True,
            'confirmation': confirmation.to_dict(),
            'message': 'Payment confirmation rejected'
        }), 200

    except Exception as e:
        session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@payment_confirm_admin_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'payment_confirmation_admin',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
