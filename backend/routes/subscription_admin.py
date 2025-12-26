"""
CoinPulse Admin Subscription Management API
Admin endpoints for managing user subscriptions and plan features
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
from models.subscription_models import (
    Subscription, SubscriptionPlan, SubscriptionStatus,
    BillingPeriod, PLAN_PRICING
)

# Create Blueprint
subscription_admin_bp = Blueprint('subscription_admin', __name__, url_prefix='/api/admin/subscriptions')

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '7DfH2jzRD4lCfQ_llC4CObochoaGzaBBZLeODoftgWk')
ADMIN_EMAILS = ['ln9swrd@gmail.com']  # Admin email addresses


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
    """
    Decorator to require admin authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id, email, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        # Check if user is admin by email
        if email not in ADMIN_EMAILS:
            return jsonify({
                'success': False,
                'error': 'Admin access required',
                'code': 'FORBIDDEN'
            }), 403

        # Add user_id and email to request context
        request.admin_id = user_id
        request.admin_email = email

        return f(*args, **kwargs)

    return decorated_function


@subscription_admin_bp.route('/users/<int:user_id>', methods=['GET'])
@require_admin
def get_user_subscription(user_id):
    """
    Get user's subscription details

    Response:
    {
        "success": true,
        "subscription": {...},
        "user_id": 123
    }
    """
    try:
        with get_db_session() as session:
            subscription = session.query(Subscription).filter(
                Subscription.user_id == user_id
            ).order_by(Subscription.created_at.desc()).first()

            if not subscription:
                return jsonify({
                    'success': True,
                    'subscription': None,
                    'user_id': user_id,
                    'message': 'No subscription found'
                }), 200

            return jsonify({
                'success': True,
                'subscription': subscription.to_dict(),
                'user_id': user_id
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@subscription_admin_bp.route('/users/<int:user_id>/extend', methods=['POST'])
@require_admin
def extend_subscription(user_id):
    """
    Extend user's subscription period

    Request JSON:
    {
        "days": 30,  # Number of days to extend
        "reason": "Beta tester reward"  # Optional reason
    }

    Response:
    {
        "success": true,
        "subscription": {...},
        "extended_days": 30,
        "new_end_date": "2025-02-20T00:00:00"
    }
    """
    try:
        data = request.get_json()

        if 'days' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: days'
            }), 400

        days = data['days']
        reason = data.get('reason', 'Admin extension')

        with get_db_session() as session:
            # Get current subscription (status is stored as string)
            subscription = session.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.status == 'active'  # Compare with string, not Enum
            ).first()

            if not subscription:
                return jsonify({
                    'success': False,
                    'error': 'No active subscription found for user'
                }), 404

            # Extend the subscription
            if subscription.current_period_end:
                new_end_date = subscription.current_period_end + timedelta(days=days)
            else:
                new_end_date = datetime.utcnow() + timedelta(days=days)

            subscription.current_period_end = new_end_date
            subscription.updated_at = datetime.utcnow()

            session.commit()

            return jsonify({
                'success': True,
                'subscription': subscription.to_dict(),
                'extended_days': days,
                'new_end_date': new_end_date.isoformat(),
                'reason': reason,
                'extended_by_admin_id': request.admin_id
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@subscription_admin_bp.route('/users/<int:user_id>/plan', methods=['PUT'])
@require_admin
def change_user_plan(user_id):
    """
    Change user's subscription plan

    Request JSON:
    {
        "plan": "pro",  # free, basic, pro, enterprise
        "billing_period": "monthly",  # monthly, annual
        "reason": "Upgrade for beta tester"  # Optional
    }

    Response:
    {
        "success": true,
        "subscription": {...},
        "old_plan": "basic",
        "new_plan": "pro"
    }
    """
    try:
        data = request.get_json()

        if 'plan' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: plan'
            }), 400

        new_plan_str = data['plan']
        billing_period_str = data.get('billing_period', 'monthly')
        reason = data.get('reason', 'Admin plan change')

        # Validate plan
        try:
            new_plan = SubscriptionPlan(new_plan_str)
            billing_period = BillingPeriod(billing_period_str)
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid plan or billing period: {new_plan_str}, {billing_period_str}'
            }), 400

        with get_db_session() as session:
            # Get current subscription
            subscription = session.query(Subscription).filter(
                Subscription.user_id == user_id
            ).order_by(Subscription.created_at.desc()).first()

            if not subscription:
                # Create new subscription if none exists
                subscription = Subscription(
                    user_id=user_id,
                    plan=new_plan_str,  # Store as string, not Enum
                    billing_period=billing_period_str,  # Store as string, not Enum
                    status='active',  # Store as string, not Enum
                    amount=PLAN_PRICING.get(new_plan, {}).get(billing_period, 0) or 0,
                    started_at=datetime.utcnow(),
                    current_period_start=datetime.utcnow(),
                    current_period_end=datetime.utcnow() + timedelta(days=30 if billing_period == BillingPeriod.MONTHLY else 365)
                )
                session.add(subscription)
                old_plan = 'none'
            else:
                # subscription.plan is already a string, not an Enum
                old_plan = subscription.plan if isinstance(subscription.plan, str) else subscription.plan.value
                subscription.plan = new_plan_str  # Store as string
                subscription.billing_period = billing_period_str  # Store as string
                subscription.amount = PLAN_PRICING.get(new_plan, {}).get(billing_period, 0) or 0
                subscription.updated_at = datetime.utcnow()

                # If upgrading from free, set start dates
                if old_plan == 'free' and new_plan_str != 'free':
                    subscription.status = 'active'  # Store as string, not Enum
                    subscription.started_at = datetime.utcnow()
                    subscription.current_period_start = datetime.utcnow()
                    subscription.current_period_end = datetime.utcnow() + timedelta(
                        days=30 if billing_period == BillingPeriod.MONTHLY else 365
                    )

            session.commit()

            return jsonify({
                'success': True,
                'subscription': subscription.to_dict(),
                'old_plan': old_plan,
                'new_plan': new_plan_str,
                'reason': reason,
                'changed_by_admin_id': request.admin_id
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@subscription_admin_bp.route('/users/<int:user_id>/custom-period', methods=['POST'])
@require_admin
def set_custom_period(user_id):
    """
    Set custom subscription period for user

    Request JSON:
    {
        "start_date": "2025-01-01T00:00:00",  # Optional, defaults to now
        "end_date": "2025-12-31T23:59:59",    # Required
        "reason": "Special promotion"          # Optional
    }

    Response:
    {
        "success": true,
        "subscription": {...},
        "period_days": 365
    }
    """
    try:
        data = request.get_json()

        if 'end_date' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: end_date'
            }), 400

        start_date_str = data.get('start_date')
        end_date_str = data['end_date']
        reason = data.get('reason', 'Admin custom period')

        # Parse dates
        try:
            if start_date_str:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            else:
                start_date = datetime.utcnow()

            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid date format: {str(e)}'
            }), 400

        if end_date <= start_date:
            return jsonify({
                'success': False,
                'error': 'End date must be after start date'
            }), 400

        with get_db_session() as session:
            # Get current subscription
            subscription = session.query(Subscription).filter(
                Subscription.user_id == user_id
            ).order_by(Subscription.created_at.desc()).first()

            if not subscription:
                return jsonify({
                    'success': False,
                    'error': 'No subscription found for user. Create subscription first.'
                }), 404

            # Set custom period
            subscription.current_period_start = start_date
            subscription.current_period_end = end_date
            subscription.started_at = start_date
            subscription.status = 'active'  # Store as string, not Enum
            subscription.updated_at = datetime.utcnow()

            period_days = (end_date - start_date).days

            session.commit()

            return jsonify({
                'success': True,
                'subscription': subscription.to_dict(),
                'period_days': period_days,
                'reason': reason,
                'set_by_admin_id': request.admin_id
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@subscription_admin_bp.route('/users/<int:user_id>/cancel', methods=['POST'])
@require_admin
def admin_cancel_subscription(user_id):
    """
    Admin cancel user's subscription

    Request JSON:
    {
        "reason": "Policy violation",  # Optional
        "immediate": true               # Optional, default false (cancel at period end)
    }

    Response:
    {
        "success": true,
        "subscription": {...},
        "cancelled_at": "2025-01-20T12:34:56"
    }
    """
    try:
        data = request.get_json() or {}
        reason = data.get('reason', 'Admin cancellation')
        immediate = data.get('immediate', False)

        with get_db_session() as session:
            subscription = session.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.status == 'active'  # Compare with string, not Enum
            ).first()

            if not subscription:
                return jsonify({
                    'success': False,
                    'error': 'No active subscription found for user'
                }), 404

            subscription.status = 'cancelled'  # Store as string, not Enum
            subscription.cancelled_at = datetime.utcnow()

            if immediate:
                subscription.ended_at = datetime.utcnow()
                subscription.current_period_end = datetime.utcnow()

            subscription.updated_at = datetime.utcnow()

            session.commit()

            return jsonify({
                'success': True,
                'subscription': subscription.to_dict(),
                'cancelled_at': subscription.cancelled_at.isoformat(),
                'immediate': immediate,
                'reason': reason,
                'cancelled_by_admin_id': request.admin_id
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@subscription_admin_bp.route('/stats', methods=['GET'])
@require_admin
def get_subscription_stats():
    """
    Get subscription statistics

    Response:
    {
        "success": true,
        "stats": {
            "total_subscriptions": 150,
            "by_plan": {
                "free": 100,
                "basic": 30,
                "pro": 18,
                "enterprise": 2
            },
            "by_status": {
                "active": 120,
                "cancelled": 20,
                "expired": 10
            },
            "total_mrr": 4850000  # Monthly Recurring Revenue in KRW
        }
    }
    """
    try:
        with get_db_session() as session:
            # Total subscriptions
            total_subs = session.query(Subscription).count()

            # By plan
            by_plan = {}
            for plan in SubscriptionPlan:
                count = session.query(Subscription).filter(
                    Subscription.plan == plan
                ).count()
                by_plan[plan.value] = count

            # By status
            by_status = {}
            for status in SubscriptionStatus:
                count = session.query(Subscription).filter(
                    Subscription.status == status
                ).count()
                by_status[status.value] = count

            # Calculate MRR (Monthly Recurring Revenue)
            active_subs = session.query(Subscription).filter(
                Subscription.status == SubscriptionStatus.ACTIVE
            ).all()

            total_mrr = 0
            for sub in active_subs:
                if sub.billing_period == BillingPeriod.MONTHLY:
                    total_mrr += sub.amount
                elif sub.billing_period == BillingPeriod.ANNUAL:
                    total_mrr += sub.amount / 12  # Convert annual to monthly

            return jsonify({
                'success': True,
                'stats': {
                    'total_subscriptions': total_subs,
                    'by_plan': by_plan,
                    'by_status': by_status,
                    'total_mrr': int(total_mrr),
                    'currency': 'KRW'
                }
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@subscription_admin_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'subscription_admin',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
