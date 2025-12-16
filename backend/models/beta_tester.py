"""
Beta Tester Database Model
베타 테스터 관리를 위한 데이터베이스 모델
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from backend.database.connection import Base


class BetaTester(Base):
    __tablename__ = 'beta_testers'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100))

    # 혜택 타입: 'free_trial', 'discount', 'lifetime'
    benefit_type = Column(String(50), nullable=False, default='free_trial')

    # 혜택 값: free_trial(일수), discount(퍼센트), lifetime(0)
    benefit_value = Column(Integer, default=30)

    # 기간
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # Changed from start_date
    end_date = Column(DateTime, nullable=True)

    # 상태: 'pending', 'active', 'expired', 'cancelled'
    status = Column(String(20), default='pending', nullable=False)

    # 메모
    notes = Column(Text, nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<BetaTester(id={self.id}, email={self.email}, status={self.status})>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'name': self.name,
            'benefit_type': self.benefit_type,
            'benefit_value': self.benefit_value,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
