"""
CoinPulse Subscription API Routes
Flask Blueprint for subscription management
"""

import os
import sys
from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime
import jwt

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.subscription_service import SubscriptionService
from database.connection import get_db_session
from backend.models.subscription_models import Subscription, SubscriptionStatus, SubscriptionPlan
from backend.models.plan_config import PlanConfig
from backend.models.plan_features import get_user_features
from sqlalchemy import desc

# Create Blueprint
subscription_bp = Blueprint('subscription', __name__, url_prefix='/api/subscription')

# Initialize service
subscription_service = SubscriptionService()

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '7DfH2jzRD4lCfQ_llC4CObochoaGzaBBZLeODoftgWk')


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
        return None, 'Authorization header missing or invalid'

    token = auth_header.split(' ')[1]
    payload, error = verify_token(token)

    if error:
        return None, error

    return payload.get('user_id'), None


def require_auth(f):
    """
    Decorator to require JWT authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        # Add user_id to request context
        request.user_id = user_id

        return f(*args, **kwargs)

    return decorated_function


@subscription_bp.route('/upgrade', methods=['POST'])
@require_auth
def upgrade_subscription():
    """
    Create/Upgrade subscription

    Request JSON:
    {
        "plan": "premium",
        "billing": "monthly",
        "payment_method": "card",
        "billing_info": {
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "country": "KR"
        },
        "card": {
            "number": "4242424242424242",
            "expiry": "12/25",
            "cvc": "123",
            "name": "JOHN DOE"
        }
    }

    Response:
    {
        "success": true,
        "subscription": {...},
        "transaction": {...},
        "requires_payment": true
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['plan', 'billing', 'payment_method', 'billing_info']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Get user email from billing info or use placeholder
        user_email = data['billing_info'].get('email', f'user_{request.user_id}@coinpulse.com')

        # Create subscription
        result = subscription_service.create_subscription(
            user_id=request.user_id,
            user_email=user_email,
            plan=data['plan'],
            billing_period=data['billing'],
            payment_method=data['payment_method'],
            billing_info=data['billing_info'],
            card_info=data.get('card')
        )

        if not result['success']:
            return jsonify(result), 400

        # If requires payment, process mock payment
        if result.get('requires_payment'):
            transaction_id = result['transaction']['transaction_id']

            # Process mock payment (90% success rate)
            payment_result = subscription_service.mock_payment_process(
                transaction_id=transaction_id,
                success_rate=0.9
            )

            if payment_result['success']:
                return jsonify({
                    'success': True,
                    'subscription': payment_result.get('subscription'),
                    'transaction': payment_result.get('transaction'),
                    'redirect_url': f'/payment-success.html?plan={data["plan"]}&billing={data["billing"]}&txn={transaction_id}'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': payment_result.get('error', 'Payment failed'),
                    'error_code': payment_result['transaction'].get('error_code'),
                    'redirect_url': f'/payment-error.html?plan={data["plan"]}&billing={data["billing"]}&method={data["payment_method"]}&error={payment_result["transaction"].get("error_code")}'
                }), 400

        # Free plan or no payment required
        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@subscription_bp.route('/cancel', methods=['POST'])
@require_auth
def cancel_subscription():
    """
    Cancel subscription

    Request JSON:
    {
        "subscription_id": 123
    }

    Response:
    {
        "success": true,
        "subscription": {...},
        "message": "Subscription cancelled..."
    }
    """
    try:
        data = request.get_json()

        if 'subscription_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing subscription_id'
            }), 400

        result = subscription_service.cancel_subscription(
            subscription_id=data['subscription_id'],
            user_id=request.user_id
        )

        if not result['success']:
            return jsonify(result), 400

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@subscription_bp.route('/current', methods=['GET'])
@require_auth
def get_current_subscription():
    """
    Get user's current subscription

    Response:
    {
        "success": true,
        "subscription": {...}
    }
    """
    try:
        subscription = subscription_service.get_user_subscription(request.user_id)

        if subscription:
            return jsonify({
                'success': True,
                'subscription': subscription
            }), 200
        else:
            return jsonify({
                'success': True,
                'subscription': None,
                'message': 'No active subscription'
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@subscription_bp.route('/transactions', methods=['GET'])
@require_auth
def get_transactions():
    """
    Get user's transaction history

    Query params:
    - limit: Number of transactions (default: 10)

    Response:
    {
        "success": true,
        "transactions": [...]
    }
    """
    try:
        limit = request.args.get('limit', 10, type=int)

        transactions = subscription_service.get_user_transactions(
            user_id=request.user_id,
            limit=limit
        )

        return jsonify({
            'success': True,
            'transactions': transactions,
            'count': len(transactions)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@subscription_bp.route('/plans', methods=['GET'])
def get_plans():
    """
    Get available subscription plans

    Response:
    {
        "success": true,
        "plans": [...]
    }
    """
    try:
        from models.subscription_models import PLAN_PRICING, SubscriptionPlan, BillingPeriod

        plans = []
        for plan in SubscriptionPlan:
            plan_info = {
                'name': plan.value,
                'display_name': plan.name.title(),
                'pricing': {}
            }

            for billing in BillingPeriod:
                price = PLAN_PRICING.get(plan, {}).get(billing)
                plan_info['pricing'][billing.value] = {
                    'amount': price,
                    'currency': 'KRW',
                    'period': billing.value
                }

            plans.append(plan_info)

        return jsonify({
            'success': True,
            'plans': plans
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@subscription_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint

    Response:
    {
        "status": "healthy",
        "service": "subscription",
        "timestamp": "2025-11-30T12:34:56"
    }
    """
    return jsonify({
        'status': 'healthy',
        'service': 'subscription',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@subscription_bp.route('/current', methods=['GET'])
@require_auth
def get_current_subscription():
    """
    Get current user's subscription information

    Returns:
        {
            "success": true,
            "subscription": {
                "plan": "basic",
                "plan_name_ko": "베이직",
                "status": "active",
                "amount": 39000,
                "billing_period": "monthly",
                "started_at": "2025-12-01T00:00:00",
                "current_period_start": "2025-12-01T00:00:00",
                "current_period_end": "2025-12-31T23:59:59",
                "days_remaining": 7,
                "auto_renew": true,
                "next_billing_date": "2025-12-31T23:59:59"
            },
            "plan_features": {
                "max_advisory_coins": 5,
                "max_surge_alerts": 5,
                "telegram_alerts": true,
                ...
            },
            "usage": {
                "advisory_coins_used": 3,
                "surge_alerts_used": 2
            }
        }
    """
    session = get_db_session()

    try:
        user_id = request.user_id

        # Get latest subscription
        subscription = session.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(desc(Subscription.created_at)).first()

        if not subscription:
            # Return free plan default
            return jsonify({
                'success': True,
                'subscription': {
                    'plan': 'free',
                    'plan_name_ko': '무료',
                    'status': 'active',
                    'amount': 0,
                    'billing_period': None,
                    'started_at': None,
                    'current_period_start': None,
                    'current_period_end': None,
                    'days_remaining': None,
                    'auto_renew': False,
                    'next_billing_date': None
                },
                'plan_features': get_user_features('free'),
                'usage': {
                    'advisory_coins_used': 0,
                    'surge_alerts_used': 0
                }
            })

        # Calculate days remaining
        days_remaining = None
        if subscription.current_period_end:
            delta = subscription.current_period_end - datetime.utcnow()
            days_remaining = max(0, delta.days)

        # Get plan name from config
        plan_config = session.query(PlanConfig).filter(
            PlanConfig.plan_code == subscription.plan.value
        ).first()

        plan_name_ko = plan_config.plan_name_ko if plan_config else subscription.plan.value

        # Get plan features
        plan_features = get_user_features(subscription.plan.value)

        # TODO: Get actual usage from database (advisory coins, surge alerts)
        # For now, return placeholder
        usage = {
            'advisory_coins_used': 0,  # Query from advisory_coins table
            'surge_alerts_used': 0     # Query from surge_alert_history table
        }

        return jsonify({
            'success': True,
            'subscription': {
                'plan': subscription.plan.value,
                'plan_name_ko': plan_name_ko,
                'status': subscription.status.value,
                'amount': subscription.amount,
                'billing_period': subscription.billing_period,
                'started_at': subscription.current_period_start.isoformat() if subscription.current_period_start else None,
                'current_period_start': subscription.current_period_start.isoformat() if subscription.current_period_start else None,
                'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                'days_remaining': days_remaining,
                'auto_renew': False,  # TODO: Implement auto-renew logic
                'next_billing_date': subscription.current_period_end.isoformat() if subscription.current_period_end else None
            },
            'plan_features': plan_features,
            'usage': usage
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@subscription_bp.route('/history', methods=['GET'])
@require_auth
def get_subscription_history():
    """
    Get subscription change history

    Returns:
        {
            "success": true,
            "history": [
                {
                    "plan": "basic",
                    "plan_name_ko": "베이직",
                    "started_at": "2025-12-01",
                    "ended_at": "2025-12-31",
                    "amount": 39000,
                    "status": "active",
                    "billing_period": "monthly"
                },
                ...
            ]
        }
    """
    session = get_db_session()

    try:
        user_id = request.user_id

        # Get all subscriptions for user
        subscriptions = session.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(desc(Subscription.created_at)).all()

        history = []
        for sub in subscriptions:
            # Get plan name
            plan_config = session.query(PlanConfig).filter(
                PlanConfig.plan_code == sub.plan.value
            ).first()

            plan_name_ko = plan_config.plan_name_ko if plan_config else sub.plan.value

            history.append({
                'plan': sub.plan.value,
                'plan_name_ko': plan_name_ko,
                'started_at': sub.current_period_start.isoformat() if sub.current_period_start else sub.created_at.isoformat(),
                'ended_at': sub.current_period_end.isoformat() if sub.current_period_end else None,
                'amount': sub.amount,
                'status': sub.status.value,
                'billing_period': sub.billing_period
            })

        return jsonify({
            'success': True,
            'history': history
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@subscription_bp.route('/upgrade-options', methods=['GET'])
@require_auth
def get_upgrade_options():
    """
    Get available upgrade plans

    Returns:
        {
            "success": true,
            "current_plan": "basic",
            "upgrade_options": [
                {
                    "plan_code": "pro",
                    "plan_name_ko": "프로",
                    "monthly_price": 79000,
                    "annual_price": 790000,
                    "annual_discount": 158000,
                    "price_difference": 40000,
                    "features": {...}
                },
                ...
            ]
        }
    """
    session = get_db_session()

    try:
        user_id = request.user_id

        # Get current subscription
        subscription = session.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(desc(Subscription.created_at)).first()

        current_plan = subscription.plan.value if subscription else 'free'

        # Get all plan configs ordered by display_order
        all_plans = session.query(PlanConfig).filter(
            PlanConfig.is_active == True
        ).order_by(PlanConfig.display_order).all()

        # Filter upgrade options (plans higher than current)
        plan_hierarchy = ['free', 'basic', 'pro', 'expert', 'enterprise']
        current_index = plan_hierarchy.index(current_plan) if current_plan in plan_hierarchy else 0

        upgrade_options = []
        for plan in all_plans:
            # Skip free and current plan
            if plan.plan_code == 'free' or plan.plan_code == current_plan:
                continue

            # Only show higher tier plans
            try:
                plan_index = plan_hierarchy.index(plan.plan_code)
                if plan_index <= current_index:
                    continue
            except ValueError:
                # Unknown plan, skip
                continue

            # Calculate price difference
            current_monthly_price = subscription.amount if subscription and subscription.billing_period == 'monthly' else 0
            price_difference = plan.price_monthly - current_monthly_price

            # Calculate annual discount
            annual_full_price = plan.price_monthly * 12
            annual_discount = annual_full_price - plan.price_annual

            # Get plan features
            features = get_user_features(plan.plan_code)

            upgrade_options.append({
                'plan_code': plan.plan_code,
                'plan_name_ko': plan.plan_name_ko,
                'plan_name_en': plan.plan_name_en,
                'description': plan.description,
                'monthly_price': plan.price_monthly,
                'annual_price': plan.price_annual,
                'annual_discount': annual_discount,
                'annual_discount_percent': round(annual_discount / annual_full_price * 100) if annual_full_price > 0 else 0,
                'price_difference': price_difference,
                'features': features,
                'badge_text': plan.badge_text,
                'cta_text': plan.cta_text
            })

        return jsonify({
            'success': True,
            'current_plan': current_plan,
            'upgrade_options': upgrade_options
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


# Error handlers
@subscription_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Bad request'
    }), 400


@subscription_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized'
    }), 401


@subscription_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Not found'
    }), 404


@subscription_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500
