"""
Authentication Middleware for CoinPulse
Provides decorator to protect routes with JWT authentication
"""

from functools import wraps
from flask import request, jsonify, g
from backend.services.auth_service import auth_service


def require_auth(f):
    """
    Decorator to require JWT authentication for routes

    Usage:
        @app.route('/api/protected')
        @require_auth
        def protected_route():
            user_id = g.user_id  # Access authenticated user ID
            return jsonify({'user_id': user_id})

    Returns:
        401: If token is missing, invalid, or expired
        403: If token is revoked
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({
                'success': False,
                'error': 'Missing authorization header',
                'code': 'AUTH_REQUIRED'
            }), 401

        if not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Invalid authorization header format. Use: Bearer <token>',
                'code': 'INVALID_AUTH_FORMAT'
            }), 401

        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({
                'success': False,
                'error': 'Malformed authorization header',
                'code': 'MALFORMED_AUTH'
            }), 401

        # Verify token
        payload = auth_service.verify_token(token)

        if not payload:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired token',
                'code': 'INVALID_TOKEN'
            }), 401

        # Check token type (should be 'access')
        if payload.get('type') != 'access':
            return jsonify({
                'success': False,
                'error': 'Invalid token type. Use access token for API requests.',
                'code': 'WRONG_TOKEN_TYPE'
            }), 401

        # Store user_id in Flask's g object for access in route
        g.user_id = payload.get('user_id')
        g.token_jti = payload.get('jti')

        # Optional: Check if token is revoked in database
        # This requires database query - can be enabled for extra security
        # session = check_token_revoked(g.token_jti)
        # if session and session.revoked:
        #     return jsonify({'error': 'Token has been revoked'}), 403

        return f(*args, **kwargs)

    return decorated_function


def optional_auth(f):
    """
    Decorator for routes that work with or without authentication
    If authenticated, g.user_id will be set

    Usage:
        @app.route('/api/public')
        @optional_auth
        def public_route():
            if hasattr(g, 'user_id'):
                # Authenticated user
                return jsonify({'user_id': g.user_id})
            else:
                # Anonymous user
                return jsonify({'user': 'anonymous'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                payload = auth_service.verify_token(token)

                if payload and payload.get('type') == 'access':
                    g.user_id = payload.get('user_id')
                    g.token_jti = payload.get('jti')
            except Exception as e:
                print(f"[OptionalAuth] Token verification failed: {e}")
                # Continue without auth - it's optional

        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    Decorator to require admin role
    Must be used after @require_auth

    Usage:
        @app.route('/api/admin/users')
        @require_auth
        @admin_required
        def admin_route():
            return jsonify({'admin': True})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'user_id'):
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }), 401

        # TODO: Check user role from database
        # user = db.query(User).filter(User.id == g.user_id).first()
        # if not user or not user.is_admin:
        #     return jsonify({'error': 'Admin access required'}), 403

        return f(*args, **kwargs)

    return decorated_function


def get_current_user_id():
    """
    Helper function to get current authenticated user ID

    Returns:
        int: User ID if authenticated, None otherwise
    """
    return getattr(g, 'user_id', None)


def get_current_token_jti():
    """
    Helper function to get current token JTI

    Returns:
        str: Token JTI if authenticated, None otherwise
    """
    return getattr(g, 'token_jti', None)
