"""
User API Routes for CoinPulse
Provides user-specific endpoints like plan information
"""

from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime
import jwt
import os

from backend.database.connection import get_db_session
# from backend.models.subscription_models import Subscription, SubscriptionStatus  # TODO: Enable when subscription system is ready

# Create Blueprint
user_bp = Blueprint('user', __name__, url_prefix='/api/user')

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


@user_bp.route('/plan', methods=['GET'])
@require_auth
def get_user_plan():
    """
    Get user's current subscription plan

    Returns:
        200: {
            "success": true,
            "plan": {
                "plan_code": "FREE|PREMIUM|ENTERPRISE",
                "plan_name": "Free Plan",
                "is_active": true,
                "start_date": "2025-12-14",
                "end_date": "2026-01-14",
                "auto_renew": false
            }
        }

        200 (No active subscription): {
            "success": true,
            "plan": {
                "plan_code": "FREE",
                "plan_name": "Free Plan",
                "is_active": true
            }
        }

        401: Unauthorized (missing or invalid token)
        500: Server error
    """
    try:
        user_id = request.user_id
        db = get_db_session()

        try:
            # Query subscription using actual DB schema (plan, status as varchar)
            from sqlalchemy import text

            query = text("""
                SELECT plan, status, started_at, expires_at, auto_renew
                FROM user_subscriptions
                WHERE user_id = :user_id AND status = 'active'
                LIMIT 1
            """)

            result = db.execute(query, {'user_id': user_id}).fetchone()

            if result:
                plan_code = result[0] or 'free'
                status = result[1]
                started_at = result[2]
                expires_at = result[3]
                auto_renew = result[4]

                # Map plan_code to display name
                plan_names = {
                    'free': 'Free Plan',
                    'basic': 'Basic Plan',
                    'pro': 'Pro Plan',
                    'premium': 'Premium Plan',
                    'enterprise': 'Enterprise Plan'
                }

                plan_data = {
                    'plan_code': plan_code.lower(),  # Return lowercase for consistency
                    'plan_name': plan_names.get(plan_code.lower(), 'Free Plan'),
                    'is_active': status == 'active',
                    'start_date': started_at.isoformat() if started_at else None,
                    'end_date': expires_at.isoformat() if expires_at else None,
                    'auto_renew': auto_renew if auto_renew is not None else False
                }

                return jsonify({
                    'success': True,
                    'plan': plan_data
                }), 200

            else:
                # No active subscription found - return FREE plan
                plan_data = {
                    'plan_code': 'FREE',
                    'plan_name': 'Free Plan',
                    'is_active': True,
                    'features': [
                        'Basic trading bot',
                        'Limited indicators',
                        'Community support'
                    ]
                }

                return jsonify({
                    'success': True,
                    'plan': plan_data
                }), 200

        finally:
            db.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500


@user_bp.route('/profile', methods=['GET'])
@require_auth
def get_user_profile():
    """
    Get user profile information

    Returns:
        200: User profile with subscription info
        401: Unauthorized
        500: Server error
    """
    try:
        from backend.database.models import User

        user_id = request.user_id
        db = get_db_session()

        try:
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }), 404

            # TODO: Implement subscription lookup
            # For now, all users have FREE plan

            profile_data = {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'plan': {
                    'plan_code': 'FREE',
                    'plan_name': 'Free Plan'
                }
            }

            return jsonify({
                'success': True,
                'profile': profile_data
            }), 200

        finally:
            db.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500


