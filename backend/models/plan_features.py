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
# Updated 2025.12.22: Revised structure based on user feedback
# Key changes:
# - Free: Portfolio tracking, price monitoring, surge detection (view only)
# - Basic: 3 alerts/week, telegram, advanced indicators (advertised lower than actual)
# - Pro: 10 alerts/week, all features (advertised lower than actual)
# Note: Actual limits are higher than advertised (marketing strategy)
PLAN_FEATURES = {
    'free': {
        'manual_trading': False,
        'max_auto_trading_alerts': 0,  # Cannot use auto-trading alerts
        'max_alerts_per_week': 0,  # Display: No alerts
        'telegram_alerts': False,
        'surge_monitoring': True,  # Price surge detection (view only)
        'advanced_indicators': False,
        'backtesting': False,
        'priority_support': False,
        'trade_history_days': 7
    },
    'basic': {
        'manual_trading': True,
        'max_auto_trading_alerts': 5,  # Actual: 5/week (advertise 3/week)
        'max_alerts_per_week': 3,  # Display: 3 alerts/week
        'telegram_alerts': True,  # Telegram notifications
        'surge_monitoring': True,
        'advanced_indicators': True,  # Advanced technical indicators
        'backtesting': False,
        'priority_support': False,
        'trade_history_days': 90
    },
    'pro': {
        'manual_trading': True,
        'max_auto_trading_alerts': 20,  # Actual: 20/week (advertise 10/week)
        'max_alerts_per_week': 10,  # Display: 10 alerts/week
        'telegram_alerts': True,  # Real-time Telegram notifications
        'surge_monitoring': True,
        'advanced_indicators': True,  # Advanced technical indicators
        'backtesting': True,  # Strategy simulation/backtesting
        'priority_support': True,  # Priority customer support
        'trade_history_days': -1  # Unlimited
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
