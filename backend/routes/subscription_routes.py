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
