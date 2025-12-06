"""
Authentication Routes for CoinPulse
Refactored to use SQLAlchemy ORM with consolidated models
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
import jwt
import os
import secrets

from backend.database.connection import get_db_session
from backend.database.models import User, Session as UserSession, EmailVerification, PasswordReset, UserAPIKey
from backend.services.auth_service import auth_service
from backend.services.email_service import email_service

# Create Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# JWT Configuration from environment
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '7DfH2jzRD4lCfQ_llC4CObochoaGzaBBZLeODoftgWk')
JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hour
JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))  # 30 days


def generate_tokens(user_id, username):
    """Generate access and refresh tokens"""
    access_payload = {
        'user_id': user_id,
        'username': username,
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES),
        'iat': datetime.utcnow()
    }

    refresh_payload = {
        'user_id': user_id,
        'username': username,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(seconds=JWT_REFRESH_TOKEN_EXPIRES),
        'iat': datetime.utcnow()
    }

    access_token = jwt.encode(access_payload, JWT_SECRET_KEY, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET_KEY, algorithm='HS256')

    return access_token, refresh_token


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


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user

    Request Body:
        {
            "email": "user@example.com",
            "username": "username",
            "password": "SecurePassword123",
            "full_name": "John Doe" (optional),
            "phone": "+1234567890" (optional)
        }

    Returns:
        201: User created successfully with tokens
        400: Validation error
        409: User already exists
        500: Server error
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'code': 'NO_DATA'
            }), 400

        # Extract and validate fields
        email = data.get('email', '').strip().lower()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        phone = data.get('phone', '').strip()

        # Validate required fields
        if not email or not username or not password:
            return jsonify({
                'success': False,
                'error': 'Email, username, and password are required',
                'code': 'MISSING_FIELDS'
            }), 400

        # Validate email
        if not auth_service.validate_email(email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format',
                'code': 'INVALID_EMAIL'
            }), 400

        # Validate username
        is_valid, error_msg = auth_service.validate_username(username)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg,
                'code': 'INVALID_USERNAME'
            }), 400

        # Validate password strength
        is_valid, error_msg = auth_service.validate_password_strength(password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg,
                'code': 'WEAK_PASSWORD'
            }), 400

        # Hash password
        password_hash = auth_service.hash_password(password)

        # Create user with SQLAlchemy
        session = get_db_session()
        try:
            # Check if user already exists
            existing_user = session.query(User).filter(
                (User.email == email) | (User.username == username)
            ).first()

            if existing_user:
                if existing_user.email == email:
                    return jsonify({
                        'success': False,
                        'error': 'Email already registered',
                        'code': 'EMAIL_EXISTS'
                    }), 409
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Username already taken',
                        'code': 'USERNAME_EXISTS'
                    }), 409

            # Create new user
            new_user = User(
                email=email,
                username=username,
                password_hash=password_hash,
                full_name=full_name if full_name else None,
                phone=phone if phone else None,
                is_active=True,
                is_verified=False  # Email verification required
            )

            session.add(new_user)
            session.flush()  # Get user ID before commit

            # Generate tokens
            access_token, refresh_token = generate_tokens(new_user.id, new_user.username)

            # Create session record
            user_session = UserSession(
                user_id=new_user.id,
                token_jti=f"session_{new_user.id}_{datetime.utcnow().timestamp()}",
                token_type='access',
                expires_at=datetime.utcnow() + timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:500]  # Limit length
            )

            session.add(user_session)

            # Generate email verification token
            verification_token = secrets.token_urlsafe(32)
            email_verification = EmailVerification(
                user_id=new_user.id,
                token=verification_token,
                expires_at=datetime.utcnow() + timedelta(hours=24)  # 24 hour expiration
            )
            session.add(email_verification)

            session.commit()

            # Send verification email (non-blocking)
            try:
                email_service.send_verification_email(
                    to_email=new_user.email,
                    username=new_user.username,
                    token=verification_token
                )
            except Exception as e:
                print(f"[Auth] Failed to send verification email: {str(e)}")
                # Don't fail registration if email fails

            return jsonify({
                'success': True,
                'message': 'User registered successfully. Please check your email to verify your account.',
                'user': new_user.to_dict(),
                'tokens': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'expires_in': JWT_ACCESS_TOKEN_EXPIRES
                },
                'email_verification_required': True
            }), 201

        except IntegrityError as e:
            session.rollback()
            print(f"[Auth] Registration integrity error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'User already exists',
                'code': 'DUPLICATE_USER'
            }), 409

        except Exception as e:
            session.rollback()
            print(f"[Auth] Registration error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Internal server error',
                'code': 'SERVER_ERROR'
            }), 500

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] Registration request error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Invalid request format',
            'code': 'INVALID_REQUEST'
        }), 400


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user

    Request Body:
        {
            "email": "user@example.com",
            "password": "SecurePassword123"
        }

    Returns:
        200: Login successful with tokens
        400: Validation error
        401: Invalid credentials
        403: Account disabled
        500: Server error
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'code': 'NO_DATA'
            }), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required',
                'code': 'MISSING_FIELDS'
            }), 400

        # Find user with SQLAlchemy
        session = get_db_session()
        try:
            user = session.query(User).filter(User.email == email).first()

            if not user:
                return jsonify({
                    'success': False,
                    'error': 'Invalid email or password',
                    'code': 'INVALID_CREDENTIALS'
                }), 401

            # Verify password
            if not auth_service.verify_password(password, user.password_hash):
                return jsonify({
                    'success': False,
                    'error': 'Invalid email or password',
                    'code': 'INVALID_CREDENTIALS'
                }), 401

            # Check if account is active
            if not user.is_active:
                return jsonify({
                    'success': False,
                    'error': 'Account is disabled',
                    'code': 'ACCOUNT_DISABLED'
                }), 403

            # Update last login
            user.last_login_at = datetime.utcnow()

            # Generate tokens
            access_token, refresh_token = generate_tokens(user.id, user.username)

            # Create session record
            user_session = UserSession(
                user_id=user.id,
                token_jti=f"session_{user.id}_{datetime.utcnow().timestamp()}",
                token_type='access',
                expires_at=datetime.utcnow() + timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:500]
            )

            session.add(user_session)
            session.commit()

            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': user.to_dict(),
                'tokens': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'expires_in': JWT_ACCESS_TOKEN_EXPIRES
                }
            }), 200

        except Exception as e:
            session.rollback()
            print(f"[Auth] Login error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Internal server error',
                'code': 'SERVER_ERROR'
            }), 500

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] Login request error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Invalid request format',
            'code': 'INVALID_REQUEST'
        }), 400


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout user (revoke all active sessions)

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        200: Logout successful
        401: Unauthorized
        500: Server error
    """
    try:
        user_id, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        # Revoke all active sessions
        session = get_db_session()
        try:
            user_sessions = session.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.revoked == False
            ).all()

            for user_session in user_sessions:
                user_session.revoked = True
                user_session.revoked_at = datetime.utcnow()

            session.commit()

            return jsonify({
                'success': True,
                'message': 'Logout successful'
            }), 200

        except Exception as e:
            session.rollback()
            print(f"[Auth] Logout error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Internal server error',
                'code': 'SERVER_ERROR'
            }), 500

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] Logout request error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Invalid request format',
            'code': 'INVALID_REQUEST'
        }), 400


