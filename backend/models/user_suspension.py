"""
User Suspension System
사용자 이용 정지 관리
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from backend.database.connection import Base


class UserSuspension(Base):
    """
    사용자 이용 정지 관리
    계정 차단, 기능 제한 등
    """
    __tablename__ = 'user_suspensions'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    email = Column(String(255), nullable=False, index=True)

    # 정지 타입
    suspension_type = Column(String(50), nullable=False, index=True)
    # 'account' - 계정 완전 차단
    # 'trading' - 자동매매 차단
    # 'withdrawal' - 출금 차단
    # 'feature' - 특정 기능 차단
    # 'payment' - 결제 차단

    # 정지 수준
    severity = Column(String(20), default='warning', nullable=False)
    # 'warning' - 경고
    # 'temporary' - 일시 정지
    # 'permanent' - 영구 정지

    # 정지 사유
    reason = Column(String(100), nullable=False)
    # 'abuse' - 서비스 악용
    # 'fraud' - 부정 행위
    # 'violation' - 약관 위반
    # 'security' - 보안 이슈
    # 'payment_issue' - 결제 문제
    # 'manual' - 관리자 수동 조치

    # 상세 설명
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # 기간
    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_date = Column(DateTime, nullable=True)  # None = 영구

    # 상태
    status = Column(String(20), default='active', index=True, nullable=False)
    # 'active' - 정지 중
    # 'lifted' - 해제됨
    # 'expired' - 기간 만료

    # 조치자
    suspended_by = Column(String(100), nullable=True)  # 관리자 ID
    lifted_by = Column(String(100), nullable=True)     # 해제한 관리자

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    lifted_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<UserSuspension(id={self.id}, email={self.email}, type={self.suspension_type}, status={self.status})>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'suspension_type': self.suspension_type,
            'severity': self.severity,
            'reason': self.reason,
            'description': self.description,
            'notes': self.notes,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'suspended_by': self.suspended_by,
            'lifted_by': self.lifted_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'lifted_at': self.lifted_at.isoformat() if self.lifted_at else None
        }
