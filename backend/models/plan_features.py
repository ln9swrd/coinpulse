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
# Updated 2025.12.24 v3.0: 5단계 플랜 구조 (Free/Basic/Pro/Expert/Enterprise)
#
# 두 가지 독립적인 시스템:
# 1. 투자조언 알림 (Investment Advisory)
#    - 사용자가 선택한 코인에 대한 투자 조언
#    - 알림만 제공 (자동 실행 없음)
#    - 요금제별 코인 개수 제한
#
# 2. 급등 알림 자동매매 (Surge Auto Trading)
#    - 시스템이 전체 마켓 스캔하여 급등 감지
#    - 자동 매수 실행 (예산/금액 설정 기반)
#    - 요금제별 주간 횟수 제한
#
# 실제 데이터 (2025.12):
#    - 3주간 급등 시그널: 16개
#    - 주당 평균: 약 5개
#
# 참고 문서: docs/features/SURGE_ALERT_SYSTEM.md v2.0
PLAN_FEATURES = {
    'free': {
        'manual_trading': False,
        # 투자조언 알림
        'advisory_coins': False,  # 투자조언 코인 설정 불가
        'max_advisory_coins': 0,  # 선택 가능 코인 수: 0개
        # 급등 알림 자동매매
        'surge_auto_trading': False,  # 급등 자동매매 불가
        'max_surge_alerts': 0,  # 주간 자동매수 횟수: 0회
        'max_alerts_per_week': 0,  # 표시: 0회
        'surge_monitoring': True,  # 급등 모니터링 (상위 3개만 상세, 나머지 잠금)
        'telegram_alerts': False,
        'max_surge_budget': 0,  # 총 예산 제한: 불가
        # 기타 (단순화)
        'advanced_indicators': False,  # 고급 지표 (Custom 포함)
        # custom_indicators 제거 (advanced_indicators로 통합)
        'backtesting': False,
        'data_export': False,
        'api_access': False,
        'priority_support': False,
        'trade_history_days': 14,  # 7일 → 14일로 확대
        # 알림 단순화
        'important_notifications': False,  # 중요 알림
        'general_notifications': False  # 일반 알림
    },
    'basic': {
        'manual_trading': True,
        # 투자조언 알림
        'advisory_coins': True,  # 투자조언 코인 설정 가능
        'max_advisory_coins': 5,  # 선택 가능 코인 수: 5개
        # 급등 알림 자동매매
        'surge_auto_trading': True,  # 급등 자동매매 가능
        'max_surge_alerts': 5,  # 실제: 주 5회 자동매수
        'max_alerts_per_week': 3,  # 표시: 주 3회
        'surge_monitoring': True,  # 전체 상세 정보 접근
        'telegram_alerts': True,
        'max_surge_budget': 5000000,  # 총 예산 제한: 500만원
        # 기타 (단순화)
        'advanced_indicators': True,  # 고급 지표 (Custom 포함)
        # custom_indicators 제거
        'backtesting': True,  # 최근 3개월
        'backtesting_period_months': 3,
        'data_export': False,
        'api_access': False,
        'priority_support': False,
        'trade_history_days': 90,
        # 알림 단순화
        'important_notifications': True,  # 중요 알림
        'general_notifications': True  # 일반 알림
    },
    'pro': {
        'manual_trading': True,
        # 투자조언 알림
        'advisory_coins': True,  # 투자조언 코인 설정 가능
        'max_advisory_coins': 10,  # 선택 가능 코인 수: 10개
        # 급등 알림 자동매매
        'surge_auto_trading': True,  # 급등 자동매매 가능
        'max_surge_alerts': 10,  # 실제: 주 10회 자동매수
        'max_alerts_per_week': 5,  # 표시: 주 5회
        'surge_monitoring': True,
        'telegram_alerts': True,
        'max_surge_budget': 10000000,  # 총 예산 제한: 1천만원
        # 기타 (단순화)
        'advanced_indicators': True,  # 고급 지표 (Custom 포함)
        # custom_indicators 제거
        'backtesting': True,  # 최근 6개월
        'backtesting_period_months': 6,
        'data_export': True,  # CSV
        'api_access': False,
        'priority_support': False,
        'trade_history_days': 180,
        # 알림 단순화
        'important_notifications': True,  # 중요 알림
        'general_notifications': True  # 일반 알림
    },
    'expert': {
        'manual_trading': True,
        # 투자조언 알림
        'advisory_coins': True,  # 투자조언 코인 설정 가능
        'max_advisory_coins': 30,  # 선택 가능 코인 수: 30개
        # 급등 알림 자동매매
        'surge_auto_trading': True,  # 급등 자동매매 가능
        'max_surge_alerts': 20,  # 실제: 주 20회 자동매수
        'max_alerts_per_week': 10,  # 표시: 주 10회
        'surge_monitoring': True,
        'telegram_alerts': True,
        'max_surge_budget': -1,  # 총 예산 제한: 무제한
        # 기타 (단순화)
        'advanced_indicators': True,  # 고급 지표 (Custom 포함)
        # custom_indicators 제거
        'backtesting': True,  # 전체 기간
        'backtesting_period_months': -1,  # Unlimited
        'data_export': True,  # CSV, JSON
        'api_access': True,  # 제한적
        'priority_support': True,
        'trade_history_days': -1,  # Unlimited
        # 알림 단순화
        'important_notifications': True,  # 중요 알림
        'general_notifications': True  # 일반 알림
    },
    'enterprise': {
        'manual_trading': True,
        # 투자조언 알림
        'advisory_coins': True,  # 투자조언 코인 설정 가능
        'max_advisory_coins': -1,  # 선택 가능 코인 수: 무제한
        # 급등 알림 자동매매
        'surge_auto_trading': True,  # 급등 자동매매 가능
        'max_surge_alerts': -1,  # 실제: 무제한
        'max_alerts_per_week': -1,  # 표시: 무제한
        'surge_monitoring': True,
        'telegram_alerts': True,
        'max_surge_budget': -1,  # 총 예산 제한: 무제한
        # 기타 (단순화)
        'advanced_indicators': True,  # 고급 지표 (Custom 포함)
        # custom_indicators 제거
        'backtesting': True,  # 전체 기간
        'backtesting_period_months': -1,  # Unlimited
        'data_export': True,  # CSV, JSON, API 연동
        'api_access': True,  # 무제한
        'priority_support': True,
        'trade_history_days': -1,  # Unlimited
        'white_labeling': True,  # Enterprise only
        'dedicated_manager': True,  # 전담 매니저
        # 알림 단순화
        'important_notifications': True,  # 중요 알림
        'general_notifications': True  # 일반 알림
    }
}


def get_user_features(plan: str, overrides: dict = None) -> dict:
    """
    Get effective features for a user based on plan and overrides

    Args:
        plan: User's subscription plan ('free', 'basic', 'pro', 'expert', 'enterprise')
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
