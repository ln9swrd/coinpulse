"""
User API Keys Middleware

Provides helper functions to get user-specific Upbit API keys from database.
"""

from flask import request, jsonify
from functools import wraps
import jwt
import os

from backend.database import get_db_session, User
from backend.common import UpbitAPI


def get_user_from_token():
    """
    Extract user_id from JWT token in request headers.

    Returns:
        int: user_id if valid token, None otherwise
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    try:
        # Extract token from "Bearer <token>"
        token = auth_header.split(' ')[1] if ' ' in auth_header else auth_header

        # Decode JWT
        secret_key = os.getenv('JWT_SECRET_KEY', 'coinpulse-secret-key-2024')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])

        return payload.get('user_id')
    except Exception as e:
        print(f"[UserAPIKeys] Error decoding token: {e}")
        return None


def get_user_upbit_api(user_id=None):
    """
    Get UpbitAPI instance with user-specific API keys from database.

    Args:
        user_id (int, optional): User ID. If None, extracts from JWT token.

    Returns:
        UpbitAPI: UpbitAPI instance with user's keys, or None if keys not found
    """
    if user_id is None:
        user_id = get_user_from_token()

    if not user_id:
        print("[UserAPIKeys] No user_id provided or found in token")
        return None

    db = get_db_session()
    try:
        # Query user's API keys from database
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            print(f"[UserAPIKeys] User {user_id} not found")
            return None

        if not user.upbit_access_key or not user.upbit_secret_key:
            print(f"[UserAPIKeys] User {user_id} has no Upbit API keys")
            return None

        # Create UpbitAPI instance with user's keys
        print(f"[UserAPIKeys] Creating UpbitAPI for user {user_id} ({user.email})")
        return UpbitAPI(user.upbit_access_key, user.upbit_secret_key)

    except Exception as e:
        print(f"[UserAPIKeys] Error getting user API keys: {e}")
        return None
    finally:
        db.close()


def require_upbit_keys(f):
    """
    Decorator to ensure user has Upbit API keys configured.

    Usage:
        @require_upbit_keys
        def my_endpoint():
            upbit_api = get_user_upbit_api()
            # Use upbit_api...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        upbit_api = get_user_upbit_api()

        if not upbit_api:
            return jsonify({
                "success": False,
                "error": "Upbit API keys not configured. Please add your API keys in Settings.",
                "error_code": "NO_API_KEYS"
            }), 400

        return f(*args, **kwargs)

    return decorated_function
