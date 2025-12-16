"""
User Benefit System - Universal Benefit Management
사용자별 혜택 관리 시스템 (범용)
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from backend.database.connection import Base


class UserBenefit(Base):
    """
    범용 사용자 혜택 관리 테이블
    베타 테스터, 프로모션, 이벤트 등 모든 혜택 관리
    """
    __tablename__ = 'user_benefits'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    email = Column(String(255), index=True, nullable=True)

    # 혜택 분류
    category = Column(String(50), nullable=False, index=True)
    # 'beta_tester', 'promotion', 'event', 'referral', 'vip', 'coupon'

    # 혜택 코드 (쿠폰 코드 등)
    code = Column(String(100), unique=True, index=True, nullable=True)

    # 혜택 타입
    benefit_type = Column(String(50), nullable=False)
    # 'free_trial', 'discount', 'credit', 'upgrade', 'feature_unlock'

    # 혜택 값
    benefit_value = Column(Integer, default=0)
    # discount: 퍼센트(%), credit: 금액, free_trial: 일수

    # 적용 대상
    applicable_to = Column(String(100), nullable=True)
    # 'all', 'premium', 'pro', 'specific_feature'

    # 기간
    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_date = Column(DateTime, nullable=True)

    # 사용 제한
    usage_limit = Column(Integer, default=1)  # 최대 사용 횟수
    usage_count = Column(Integer, default=0)  # 현재 사용 횟수

    # 우선순위 (낮을수록 먼저 적용)
    priority = Column(Integer, default=100, nullable=False)

    # 상태
    status = Column(String(20), default='active', index=True, nullable=False)
    # 'pending', 'active', 'used', 'expired', 'cancelled'

    # 중복 허용 여부
    stackable = Column(Boolean, default=False, nullable=False)

    # 설명/메모
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # 발급자
    issued_by = Column(String(100), nullable=True)  # 관리자 ID

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<UserBenefit(id={self.id}, email={self.email}, category={self.category}, status={self.status})>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'category': self.category,
            'code': self.code,
            'benefit_type': self.benefit_type,
            'benefit_value': self.benefit_value,
            'applicable_to': self.applicable_to,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'usage_limit': self.usage_limit,
            'usage_count': self.usage_count,
            'priority': self.priority,
            'status': self.status,
            'stackable': self.stackable,
            'title': self.title,
            'description': self.description,
            'notes': self.notes,
            'issued_by': self.issued_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None
        }
