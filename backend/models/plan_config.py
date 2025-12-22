"""
Plan Configuration Model
동적 요금제 관리 시스템
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from backend.database.connection import Base


class PlanConfig(Base):
    """
    요금제 설정 및 기능 제한 관리
    관리자가 요금제를 동적으로 관리할 수 있음
    """
    __tablename__ = 'plan_configs'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_code = Column(String(50), unique=True, nullable=False, index=True)
    # 'free', 'premium', 'pro', 'enterprise'

    # 기본 정보
    plan_name = Column(String(100), nullable=False)
    plan_name_ko = Column(String(100), nullable=True)  # 한글 이름
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)  # 표시 순서

    # 가격 정보
    monthly_price = Column(Integer, default=0, nullable=False)  # 월 구독료 (원)
    annual_price = Column(Integer, default=0, nullable=False)   # 연 구독료 (원)
    setup_fee = Column(Integer, default=0, nullable=False)       # 초기 설정비

    # 할인 정보
    annual_discount_rate = Column(Integer, default=0, nullable=False)  # 연 구독 할인율 (%)
    trial_days = Column(Integer, default=0, nullable=False)  # 무료 체험 기간

    # 기능 제한 - 모니터링
    max_coins = Column(Integer, default=1, nullable=False)  # 최대 모니터링 코인 수 (0 = 무제한)
    max_watchlists = Column(Integer, default=1, nullable=False)  # 최대 관심종목 개수

    # 기능 제한 - 자동매매
    auto_trading_enabled = Column(Boolean, default=False, nullable=False)
    max_auto_strategies = Column(Integer, default=0, nullable=False)  # 자동매매 전략 개수 (0 = 무제한)
    max_concurrent_trades = Column(Integer, default=0, nullable=False)  # 동시 거래 개수

    # 기능 제한 - 분석
    advanced_indicators = Column(Boolean, default=False, nullable=False)  # 고급 지표
    custom_indicators = Column(Boolean, default=False, nullable=False)   # 커스텀 지표
    backtesting_enabled = Column(Boolean, default=False, nullable=False) # 백테스팅

    # 기능 제한 - 데이터
    history_days = Column(Integer, default=7, nullable=False)  # 히스토리 보관 일수 (0 = 무제한)
    data_export = Column(Boolean, default=False, nullable=False)  # 데이터 내보내기
    api_access = Column(Boolean, default=False, nullable=False)   # API 접근

    # 기능 제한 - 알림 (Email Notifications) ✉️
    email_notifications_enabled = Column(Boolean, default=False, nullable=False)  # 이메일 알림 활성화
    daily_email_limit = Column(Integer, default=0, nullable=False)  # 일일 이메일 발송 한도 (0 = 무제한)
    signal_notifications = Column(Boolean, default=False, nullable=False)  # 시그널 알림
    portfolio_notifications = Column(Boolean, default=False, nullable=False)  # 포트폴리오 알림
    trade_notifications = Column(Boolean, default=False, nullable=False)  # 거래 실행 알림
    system_notifications = Column(Boolean, default=False, nullable=False)  # 시스템 알림

    # 기능 제한 - 지원
    support_level = Column(String(50), default='community', nullable=False)
    # 'community', 'email', 'priority', 'dedicated'
    response_time_hours = Column(Integer, default=72, nullable=False)  # 응답 시간

    # 기능 제한 - 기타
    white_labeling = Column(Boolean, default=False, nullable=False)  # 화이트라벨링
    sla_guarantee = Column(Boolean, default=False, nullable=False)   # SLA 보증
    custom_development = Column(Boolean, default=False, nullable=False)  # 맞춤 개발

    # 표시 설정
    is_active = Column(Boolean, default=True, nullable=False)  # 활성화 여부
    is_featured = Column(Boolean, default=False, nullable=False)  # 추천 플랜
    is_visible = Column(Boolean, default=True, nullable=False)  # 표시 여부

    # 마케팅
    badge_text = Column(String(50), nullable=True)  # 배지 텍스트 (예: "가장 인기", "최고 가치")
    cta_text = Column(String(100), nullable=True)   # CTA 버튼 텍스트

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<PlanConfig(id={self.id}, plan_code={self.plan_code}, plan_name={self.plan_name})>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'plan_code': self.plan_code,
            'plan_name': self.plan_name,
            'plan_name_ko': self.plan_name_ko,
            'description': self.description,
            'display_order': self.display_order,
            'price': {
                'monthly': self.monthly_price,
                'annual': self.annual_price,
                'setup_fee': self.setup_fee,
                'annual_discount_rate': self.annual_discount_rate
            },
            'trial_days': self.trial_days,
            'limits': {
                'max_coins': self.max_coins if self.max_coins > 0 else None,
                'max_watchlists': self.max_watchlists,
                'max_auto_strategies': self.max_auto_strategies if self.max_auto_strategies > 0 else None,
                'max_concurrent_trades': self.max_concurrent_trades if self.max_concurrent_trades > 0 else None,
                'history_days': self.history_days if self.history_days > 0 else None
            },
            'features': {
                'auto_trading': self.auto_trading_enabled,
                'advanced_indicators': self.advanced_indicators,
                'custom_indicators': self.custom_indicators,
                'backtesting': self.backtesting_enabled,
                'data_export': self.data_export,
                'api_access': self.api_access,
                'white_labeling': self.white_labeling,
                'sla_guarantee': self.sla_guarantee,
                'custom_development': self.custom_development
            },
            'notifications': {
                'email_enabled': self.email_notifications_enabled,
                'daily_email_limit': self.daily_email_limit if self.daily_email_limit > 0 else None,
                'signal_notifications': self.signal_notifications,
                'portfolio_notifications': self.portfolio_notifications,
                'trade_notifications': self.trade_notifications,
                'system_notifications': self.system_notifications
            },
            'support': {
                'level': self.support_level,
                'response_time_hours': self.response_time_hours
            },
            'display': {
                'is_active': self.is_active,
                'is_featured': self.is_featured,
                'is_visible': self.is_visible,
                'badge_text': self.badge_text,
                'cta_text': self.cta_text
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def get_active_plans(session):
        """활성화된 플랜 목록 조회 (표시 가능한 플랜만)"""
        return session.query(PlanConfig).filter(
            PlanConfig.is_active == True,
            PlanConfig.is_visible == True
        ).order_by(PlanConfig.display_order.asc()).all()

    @staticmethod
    def get_plan_by_code(plan_code, session):
        """플랜 코드로 플랜 조회"""
        return session.query(PlanConfig).filter(
            PlanConfig.plan_code == plan_code
        ).first()

    @staticmethod
    def check_feature_limit(subscription, feature, current_count, session):
        """
        기능 사용 제한 확인

        Args:
            subscription: 사용자 구독 정보
            feature: 확인할 기능 ('coins', 'strategies', 'trades', 'watchlists')
            current_count: 현재 사용 중인 개수
            session: 데이터베이스 세션

        Returns:
            dict: {
                'allowed': bool,
                'limit': int | None,  # None = unlimited
                'current': int,
                'remaining': int | None
            }
        """
        plan = session.query(PlanConfig).filter(
            PlanConfig.plan_code == subscription.plan
        ).first()

        if not plan:
            # 플랜이 없으면 FREE 플랜 기본값 사용
            return {
                'allowed': current_count < 1,
                'limit': 1,
                'current': current_count,
                'remaining': max(0, 1 - current_count)
            }

        # 기능별 제한 확인
        limit_map = {
            'coins': plan.max_coins,
            'strategies': plan.max_auto_strategies,
            'trades': plan.max_concurrent_trades,
            'watchlists': plan.max_watchlists
        }

        limit = limit_map.get(feature, 0)

        # 0 = 무제한
        if limit == 0:
            return {
                'allowed': True,
                'limit': None,
                'current': current_count,
                'remaining': None
            }

        # 제한이 있는 경우
        return {
            'allowed': current_count < limit,
            'limit': limit,
            'current': current_count,
            'remaining': max(0, limit - current_count)
        }
