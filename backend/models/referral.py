"""
Referral System Models
친구 초대 시스템
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.connection import Base
import secrets
import string


class ReferralCode(Base):
    """사용자별 추천 코드"""
    __tablename__ = 'referral_codes'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    referrals = relationship('Referral', back_populates='referral_code', foreign_keys='Referral.referral_code_id')

    def __repr__(self):
        return f"<ReferralCode(user_id={self.user_id}, code={self.code})>"

    @staticmethod
    def generate_code():
        """6자리 랜덤 코드 생성"""
        chars = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(6))


class Referral(Base):
    """추천 관계 및 보상 추적"""
    __tablename__ = 'referrals'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    referrer_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)  # 추천한 사람
    referred_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)  # 추천받은 사람
    referral_code_id = Column(Integer, ForeignKey('referral_codes.id'), nullable=False)

    # 보상 정보
    reward_granted = Column(Boolean, default=False, nullable=False)  # 보상 지급 여부
    reward_days = Column(Integer, default=30, nullable=False)  # 보상 일수 (기본 30일)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reward_granted_at = Column(DateTime, nullable=True)

    # Relationships
    referral_code = relationship('ReferralCode', back_populates='referrals', foreign_keys=[referral_code_id])

    def __repr__(self):
        return f"<Referral(referrer_id={self.referrer_id}, referred_id={self.referred_id})>"
