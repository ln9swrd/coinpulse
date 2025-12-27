"""
User API Key Model
Stores encrypted Upbit API keys for each user
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from datetime import datetime
from backend.database.connection import Base


class UserAPIKey(Base):
    """
    User API Key model
    Stores encrypted Upbit API credentials for automated trading
    """
    __tablename__ = 'user_api_keys'
    __table_args__ = {'extend_existing': True}

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # User reference
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True, index=True)

    # Encrypted API credentials
    # IMPORTANT: These are encrypted using Fernet symmetric encryption
    access_key_encrypted = Column(Text, nullable=False)
    secret_key_encrypted = Column(Text, nullable=False)

    # API key metadata
    key_name = Column(String(100), nullable=True)  # User-defined name for this key
    permissions = Column(String(500), nullable=True)  # Comma-separated permissions (e.g., "trade,withdraw")

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)  # Verified by test API call

    # Last usage
    last_used_at = Column(DateTime, nullable=True)
    last_verified_at = Column(DateTime, nullable=True)

    # Error tracking
    error_count = Column(Integer, nullable=False, default=0)  # Consecutive API errors
    last_error = Column(Text, nullable=True)  # Last error message

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserAPIKey(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"

    def to_dict(self, include_keys=False):
        """
        Convert to dictionary for JSON serialization

        Args:
            include_keys: If True, include encrypted keys (for internal use only)

        Returns:
            Dictionary representation
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'key_name': self.key_name,
            'permissions': self.permissions.split(',') if self.permissions else [],
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'last_verified_at': self.last_verified_at.isoformat() if self.last_verified_at else None,
            'error_count': self.error_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

        if include_keys:
            # Only include for internal use (admin/debugging)
            data['access_key_encrypted'] = self.access_key_encrypted
            data['secret_key_encrypted'] = self.secret_key_encrypted

        return data

    def mark_used(self):
        """Mark API key as recently used"""
        self.last_used_at = datetime.utcnow()

    def mark_verified(self):
        """Mark API key as verified"""
        self.is_verified = True
        self.last_verified_at = datetime.utcnow()
        self.error_count = 0
        self.last_error = None

    def record_error(self, error_message: str):
        """Record an API error"""
        self.error_count += 1
        self.last_error = error_message

        # Auto-disable after 5 consecutive errors
        if self.error_count >= 5:
            self.is_active = False

    def reset_errors(self):
        """Reset error count after successful API call"""
        self.error_count = 0
        self.last_error = None