@user_bp.route('/subscription', methods=['GET'])
@require_auth
def get_user_subscription():
    """
    Get user's current subscription information

    Returns:
        200: {
            "success": true,
            "subscription": {
                "plan": "free"|"basic"|"pro"|"enterprise",
                "status": "active"|"expired"|"cancelled",
                "expires_at": "2025-12-31T23:59:59",
                ...
            }
        }
        401: Unauthorized
        404: No subscription found
    """
    from backend.models.subscription_models import UserSubscription

    session = get_db_session()
    try:
        user_id = request.user_id

        # Query user subscription
        subscription = session.query(UserSubscription)\
            .filter(UserSubscription.user_id == user_id)\
            .first()

        if subscription:
            return jsonify({
                'success': True,
                'subscription': {
                    'plan': subscription.plan,
                    'status': subscription.status,
                    'started_at': subscription.started_at.isoformat() if subscription.started_at else None,
                    'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
                    'auto_renew': subscription.auto_renew,
                    'payment_method': subscription.payment_method
                }
            }), 200
        else:
            # No subscription found - default to free plan
            return jsonify({
                'success': True,
                'subscription': {
                    'plan': 'free',
                    'status': 'active',
                    'started_at': None,
                    'expires_at': None,
                    'auto_renew': False,
                    'payment_method': None
                }
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500
    finally:
        session.close()


@user_bp.route('/api-keys/status', methods=['GET'])
@require_auth
def get_api_keys_status():
    """
    Get user's API keys status (whether they have keys configured)

    Returns:
        200: API keys status
        401: Unauthorized
    """
    from backend.database.models import User

    session = get_db_session()
    try:
        user_id = request.user_id

        # Query user
        user = session.query(User).filter(User.id == user_id).first()

        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }), 404

        has_keys = bool(user.upbit_access_key and user.upbit_secret_key)

        return jsonify({
            'success': True,
            'has_keys': has_keys
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500
    finally:
        session.close()


@user_bp.route('/api-keys', methods=['GET', 'POST'])
@require_auth
def manage_api_keys():
    """
    Get or save user's Upbit API keys (encrypted storage)

    GET:
        Returns user's API keys (secret key is masked)

    POST:
        Request Body:
        {
            "access_key": "string",
            "secret_key": "string"
        }

    Returns:
        200: Success
        400: Invalid request (POST only)
        401: Unauthorized
        404: User not found
    """
    from backend.database.models import User
    from backend.models.user_api_key import UpbitAPIKey
    from backend.utils.crypto import encrypt_api_credentials, decrypt_api_credentials
    from backend.common import UpbitAPI
    from datetime import datetime

    session = get_db_session()
    try:
        user_id = request.user_id

        # GET: Return existing API keys from encrypted storage
        if request.method == 'GET':
            # Check if user exists
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }), 404

            # Get encrypted keys from upbit_api_keys table
            api_key_record = session.query(UpbitAPIKey).filter(
                UpbitAPIKey.user_id == user_id
            ).first()

            if not api_key_record:
                # No keys registered
                return jsonify({
                    'success': True,
                    'access_key': None,
                    'secret_key_masked': None,
                    'has_keys': False
                }), 200

            # Decrypt and return access key
            access_key, secret_key = decrypt_api_credentials(
                api_key_record.access_key_encrypted,
                api_key_record.secret_key_encrypted
            )

            # Mask secret key (show only last 4 characters)
            secret_key_masked = None
            if secret_key:
                if len(secret_key) > 4:
                    secret_key_masked = '****' + secret_key[-4:]
                else:
                    secret_key_masked = '****'

            return jsonify({
                'success': True,
                'access_key': access_key,
                'secret_key_masked': secret_key_masked,
                'has_keys': True,
                'is_verified': api_key_record.is_verified,
                'key_name': api_key_record.key_name
            }), 200

        # POST: Save new API keys to encrypted storage (delete old if exists)
        elif request.method == 'POST':
            data = request.get_json()

            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided',
                    'code': 'INVALID_REQUEST'
                }), 400

            access_key = data.get('access_key', '').strip()
            secret_key = data.get('secret_key', '').strip()

            if not access_key or not secret_key:
                return jsonify({
                    'success': False,
                    'error': 'Access key and secret key are required',
                    'code': 'MISSING_KEYS'
                }), 400

            # Verify user exists
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }), 404

            # Verify keys with Upbit API
            try:
                upbit_api = UpbitAPI(access_key, secret_key)
                accounts = upbit_api.get_accounts()

                if not accounts:
                    return jsonify({
                        'success': False,
                        'error': 'API key verification failed. Please check your keys.',
                        'code': 'VERIFICATION_FAILED'
                    }), 400

            except Exception as verify_error:
                return jsonify({
                    'success': False,
                    'error': f'API key verification failed: {str(verify_error)}',
                    'code': 'VERIFICATION_FAILED'
                }), 400

            # Encrypt keys
            encrypted_access, encrypted_secret = encrypt_api_credentials(access_key, secret_key)

            # Check if user already has keys (DELETE old keys if exists)
            existing_key = session.query(UpbitAPIKey).filter(
                UpbitAPIKey.user_id == user_id
            ).first()

            if existing_key:
                # Delete old keys first (as requested by user)
                session.delete(existing_key)
                session.flush()  # Ensure deletion is committed before insert

            # Create new API key record
            new_key = UpbitAPIKey(
                user_id=user_id,
                access_key_encrypted=encrypted_access,
                secret_key_encrypted=encrypted_secret,
                key_name=f'Settings Key ({datetime.now().strftime("%Y-%m-%d")})',
                is_active=True,
                is_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            session.add(new_key)
            session.commit()

            return jsonify({
                'success': True,
                'message': 'API keys saved successfully',
                'verified': True
            }), 200

    except Exception as e:
        if request.method == 'POST':
            session.rollback()
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500
    finally:
        session.close()


@user_bp.route('/test-api-keys', methods=['POST'])
@require_auth
def test_api_keys():
    """
    Test Upbit API keys without saving them

    Request Body:
    {
        "access_key": "string",
        "secret_key": "string"
    }

    Returns:
        200: Connection successful
        400: Invalid request or keys
        401: Unauthorized
    """
    from backend.common import UpbitAPI

    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'code': 'INVALID_REQUEST'
            }), 400

        access_key = data.get('access_key', '').strip()
        secret_key = data.get('secret_key', '').strip()

        if not access_key or not secret_key:
            return jsonify({
                'success': False,
                'error': 'Access key and secret key are required',
                'code': 'MISSING_KEYS'
            }), 400

        # Test connection by fetching accounts
        upbit_api = UpbitAPI(access_key, secret_key)
        accounts = upbit_api.get_accounts()

        if accounts is None:
            return jsonify({
                'success': False,
                'error': 'Failed to connect to Upbit API. Please check your keys.',
                'code': 'CONNECTION_FAILED'
            }), 400

        # Connection successful
        return jsonify({
            'success': True,
            'message': 'API keys are valid and working',
            'accounts_count': len(accounts)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500


@user_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint

    Response:
    {
        "status": "healthy",
        "service": "user",
        "timestamp": "2025-12-14T12:34:56"
    }
    """
    return jsonify({
        'status': 'healthy',
        'service': 'user',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


# Error handlers
@user_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'error': 'Unauthorized',
        'code': 'UNAUTHORIZED'
    }), 401


@user_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Not found',
        'code': 'NOT_FOUND'
    }), 404


@user_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR'
    }), 500
