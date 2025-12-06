"""
Authentication Utilities
JWT token generation, password hashing, and verification
"""

import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

# Configuration
SECRET_KEY = secrets.token_hex(32)  # Should be in environment variable in production
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 30


# ============================================
# Password Hashing
# ============================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        print(f"[Auth] Password verification error: {e}")
        return False


# ============================================
# JWT Token Generation
# ============================================

def create_access_token(user_id: int, email: str, username: str = None) -> str:
    """
    Create JWT access token for user.

    Args:
        user_id: User ID from database
        email: User email
        username: Username (optional)

    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        'user_id': user_id,
        'email': email,
        'username': username,
        'exp': expire,
        'iat': datetime.utcnow(),
        'type': 'access'
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def create_refresh_token(user_id: int) -> str:
    """
    Create JWT refresh token for long-term authentication.

    Args:
        user_id: User ID from database

    Returns:
        JWT refresh token string
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        'user_id': user_id,
        'exp': expire,
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_token(token: str) -> dict:
    """
    Decode and verify JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dictionary

    Raises:
        jwt.ExpiredSignatureError: Token has expired
        jwt.InvalidTokenError: Token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception('Token has expired')
    except jwt.InvalidTokenError as e:
        raise Exception(f'Invalid token: {str(e)}')


# ============================================
# Authentication Decorators
# ============================================

def require_auth(f):
    """
    Decorator to protect routes with JWT authentication.

    Usage:
        @app.route('/api/protected')
        @require_auth
        def protected_route():
            user_id = request.user_id  # Available after authentication
            return jsonify({'message': 'Protected data'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({
                'success': False,
                'message': 'Authorization header missing'
            }), 401

        # Extract token (format: "Bearer <token>")
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({
                'success': False,
                'message': 'Invalid authorization header format'
            }), 401

        # Verify token
        try:
            payload = decode_token(token)

            # Check token type
            if payload.get('type') != 'access':
                return jsonify({
                    'success': False,
                    'message': 'Invalid token type'
                }), 401

            # Attach user info to request
            request.user_id = payload.get('user_id')
            request.user_email = payload.get('email')
            request.user_username = payload.get('username')

        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 401

        return f(*args, **kwargs)

    return decorated_function


def optional_auth(f):
    """
    Decorator for optional authentication.
    Route works without auth, but attaches user info if present.

    Usage:
        @app.route('/api/public-with-user')
        @optional_auth
        def public_route():
            user_id = getattr(request, 'user_id', None)
            if user_id:
                # Authenticated user
                pass
            else:
                # Anonymous user
                pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if auth_header:
            try:
                token = auth_header.split(' ')[1]
                payload = decode_token(token)

                request.user_id = payload.get('user_id')
                request.user_email = payload.get('email')
                request.user_username = payload.get('username')
            except:
                # Invalid token, but that's okay for optional auth
                pass

        return f(*args, **kwargs)

    return decorated_function


# ============================================
# API Key Generation
# ============================================

def generate_api_key() -> str:
    """
    Generate a random API key for user authentication.

    Returns:
        64-character hexadecimal API key
    """
    return secrets.token_hex(32)


# ============================================
# Token Validation Helpers
# ============================================

def is_token_expired(token: str) -> bool:
    """
    Check if a JWT token is expired without raising an exception.

    Args:
        token: JWT token string

    Returns:
        True if expired, False if still valid
    """
    try:
        decode_token(token)
        return False
    except Exception as e:
        if 'expired' in str(e).lower():
            return True
        return False


def get_token_expiry(token: str) -> datetime:
    """
    Get the expiration datetime of a JWT token.

    Args:
        token: JWT token string

    Returns:
        Expiration datetime
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        exp_timestamp = payload.get('exp')
        return datetime.fromtimestamp(exp_timestamp)
    except Exception as e:
        raise Exception(f'Failed to get token expiry: {str(e)}')


# ============================================
# User Session Management
# ============================================

class UserSession:
    """
    Helper class for managing user sessions.
    """

    def __init__(self, user_id: int, email: str, username: str = None):
        self.user_id = user_id
        self.email = email
        self.username = username

    def create_tokens(self) -> dict:
        """
        Create both access and refresh tokens for the user.

        Returns:
            Dictionary with access_token and refresh_token
        """
        return {
            'access_token': create_access_token(self.user_id, self.email, self.username),
            'refresh_token': create_refresh_token(self.user_id),
            'token_type': 'Bearer',
            'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds
        }

    def to_dict(self) -> dict:
        """
        Convert session to dictionary for JSON response.

        Returns:
            User session data dictionary
        """
        return {
            'user_id': self.user_id,
            'email': self.email,
            'username': self.username
        }


# ============================================
# Example Usage
# ============================================

if __name__ == '__main__':
    # Example: Hash and verify password
    password = 'mySecurePassword123'
    hashed = hash_password(password)
    print(f'Hashed password: {hashed}')
    print(f'Password valid: {verify_password(password, hashed)}')
    print(f'Wrong password: {verify_password("wrongPassword", hashed)}')

    # Example: Create and decode token
    token = create_access_token(user_id=1, email='test@example.com', username='testuser')
    print(f'\nAccess token: {token}')

    payload = decode_token(token)
    print(f'Decoded payload: {payload}')

    # Example: User session
    session = UserSession(user_id=1, email='test@example.com', username='testuser')
    tokens = session.create_tokens()
    print(f'\nTokens: {tokens}')
