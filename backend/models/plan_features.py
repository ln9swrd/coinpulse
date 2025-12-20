"""
CoinPulse Plan Features Model
Custom feature overrides for users
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from datetime import datetime

# Import unified Base from database connection
from backend.database.connection import Base


class UserFeatureOverride(Base):
    """
    User Feature Override model
    Allows admin to customize specific features for individual users
    """
    __tablename__ = 'user_feature_overrides'
    __table_args__ = {'extend_existing': True}

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # User reference
    user_id = Column(Integer, nullable=False, index=True, unique=True)

    # Feature overrides (stored as JSON)
    # Example: {"max_bots": 10, "api_access": true, "backtesting": true}
    features = Column(JSON, nullable=False, default={})

    # Metadata
    reason = Column(String(500), nullable=True)  # Why these overrides were applied
    created_by_admin_id = Column(Integer, nullable=True)  # Which admin created this
    expires_at = Column(DateTime, nullable=True)  # Optional expiration date

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserFeatureOverride(id={self.id}, user_id={self.user_id}, features={self.features})>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'features': self.features,
            'reason': self.reason,
            'created_by_admin_id': self.created_by_admin_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def is_expired(self):
        """Check if override has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


# Default feature sets for each plan
PLAN_FEATURES = {
    'free': {
        'manual_trading': False,
        'max_bots': 0,
        'indicators': ['basic'],
        'advanced_strategies': False,
        'backtesting': False,
        'api_access': False,
        'webhook_access': False,
        'priority_support': False,
        'email_alerts': True,
        'realtime_alerts': False,
        'data_export': False
    },
    'basic': {
        'manual_trading': True,
        'max_bots': 1,
        'indicators': ['basic', 'intermediate'],
        'advanced_strategies': False,
        'backtesting': False,
        'api_access': False,
        'webhook_access': False,
        'priority_support': False,
        'email_alerts': True,
        'realtime_alerts': False,
        'data_export': False
    },
    'pro': {
        'manual_trading': True,
        'max_bots': -1,  # Unlimited
        'indicators': ['basic', 'intermediate', 'advanced', 'ai'],
        'advanced_strategies': True,
        'backtesting': True,
        'api_access': True,
        'webhook_access': True,
        'priority_support': True,
        'email_alerts': True,
        'realtime_alerts': True,
        'data_export': True
    },
    'enterprise': {
        'manual_trading': True,
        'max_bots': -1,  # Unlimited
        'indicators': ['basic', 'intermediate', 'advanced', 'ai', 'custom'],
        'advanced_strategies': True,
        'backtesting': True,
        'api_access': True,
        'webhook_access': True,
        'priority_support': True,
        'email_alerts': True,
        'realtime_alerts': True,
        'data_export': True,
        'white_label': True,  # Enterprise only
        'dedicated_support': True,  # Enterprise only
        'custom_strategies': True  # Enterprise only
    }
}


def get_user_features(plan: str, overrides: dict = None) -> dict:
    """
    Get effective features for a user based on plan and overrides

    Args:
        plan: User's subscription plan ('free', 'basic', 'pro', 'enterprise')
        overrides: Optional feature overrides from UserFeatureOverride

    Returns:
        Dictionary of effective features
    """
    # Start with plan defaults
    features = PLAN_FEATURES.get(plan, PLAN_FEATURES['free']).copy()

    # Apply overrides if provided
    if overrides:
        features.update(overrides)

    return features
