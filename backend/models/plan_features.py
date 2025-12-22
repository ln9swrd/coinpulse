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
# Updated 2025.12.22: 관심 코인 기반 급등 알림 시스템
#
# 시스템 개요:
# - 급등 모니터링: AI가 전체 마켓을 스캔하여 급등 신호 감지
# - 관심 코인: 사용자가 선택한 우선 모니터링 코인 (최대 5개)
# - 급등 알림: 텔레그램으로 전송되는 매수 추천 알림
#
# 요금제별 제공량:
# - Free: 대시보드에서만 확인 가능 (알림 없음)
# - Basic: 주 3회 표시 (실제 5회 제공)
# - Pro: 주 10회 표시 (실제 20회 제공)
#
# 마케팅 전략: 실제 제공량을 표시량보다 높게 설정하여 고객 만족도 향상
#
# 참고 문서: docs/features/SURGE_ALERT_SYSTEM.md
PLAN_FEATURES = {
    'free': {
        'manual_trading': False,
        'max_surge_alerts': 0,  # 급등 알림 불가 (대시보드에서만 확인)
        'max_alerts_per_week': 0,  # 표시: 알림 없음
        'telegram_alerts': False,
        'surge_monitoring': True,  # 급등 모니터링 (view only)
        'favorite_coins': False,  # 관심 코인 설정 불가
        'advanced_indicators': False,
        'backtesting': False,
        'priority_support': False,
        'trade_history_days': 7
    },
    'basic': {
        'manual_trading': True,
        'max_surge_alerts': 5,  # 실제: 주 5회 급등 알림
        'max_alerts_per_week': 3,  # 표시: 주 3회
        'telegram_alerts': True,  # 텔레그램 급등 알림
        'surge_monitoring': True,
        'favorite_coins': True,  # 관심 코인 설정 가능 (최대 5개)
        'advanced_indicators': True,
        'backtesting': False,
        'priority_support': False,
        'trade_history_days': 90
    },
    'pro': {
        'manual_trading': True,
        'max_surge_alerts': 20,  # 실제: 주 20회 급등 알림
        'max_alerts_per_week': 10,  # 표시: 주 10회
        'telegram_alerts': True,  # 실시간 텔레그램 알림
        'surge_monitoring': True,
        'favorite_coins': True,  # 관심 코인 설정 가능 (최대 5개)
        'advanced_indicators': True,
        'backtesting': True,
        'priority_support': True,
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
