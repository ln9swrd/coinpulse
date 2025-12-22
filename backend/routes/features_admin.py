"""
CoinPulse Admin Features Management API
Admin endpoints for customizing user plan features
"""

import os
import sys
from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime
import jwt

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.connection import get_db_session
from models.plan_features import UserFeatureOverride, PLAN_FEATURES, get_user_features
from models.subscription_models import Subscription

# Create Blueprint
features_admin_bp = Blueprint('features_admin', __name__, url_prefix='/api/admin/features')

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


@features_admin_bp.route('/users/<int:user_id>', methods=['GET'])
@require_admin
def get_user_features_endpoint(user_id):
    """
    Get user's effective features (plan + overrides)

    Response:
    {
        "success": true,
        "user_id": 123,
        "plan": "basic",
        "plan_features": {...},
        "overrides": {...},
        "effective_features": {...}
    }
    """
    try:
        session = get_db_session()

        # Get user subscription
        subscription = session.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(Subscription.created_at.desc()).first()

        plan = subscription.plan.value if subscription else 'free'

        # Get overrides
        override = session.query(UserFeatureOverride).filter(
            UserFeatureOverride.user_id == user_id
        ).first()

        # Check if override is expired
        override_dict = None
        if override and not override.is_expired():
            override_dict = override.features

        # Calculate effective features
        effective_features = get_user_features(plan, override_dict)

        return jsonify({
            'success': True,
            'user_id': user_id,
            'plan': plan,
            'plan_features': PLAN_FEATURES.get(plan, PLAN_FEATURES['free']),
            'overrides': override.to_dict() if override else None,
            'effective_features': effective_features
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@features_admin_bp.route('/users/<int:user_id>/override', methods=['POST'])
@require_admin
def set_feature_override(user_id):
    """
    Set or update feature overrides for a user

    Request JSON:
    {
        "features": {
            "max_auto_trading_alerts": 5,
            "telegram_alerts": true,
            "backtesting": true
        },
        "reason": "Beta tester special access",
        "expires_at": "2025-12-31T23:59:59"  # Optional
    }

    Response:
    {
        "success": true,
        "override": {...},
        "effective_features": {...}
    }
    """
    try:
        data = request.get_json()

        if 'features' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required field: features'
            }), 400

        features = data['features']
        reason = data.get('reason', 'Admin override')
        expires_at_str = data.get('expires_at')

        # Parse expiration date if provided
        expires_at = None
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            except ValueError as e:
                return jsonify({
                    'success': False,
                    'error': f'Invalid expires_at format: {str(e)}'
                }), 400

        session = get_db_session()

        # Check if override already exists
        override = session.query(UserFeatureOverride).filter(
            UserFeatureOverride.user_id == user_id
        ).first()

        if override:
            # Update existing override
            override.features = features
            override.reason = reason
            override.expires_at = expires_at
            override.created_by_admin_id = request.admin_id
            override.updated_at = datetime.utcnow()
        else:
            # Create new override
            override = UserFeatureOverride(
                user_id=user_id,
                features=features,
                reason=reason,
                expires_at=expires_at,
                created_by_admin_id=request.admin_id
            )
            session.add(override)

        session.commit()

        # Get subscription to calculate effective features
        subscription = session.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(Subscription.created_at.desc()).first()

        plan = subscription.plan.value if subscription else 'free'
        effective_features = get_user_features(plan, features)

        return jsonify({
            'success': True,
            'override': override.to_dict(),
            'effective_features': effective_features
        }), 200

    except Exception as e:
        session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@features_admin_bp.route('/users/<int:user_id>/override', methods=['DELETE'])
@require_admin
def delete_feature_override(user_id):
    """
    Remove feature overrides for a user

    Response:
    {
        "success": true,
        "message": "Feature override removed",
        "effective_features": {...}
    }
    """
    try:
        session = get_db_session()

        override = session.query(UserFeatureOverride).filter(
            UserFeatureOverride.user_id == user_id
        ).first()

        if not override:
            return jsonify({
                'success': False,
                'error': 'No feature override found for user'
            }), 404

        session.delete(override)
        session.commit()

        # Get subscription to calculate effective features
        subscription = session.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(Subscription.created_at.desc()).first()

        plan = subscription.plan.value if subscription else 'free'
        effective_features = get_user_features(plan, None)

        return jsonify({
            'success': True,
            'message': 'Feature override removed',
            'user_id': user_id,
            'effective_features': effective_features
        }), 200

    except Exception as e:
        session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@features_admin_bp.route('/plans', methods=['GET'])
def get_plan_features():
    """
    Get default features for all plans

    Response:
    {
        "success": true,
        "plans": {
            "free": {...},
            "basic": {...},
            "pro": {...},
            "enterprise": {...}
        }
    }
    """
    return jsonify({
        'success': True,
        'plans': PLAN_FEATURES
    }), 200


@features_admin_bp.route('/overrides', methods=['GET'])
@require_admin
def list_all_overrides():
    """
    List all active feature overrides

    Query params:
    - limit: Number of results (default: 50)
    - offset: Offset for pagination (default: 0)

    Response:
    {
        "success": true,
        "overrides": [...],
        "total": 10,
        "limit": 50,
        "offset": 0
    }
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        session = get_db_session()

        # Get total count
        total = session.query(UserFeatureOverride).count()

        # Get overrides with pagination
        overrides = session.query(UserFeatureOverride).order_by(
            UserFeatureOverride.created_at.desc()
        ).limit(limit).offset(offset).all()

        return jsonify({
            'success': True,
            'overrides': [o.to_dict() for o in overrides],
            'total': total,
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


@features_admin_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'features_admin',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
