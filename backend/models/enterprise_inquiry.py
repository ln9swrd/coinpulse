# -*- coding: utf-8 -*-
"""
Enterprise Inquiry Model
Enterprise 플랜 상담 신청 모델
"""

from datetime import datetime
from backend.models.database import db

class EnterpriseInquiry(db.Model):
    """Enterprise 상담 신청"""
    __tablename__ = 'enterprise_inquiries'

    id = db.Column(db.Integer, primary_key=True)

    # 기본 정보
    name = db.Column(db.String(100), nullable=False, comment='신청자 이름')
    email = db.Column(db.String(255), nullable=False, comment='연락 이메일')
    phone = db.Column(db.String(50), nullable=False, comment='연락처')
    company = db.Column(db.String(255), nullable=True, comment='회사명')

    # 거래 정보
    trading_volume = db.Column(db.String(50), nullable=False, comment='예상 월 거래량')
    message = db.Column(db.Text, nullable=False, comment='문의 내용')

    # 상태 관리
    status = db.Column(db.String(20), default='pending', comment='처리 상태')
    # pending: 대기, contacted: 연락 완료, converted: 계약 완료, rejected: 거절

    # 관리자 메모
    admin_note = db.Column(db.Text, nullable=True, comment='관리자 메모')
    contacted_at = db.Column(db.DateTime, nullable=True, comment='최초 연락 일시')
    converted_at = db.Column(db.DateTime, nullable=True, comment='계약 완료 일시')

    # 타임스탬프
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, comment='생성일시')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment='수정일시')

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'trading_volume': self.trading_volume,
            'message': self.message,
            'status': self.status,
            'admin_note': self.admin_note,
            'contacted_at': self.contacted_at.isoformat() if self.contacted_at else None,
            'converted_at': self.converted_at.isoformat() if self.converted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<EnterpriseInquiry {self.id}: {self.name} ({self.status})>'
