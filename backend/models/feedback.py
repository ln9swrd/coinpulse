"""
Feedback Model
사용자 피드백 모델
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func
from backend.database.connection import Base


class Feedback(Base):
    """사용자 피드백 테이블"""
    __tablename__ = 'feedback'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(20), nullable=False)  # bug, feature, general
    priority = Column(String(20), nullable=False, default='normal')  # urgent, high, normal, low
    subject = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    screenshot_url = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default='new')  # new, in_progress, resolved, closed
    admin_notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        CheckConstraint("type IN ('bug', 'feature', 'general')", name='feedback_type_check'),
        CheckConstraint("priority IN ('urgent', 'high', 'normal', 'low')", name='feedback_priority_check'),
        CheckConstraint("status IN ('new', 'in_progress', 'resolved', 'closed')", name='feedback_status_check'),
        Index('idx_feedback_user_id', 'user_id'),
        Index('idx_feedback_type', 'type'),
        Index('idx_feedback_status', 'status'),
        Index('idx_feedback_created_at', 'created_at'),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'priority': self.priority,
            'subject': self.subject,
            'content': self.content,
            'screenshot_url': self.screenshot_url,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
