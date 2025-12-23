# -*- coding: utf-8 -*-
"""
User Agreement Models
사용자 동의 기록 모델

법적 보호를 위한 사용자 동의 이력 저장
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index, Text
from datetime import datetime
from backend.database.connection import Base


class UserAgreement(Base):
    """
    User Agreement Records
    사용자 동의 기록

    법적 문서(이용약관, 투자위험고지서 등)에 대한 사용자 동의 이력 저장
    """
    __tablename__ = 'user_agreements'
    __table_args__ = {'extend_existing': True}

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # User reference
    user_id = Column(Integer, nullable=False, index=True)

    # Agreement type
    agreement_type = Column(String(50), nullable=False)  # 'terms_of_service', 'risk_disclosure', 'privacy_policy'

    # Version (for tracking agreement updates)
    version = Column(String(20), nullable=False, default='1.0')  # e.g., '1.0', '1.1', '2.0'

    # Agreement status
    agreed = Column(Boolean, default=False, nullable=False)

    # IP address for legal proof
    ip_address = Column(String(45), nullable=True)  # IPv4: 15 chars, IPv6: 45 chars

    # User agent for device tracking
    user_agent = Column(Text, nullable=True)

    # Timestamps
    agreed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes for fast queries
    __table_args__ = (
        Index('idx_user_agreements_user_type', 'user_id', 'agreement_type'),
        Index('idx_user_agreements_agreed_at', 'agreed_at'),
        {'extend_existing': True}
    )

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'agreement_type': self.agreement_type,
            'version': self.version,
            'agreed': self.agreed,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'agreed_at': self.agreed_at.isoformat() if self.agreed_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<UserAgreement(id={self.id}, user_id={self.user_id}, type={self.agreement_type}, agreed={self.agreed})>"


# Agreement types constants
AGREEMENT_TYPES = {
    'TERMS_OF_SERVICE': 'terms_of_service',      # 이용약관
    'RISK_DISCLOSURE': 'risk_disclosure',         # 투자위험고지서
    'PRIVACY_POLICY': 'privacy_policy',           # 개인정보처리방침
    'AUTO_TRADING_RISK': 'auto_trading_risk'      # 자동매매 위험 동의
}

# Current versions
CURRENT_VERSIONS = {
    'terms_of_service': '1.0',
    'risk_disclosure': '1.0',
    'privacy_policy': '1.0',
    'auto_trading_risk': '1.0'
}


# 초기화 함수
def init_db(engine):
    """Create database tables"""
    Base.metadata.create_all(engine)
    print("[UserAgreement] Database table created: user_agreements")


if __name__ == "__main__":
    print("User Agreement Models v1.0")
    print("=" * 60)

    print("\n1. Agreement Types:")
    for key, value in AGREEMENT_TYPES.items():
        print(f"   - {key}: {value}")

    print("\n2. Current Versions:")
    for agreement_type, version in CURRENT_VERSIONS.items():
        print(f"   - {agreement_type}: v{version}")

    print("\n3. Sample Agreement:")
    agreement = UserAgreement(
        user_id=1,
        agreement_type='risk_disclosure',
        version='1.0',
        agreed=True,
        ip_address='192.168.1.1',
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    )
    print(f"   {agreement}")

    print("\n✅ Model defined successfully (v1.0)")