@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """
    Get user profile

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        200: Profile retrieved successfully
        401: Unauthorized
        404: User not found
        500: Server error
    """
    try:
        user_id, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        session = get_db_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()

            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }), 404

            return jsonify({
                'success': True,
                'user': user.to_dict()
            }), 200

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] Get profile error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }), 500


@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """
    Update user profile

    Headers:
        Authorization: Bearer <access_token>

    Request Body:
        {
            "full_name": "John Doe" (optional),
            "phone": "+1234567890" (optional)
        }

    Returns:
        200: Profile updated successfully
        400: Validation error
        401: Unauthorized
        404: User not found
        500: Server error
    """
    try:
        user_id, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'code': 'NO_DATA'
            }), 400

        session = get_db_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()

            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }), 404

            # Update allowed fields
            if 'full_name' in data:
                user.full_name = data['full_name'].strip() if data['full_name'] else None

            if 'phone' in data:
                user.phone = data['phone'].strip() if data['phone'] else None

            user.updated_at = datetime.utcnow()
            session.commit()

            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'user': user.to_dict()
            }), 200

        except Exception as e:
            session.rollback()
            print(f"[Auth] Update profile error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Internal server error',
                'code': 'SERVER_ERROR'
            }), 500

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] Update profile request error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Invalid request format',
            'code': 'INVALID_REQUEST'
        }), 400


