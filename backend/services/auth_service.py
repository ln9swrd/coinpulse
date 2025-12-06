"""
Authentication Service for CoinPulse
Handles user registration, login, password hashing, and JWT tokens
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
import bcrypt
import jwt
from cryptography.fernet import Fernet


class AuthService:
    """
    Authentication service for user management and security
    """

    def __init__(self, secret_key: str = None, encryption_key: str = None):
        """
        Initialize authentication service

        Args:
            secret_key: JWT secret key (from environment)
            encryption_key: Fernet encryption key for API credentials
        """
        self.secret_key = secret_key or os.environ.get('JWT_SECRET_KEY', self._generate_secret_key())
        self.encryption_key = encryption_key or os.environ.get('ENCRYPTION_KEY', Fernet.generate_key().decode())
        self.fernet = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key)

        # Token expiration times
        self.access_token_expires = timedelta(hours=1)
        self.refresh_token_expires = timedelta(days=30)

    @staticmethod
    def _generate_secret_key() -> str:
        """
        Generate a secure random secret key

        Returns:
            str: Random secret key
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt

        Args:
            password: Plain text password

        Returns:
            str: Hashed password
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify a password against its hash

        Args:
            password: Plain text password
            password_hash: Hashed password from database

        Returns:
            bool: True if password matches
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except Exception as e:
            print(f"[AuthService] Password verification error: {e}")
            return False

    def generate_token(
        self,
        user_id: int,
        token_type: str = 'access',
        additional_claims: dict = None
    ) -> Tuple[str, str, datetime]:
        """
        Generate JWT token

        Args:
            user_id: User ID
            token_type: 'access' or 'refresh'
            additional_claims: Additional JWT claims

        Returns:
            Tuple[str, str, datetime]: (token, jti, expires_at)
        """
        expires_delta = self.access_token_expires if token_type == 'access' else self.refresh_token_expires
        expires_at = datetime.utcnow() + expires_delta
        jti = secrets.token_urlsafe(32)

        payload = {
            'user_id': user_id,
            'type': token_type,
            'exp': expires_at,
            'iat': datetime.utcnow(),
            'jti': jti
        }

        if additional_claims:
            payload.update(additional_claims)

        token = jwt.encode(payload, self.secret_key, algorithm='HS256')

        return token, jti, expires_at

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode JWT token

        Args:
            token: JWT token string

        Returns:
            Optional[Dict]: Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            print("[AuthService] Token expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"[AuthService] Invalid token: {e}")
            return None

    def encrypt_api_key(self, api_key: str) -> str:
        """
        Encrypt API key using Fernet

        Args:
            api_key: Plain text API key

        Returns:
            str: Encrypted API key
        """
        if not api_key:
            return None
        return self.fernet.encrypt(api_key.encode()).decode()

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """
        Decrypt API key using Fernet

        Args:
            encrypted_key: Encrypted API key

        Returns:
            str: Plain text API key
        """
        if not encrypted_key:
            return None
        try:
            return self.fernet.decrypt(encrypted_key.encode()).decode()
        except Exception as e:
            print(f"[AuthService] Decryption error: {e}")
            return None

    @staticmethod
    def generate_verification_token() -> str:
        """
        Generate email verification token

        Returns:
            str: Random verification token
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_reset_token() -> str:
        """
        Generate password reset token

        Returns:
            str: Random reset token
        """
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_api_key() -> str:
        """
        Generate user API key for programmatic access

        Returns:
            str: Random API key
        """
        return f"cpk_{secrets.token_urlsafe(32)}"

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format

        Args:
            email: Email address

        Returns:
            bool: True if valid
        """
        import re
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """
        Validate password strength

        Args:
            password: Password to validate

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"

        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"

        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number"

        # Optional: Check for special characters
        # if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        #     return False, "Password must contain at least one special character"

        return True, ""

    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Validate username format

        Args:
            username: Username to validate

        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"

        if len(username) > 30:
            return False, "Username must be at most 30 characters long"

        if not username[0].isalpha():
            return False, "Username must start with a letter"

        if not all(c.isalnum() or c in '-_' for c in username):
            return False, "Username can only contain letters, numbers, hyphens, and underscores"

        return True, ""


# Singleton instance
auth_service = AuthService()