@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    Refresh access token using refresh token

    Request Body:
        {
            "refresh_token": "<refresh_token>"
        }

    Returns:
        200: New access token generated
        400: Missing refresh token
        401: Invalid or expired refresh token
        500: Server error
    """
    try:
        data = request.get_json()

        if not data or 'refresh_token' not in data:
            return jsonify({
                'success': False,
                'error': 'Refresh token is required',
                'code': 'MISSING_TOKEN'
            }), 400

        refresh_token = data['refresh_token']
        payload, error = verify_token(refresh_token)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'INVALID_TOKEN'
            }), 401

        # Verify it's a refresh token
        if payload.get('type') != 'refresh':
            return jsonify({
                'success': False,
                'error': 'Invalid token type',
                'code': 'INVALID_TOKEN_TYPE'
            }), 401

        user_id = payload.get('user_id')
        username = payload.get('username')

        # Generate new access token
        new_access_token, _ = generate_tokens(user_id, username)

        return jsonify({
            'success': True,
            'message': 'Token refreshed successfully',
            'tokens': {
                'access_token': new_access_token,
                'expires_in': JWT_ACCESS_TOKEN_EXPIRES
            }
        }), 200

    except Exception as e:
        print(f"[Auth] Refresh token error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }), 500


@auth_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'service': 'authentication',
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@auth_bp.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    """
    Verify user email address

    Query Parameters (GET) or Request Body (POST):
        token: Verification token from email

    Returns:
        200: Email verified successfully
        400: Missing or invalid token
        404: Token not found or expired
        500: Server error
    """
    try:
        # Get token from query params (GET) or body (POST)
        if request.method == 'GET':
            token = request.args.get('token')
        else:
            data = request.get_json()
            token = data.get('token') if data else None

        if not token:
            return jsonify({
                'success': False,
                'error': 'Verification token is required',
                'code': 'MISSING_TOKEN'
            }), 400

        session = get_db_session()
        try:
            # Find verification record
            verification = session.query(EmailVerification).filter(
                EmailVerification.token == token,
                EmailVerification.verified == False
            ).first()

            if not verification:
                return jsonify({
                    'success': False,
                    'error': 'Invalid or already used verification token',
                    'code': 'INVALID_TOKEN'
                }), 404

            # Check expiration
            if verification.expires_at < datetime.utcnow():
                return jsonify({
                    'success': False,
                    'error': 'Verification token has expired. Please request a new one.',
                    'code': 'TOKEN_EXPIRED'
                }), 404

            # Update user and verification record
            user = session.query(User).filter(User.id == verification.user_id).first()
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }), 404

            user.is_verified = True
            user.email_verified_at = datetime.utcnow()
            verification.verified = True
            verification.verified_at = datetime.utcnow()

            session.commit()

            return jsonify({
                'success': True,
                'message': 'Email verified successfully',
                'user': user.to_dict()
            }), 200

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] Email verification error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }), 500


@auth_bp.route('/request-password-reset', methods=['POST'])
def request_password_reset():
    """
    Request password reset

    Request Body:
        {
            "email": "user@example.com"
        }

    Returns:
        200: Reset email sent (always returns 200 even if email doesn't exist - security)
        400: Validation error
        500: Server error
    """
    try:
        data = request.get_json()

        if not data or 'email' not in data:
            return jsonify({
                'success': False,
                'error': 'Email address is required',
                'code': 'MISSING_EMAIL'
            }), 400

        email = data['email'].strip().lower()

        if not auth_service.validate_email(email):
            return jsonify({
                'success': False,
                'error': 'Invalid email format',
                'code': 'INVALID_EMAIL'
            }), 400

        session = get_db_session()
        try:
            # Find user by email
            user = session.query(User).filter(User.email == email).first()

            # Always return success to prevent email enumeration
            # (don't reveal if email exists or not)
            if not user:
                print(f"[Auth] Password reset requested for non-existent email: {email}")
                return jsonify({
                    'success': True,
                    'message': 'If an account exists with this email, a password reset link has been sent.'
                }), 200

            # Check for recent reset requests (rate limiting)
            recent_reset = session.query(PasswordReset).filter(
                PasswordReset.user_id == user.id,
                PasswordReset.created_at > datetime.utcnow() - timedelta(minutes=15)
            ).first()

            if recent_reset:
                print(f"[Auth] Rate limited password reset for user: {user.id}")
                # Still return success (don't reveal rate limiting)
                return jsonify({
                    'success': True,
                    'message': 'If an account exists with this email, a password reset link has been sent.'
                }), 200

            # Generate reset token
            reset_token = secrets.token_urlsafe(32)
            password_reset = PasswordReset(
                user_id=user.id,
                token=reset_token,
                expires_at=datetime.utcnow() + timedelta(hours=1)  # 1 hour expiration
            )
            session.add(password_reset)
            session.commit()

            # Send password reset email
            try:
                email_service.send_password_reset_email(
                    to_email=user.email,
                    username=user.username,
                    token=reset_token
                )
                print(f"[Auth] Password reset email sent to: {user.email}")
            except Exception as e:
                print(f"[Auth] Failed to send password reset email: {str(e)}")

            return jsonify({
                'success': True,
                'message': 'If an account exists with this email, a password reset link has been sent.'
            }), 200

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] Request password reset error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }), 500


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Reset password using token

    Request Body:
        {
            "token": "reset_token_from_email",
            "new_password": "NewSecurePassword123!"
        }

    Returns:
        200: Password reset successfully
        400: Validation error
        404: Invalid or expired token
        500: Server error
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required',
                'code': 'NO_DATA'
            }), 400

        token = data.get('token', '').strip()
        new_password = data.get('new_password', '')

        if not token or not new_password:
            return jsonify({
                'success': False,
                'error': 'Token and new password are required',
                'code': 'MISSING_FIELDS'
            }), 400

        # Validate new password strength
        is_valid, error_msg = auth_service.validate_password_strength(new_password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': error_msg,
                'code': 'WEAK_PASSWORD'
            }), 400

        session = get_db_session()
        try:
            # Find reset record
            reset_record = session.query(PasswordReset).filter(
                PasswordReset.token == token,
                PasswordReset.used == False
            ).first()

            if not reset_record:
                return jsonify({
                    'success': False,
                    'error': 'Invalid or already used reset token',
                    'code': 'INVALID_TOKEN'
                }), 404

            # Check expiration
            if reset_record.expires_at < datetime.utcnow():
                return jsonify({
                    'success': False,
                    'error': 'Reset token has expired. Please request a new one.',
                    'code': 'TOKEN_EXPIRED'
                }), 404

            # Get user
            user = session.query(User).filter(User.id == reset_record.user_id).first()
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }), 404

            # Update password
            user.password_hash = auth_service.hash_password(new_password)

            # Mark reset token as used
            reset_record.used = True
            reset_record.used_at = datetime.utcnow()

            # Revoke all active sessions for security
            active_sessions = session.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.revoked == False
            ).all()

            for user_session in active_sessions:
                user_session.revoked = True
                user_session.revoked_at = datetime.utcnow()

            session.commit()

            print(f"[Auth] Password reset successful for user: {user.id}")
            print(f"[Auth] Revoked {len(active_sessions)} active sessions")

            return jsonify({
                'success': True,
                'message': 'Password reset successfully. Please log in with your new password.',
                'sessions_revoked': len(active_sessions)
            }), 200

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] Reset password error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }), 500


@auth_bp.route('/resend-verification', methods=['POST'])
def resend_verification():
    """
    Resend verification email

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        200: Verification email sent
        400: Email already verified
        401: Unauthorized
        429: Too many requests
        500: Server error
    """
    try:
        user_id, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        session = get_db_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()

            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }), 404

            # Check if already verified
            if user.is_verified:
                return jsonify({
                    'success': False,
                    'error': 'Email is already verified',
                    'code': 'ALREADY_VERIFIED'
                }), 400

            # Check for recent verification requests (rate limiting)
            recent_verification = session.query(EmailVerification).filter(
                EmailVerification.user_id == user_id,
                EmailVerification.created_at > datetime.utcnow() - timedelta(minutes=5)
            ).first()

            if recent_verification:
                return jsonify({
                    'success': False,
                    'error': 'Please wait 5 minutes before requesting another verification email',
                    'code': 'TOO_MANY_REQUESTS'
                }), 429

            # Generate new verification token
            verification_token = secrets.token_urlsafe(32)
            email_verification = EmailVerification(
                user_id=user.id,
                token=verification_token,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            session.add(email_verification)
            session.commit()

            # Send verification email
            try:
                email_service.send_verification_email(
                    to_email=user.email,
                    username=user.username,
                    token=verification_token
                )

                return jsonify({
                    'success': True,
                    'message': 'Verification email sent successfully'
                }), 200

            except Exception as e:
                print(f"[Auth] Failed to send verification email: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Failed to send verification email',
                    'code': 'EMAIL_SEND_FAILED'
                }), 500

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] Resend verification error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }), 500


@auth_bp.route('/sessions', methods=['GET'])
def get_sessions():
    """
    Get all active sessions for current user

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        200: List of active sessions
        401: Unauthorized
        500: Server error
    """
    try:
        user_id, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        session = get_db_session()
        try:
            # Get all active sessions
            active_sessions = session.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.revoked == False,
                UserSession.expires_at > datetime.utcnow()
            ).order_by(UserSession.created_at.desc()).all()

            sessions_data = []
            current_session_jti = None

            # Get current session JTI from token
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                try:
                    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
                    # Current session ID from token (we'll match by timestamp)
                except:
                    pass

            for user_session in active_sessions:
                session_info = {
                    'id': user_session.id,
                    'token_jti': user_session.token_jti,
                    'token_type': user_session.token_type,
                    'ip_address': user_session.ip_address,
                    'user_agent': user_session.user_agent,
                    'created_at': user_session.created_at.isoformat(),
                    'expires_at': user_session.expires_at.isoformat(),
                    'is_current': user_session.ip_address == request.remote_addr
                }
                sessions_data.append(session_info)

            return jsonify({
                'success': True,
                'sessions': sessions_data,
                'total': len(sessions_data)
            }), 200

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] Get sessions error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }), 500


@auth_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
def revoke_session(session_id):
    """
    Revoke a specific session

    Headers:
        Authorization: Bearer <access_token>

    Path Parameters:
        session_id: Session ID to revoke

    Returns:
        200: Session revoked successfully
        401: Unauthorized
        403: Cannot revoke other user's session
        404: Session not found
        500: Server error
    """
    try:
        user_id, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        session = get_db_session()
        try:
            # Find session
            user_session = session.query(UserSession).filter(
                UserSession.id == session_id
            ).first()

            if not user_session:
                return jsonify({
                    'success': False,
                    'error': 'Session not found',
                    'code': 'SESSION_NOT_FOUND'
                }), 404

            # Verify session belongs to current user
            if user_session.user_id != user_id:
                return jsonify({
                    'success': False,
                    'error': 'Cannot revoke another user\'s session',
                    'code': 'FORBIDDEN'
                }), 403

            # Check if already revoked
            if user_session.revoked:
                return jsonify({
                    'success': False,
                    'error': 'Session already revoked',
                    'code': 'ALREADY_REVOKED'
                }), 400

            # Revoke session
            user_session.revoked = True
            user_session.revoked_at = datetime.utcnow()
            session.commit()

            return jsonify({
                'success': True,
                'message': 'Session revoked successfully',
                'session_id': session_id
            }), 200

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] Revoke session error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }), 500


@auth_bp.route('/sessions/all', methods=['DELETE'])
def revoke_all_sessions():
    """
    Revoke all other sessions (keep current session active)

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        200: Sessions revoked successfully
        401: Unauthorized
        500: Server error
    """
    try:
        user_id, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        session = get_db_session()
        try:
            # Get current session IP to keep it active
            current_ip = request.remote_addr

            # Revoke all other active sessions
            other_sessions = session.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.revoked == False,
                UserSession.ip_address != current_ip
            ).all()

            revoked_count = 0
            for user_session in other_sessions:
                user_session.revoked = True
                user_session.revoked_at = datetime.utcnow()
                revoked_count += 1

            session.commit()

            return jsonify({
                'success': True,
                'message': f'Revoked {revoked_count} other session(s)',
                'sessions_revoked': revoked_count
            }), 200

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] Revoke all sessions error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }), 500


# ==================== API Key Management ====================

@auth_bp.route('/api-keys', methods=['POST'])
def create_api_key():
    """Create a new API key for current user"""
    try:
        user_id, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required',
                'code': 'NO_DATA'
            }), 400

        key_name = data.get('key_name', '').strip()
        expires_in_days = data.get('expires_in_days')  # Optional

        if not key_name:
            return jsonify({
                'success': False,
                'error': 'API key name is required',
                'code': 'MISSING_KEY_NAME'
            }), 400

        if len(key_name) > 100:
            return jsonify({
                'success': False,
                'error': 'Key name must be 100 characters or less',
                'code': 'KEY_NAME_TOO_LONG'
            }), 400

        session = get_db_session()
        try:
            # Check if user already has 10 active API keys (limit)
            active_keys_count = session.query(UserAPIKey).filter(
                UserAPIKey.user_id == user_id,
                UserAPIKey.is_active == True
            ).count()

            if active_keys_count >= 10:
                return jsonify({
                    'success': False,
                    'error': 'Maximum number of active API keys reached (10)',
                    'code': 'KEY_LIMIT_REACHED'
                }), 400

            # Generate secure API key (32 bytes = 256 bits)
            api_key = f"cp_{secrets.token_urlsafe(32)}"  # cp_ prefix for CoinPulse

            # Calculate expiration
            expires_at = None
            if expires_in_days:
                try:
                    days = int(expires_in_days)
                    if days <= 0 or days > 365:
                        return jsonify({
                            'success': False,
                            'error': 'Expiration must be between 1 and 365 days',
                            'code': 'INVALID_EXPIRATION'
                        }), 400
                    expires_at = datetime.utcnow() + timedelta(days=days)
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid expiration days value',
                        'code': 'INVALID_EXPIRATION'
                    }), 400

            # Create API key record
            new_api_key = UserAPIKey(
                user_id=user_id,
                key_name=key_name,
                api_key=api_key,
                expires_at=expires_at
            )
            session.add(new_api_key)
            session.commit()

            print(f"[Auth] Created API key '{key_name}' for user: {user_id}")

            return jsonify({
                'success': True,
                'message': 'API key created successfully. Please save it securely - it will not be shown again.',
                'api_key': {
                    'id': new_api_key.id,
                    'key_name': new_api_key.key_name,
                    'api_key': api_key,  # Only shown once!
                    'created_at': new_api_key.created_at.isoformat(),
                    'expires_at': new_api_key.expires_at.isoformat() if new_api_key.expires_at else None
                }
            }), 201

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] Create API key error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }), 500


@auth_bp.route('/api-keys', methods=['GET'])
def list_api_keys():
    """List all API keys for current user (without exposing full key)"""
    try:
        user_id, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        session = get_db_session()
        try:
            # Get all API keys (active and inactive)
            api_keys = session.query(UserAPIKey).filter(
                UserAPIKey.user_id == user_id
            ).order_by(UserAPIKey.created_at.desc()).all()

            keys_data = []
            for key in api_keys:
                # Only show partial key for security (first 8 + last 4 chars)
                partial_key = None
                if key.api_key:
                    if len(key.api_key) > 15:
                        partial_key = f"{key.api_key[:8]}...{key.api_key[-4:]}"
                    else:
                        partial_key = f"{key.api_key[:4]}..."

                key_info = {
                    'id': key.id,
                    'key_name': key.key_name,
                    'partial_key': partial_key,
                    'is_active': key.is_active,
                    'created_at': key.created_at.isoformat(),
                    'last_used_at': key.last_used_at.isoformat() if key.last_used_at else None,
                    'expires_at': key.expires_at.isoformat() if key.expires_at else None,
                    'is_expired': key.expires_at < datetime.utcnow() if key.expires_at else False
                }
                keys_data.append(key_info)

            return jsonify({
                'success': True,
                'api_keys': keys_data,
                'total': len(keys_data),
                'active_count': sum(1 for k in keys_data if k['is_active'])
            }), 200

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] List API keys error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }), 500


@auth_bp.route('/api-keys/<int:key_id>', methods=['DELETE'])
def revoke_api_key(key_id):
    """Revoke/delete a specific API key"""
    try:
        user_id, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        session = get_db_session()
        try:
            # Find API key
            api_key = session.query(UserAPIKey).filter(
                UserAPIKey.id == key_id
            ).first()

            if not api_key:
                return jsonify({
                    'success': False,
                    'error': 'API key not found',
                    'code': 'KEY_NOT_FOUND'
                }), 404

            # Verify ownership
            if api_key.user_id != user_id:
                return jsonify({
                    'success': False,
                    'error': 'Cannot revoke another user\'s API key',
                    'code': 'FORBIDDEN'
                }), 403

            # Check if already inactive
            if not api_key.is_active:
                return jsonify({
                    'success': False,
                    'error': 'API key is already inactive',
                    'code': 'ALREADY_INACTIVE'
                }), 400

            # Revoke API key
            api_key.is_active = False
            session.commit()

            print(f"[Auth] Revoked API key '{api_key.key_name}' for user: {user_id}")

            return jsonify({
                'success': True,
                'message': f'API key "{api_key.key_name}" has been revoked',
                'key_id': key_id
            }), 200

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] Revoke API key error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }), 500


@auth_bp.route('/api-keys/<int:key_id>/rotate', methods=['POST'])
def rotate_api_key(key_id):
    """Rotate an API key - Creates new key with same name and revokes old one"""
    try:
        user_id, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        session = get_db_session()
        try:
            # Find existing API key
            old_key = session.query(UserAPIKey).filter(
                UserAPIKey.id == key_id
            ).first()

            if not old_key:
                return jsonify({
                    'success': False,
                    'error': 'API key not found',
                    'code': 'KEY_NOT_FOUND'
                }), 404

            # Verify ownership
            if old_key.user_id != user_id:
                return jsonify({
                    'success': False,
                    'error': 'Cannot rotate another user\'s API key',
                    'code': 'FORBIDDEN'
                }), 403

            # Check if old key is active
            if not old_key.is_active:
                return jsonify({
                    'success': False,
                    'error': 'Cannot rotate an inactive API key',
                    'code': 'KEY_INACTIVE'
                }), 400

            # Generate new secure API key
            new_api_key_value = f"cp_{secrets.token_urlsafe(32)}"

            # Preserve expiration settings from old key
            expires_at = None
            if old_key.expires_at:
                # Calculate remaining days and apply to new key
                remaining = old_key.expires_at - datetime.utcnow()
                if remaining.total_seconds() > 0:
                    expires_at = datetime.utcnow() + remaining

            # Create new API key with same name
            new_key = UserAPIKey(
                user_id=user_id,
                key_name=old_key.key_name,
                api_key=new_api_key_value,
                expires_at=expires_at
            )
            session.add(new_key)

            # Revoke old key
            old_key.is_active = False

            session.commit()

            print(f"[Auth] Rotated API key '{old_key.key_name}' for user: {user_id}")

            return jsonify({
                'success': True,
                'message': 'API key rotated successfully. Please save the new key securely - it will not be shown again.',
                'old_key_id': key_id,
                'new_api_key': {
                    'id': new_key.id,
                    'key_name': new_key.key_name,
                    'api_key': new_api_key_value,  # Only shown once!
                    'created_at': new_key.created_at.isoformat(),
                    'expires_at': new_key.expires_at.isoformat() if new_key.expires_at else None
                }
            }), 200

        finally:
            session.close()

    except Exception as e:
        print(f"[Auth] Rotate API key error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 'SERVER_ERROR'
        }), 500
