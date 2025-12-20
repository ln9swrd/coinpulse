"""
CoinPulse Payment Confirmation API
Handle bank transfer payment confirmations
"""

import os
import sys
from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime
import jwt

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.connection import get_db_session
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

# Import unified Base from database connection
from backend.database.connection import Base

# Create Blueprint
payment_confirm_bp = Blueprint('payment_confirm', __name__, url_prefix='/api/payment-confirm')

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '7DfH2jzRD4lCfQ_llC4CObochoaGzaBBZLeODoftgWk')
ADMIN_EMAIL = 'ln9swrd@gmail.com'


class PaymentConfirmStatus(enum.Enum):
    """Payment confirmation status"""
    PENDING = "pending"      # 확인 대기중
    APPROVED = "approved"    # 승인됨
    REJECTED = "rejected"    # 거부됨


class PaymentConfirmation(Base):
    """
    Payment Confirmation model
    Users submit bank transfer confirmations
    """
    __tablename__ = 'payment_confirmations'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)

    # User info
    user_id = Column(Integer, nullable=False, index=True)
    user_email = Column(String(255), nullable=False)
    user_name = Column(String(100), nullable=False)
    user_phone = Column(String(20), nullable=True)

    # Payment info
    plan = Column(String(50), nullable=False)  # basic, pro
    billing_period = Column(String(20), nullable=False)  # monthly, annual
    amount = Column(Integer, nullable=False)  # Amount in KRW

    # Bank transfer details
    depositor_name = Column(String(100), nullable=False)  # 입금자명
    transfer_date = Column(DateTime, nullable=False)  # 입금 날짜/시간
    bank_name = Column(String(100), nullable=True)  # 은행명

    # Optional proof
    notes = Column(Text, nullable=True)  # 추가 메모

    # Status
    status = Column(SQLEnum(PaymentConfirmStatus), nullable=False, default=PaymentConfirmStatus.PENDING)

    # Admin response
    reviewed_by_admin = Column(String(255), nullable=True)  # Admin email who reviewed
    reviewed_at = Column(DateTime, nullable=True)
    admin_notes = Column(Text, nullable=True)  # Admin의 메모

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_email': self.user_email,
            'user_name': self.user_name,
            'user_phone': self.user_phone,
            'plan': self.plan,
            'billing_period': self.billing_period,
            'amount': self.amount,
            'depositor_name': self.depositor_name,
            'transfer_date': self.transfer_date.isoformat() if self.transfer_date else None,
            'bank_name': self.bank_name,
            'notes': self.notes,
            'status': self.status.value,
            'reviewed_by_admin': self.reviewed_by_admin,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


def verify_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, 'Token has expired'
    except jwt.InvalidTokenError:
        return None, 'Invalid token'


def get_current_user(request):
    """Get current user from Authorization header"""
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return None, None, 'Authorization header missing or invalid'

    token = auth_header.split(' ')[1]
    payload, error = verify_token(token)

    if error:
        return None, None, error

    return payload.get('user_id'), payload.get('email'), None


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id, email, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error
            }), 401

        request.user_id = user_id
        request.user_email = email
        return f(*args, **kwargs)

    return decorated_function


@payment_confirm_bp.route('/submit', methods=['POST'])
@require_auth
def submit_payment_confirmation():
    """
    Submit payment confirmation after bank transfer

    Request JSON:
    {
        "user_name": "홍길동",
        "user_phone": "010-1234-5678",
        "plan": "pro",
        "billing_period": "monthly",
        "amount": 99000,
        "depositor_name": "홍길동",
        "transfer_date": "2025-01-20T14:30:00",
        "bank_name": "신한은행",
        "notes": "점심 시간에 입금했습니다"
    }

    Response:
    {
        "success": true,
        "confirmation": {...},
        "message": "결제 확인 요청이 제출되었습니다"
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        required = ['user_name', 'plan', 'billing_period', 'amount', 'depositor_name', 'transfer_date']
        for field in required:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Parse transfer date
        try:
            transfer_date = datetime.fromisoformat(data['transfer_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid transfer_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'
            }), 400

        session = get_db_session()

        # Create payment confirmation
        confirmation = PaymentConfirmation(
            user_id=request.user_id,
            user_email=request.user_email,
            user_name=data['user_name'],
            user_phone=data.get('user_phone'),
            plan=data['plan'],
            billing_period=data['billing_period'],
            amount=data['amount'],
            depositor_name=data['depositor_name'],
            transfer_date=transfer_date,
            bank_name=data.get('bank_name'),
            notes=data.get('notes'),
            status=PaymentConfirmStatus.PENDING
        )

        session.add(confirmation)
        session.commit()

        # TODO: Send email notification to admin
        # send_email_to_admin(confirmation)

        return jsonify({
            'success': True,
            'confirmation': confirmation.to_dict(),
            'message': '결제 확인 요청이 제출되었습니다. 관리자 확인 후 플랜이 활성화됩니다.',
            'admin_email': ADMIN_EMAIL
        }), 200

    except Exception as e:
        session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@payment_confirm_bp.route('/my-confirmations', methods=['GET'])
@require_auth
def get_my_confirmations():
    """
    Get current user's payment confirmations

    Response:
    {
        "success": true,
        "confirmations": [...]
    }
    """
    try:
        session = get_db_session()

        confirmations = session.query(PaymentConfirmation).filter(
            PaymentConfirmation.user_id == request.user_id
        ).order_by(PaymentConfirmation.created_at.desc()).all()

        return jsonify({
            'success': True,
            'confirmations': [c.to_dict() for c in confirmations],
            'count': len(confirmations)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@payment_confirm_bp.route('/status/<int:confirmation_id>', methods=['GET'])
@require_auth
def get_confirmation_status(confirmation_id):
    """
    Get status of a specific payment confirmation

    Response:
    {
        "success": true,
        "confirmation": {...}
    }
    """
    try:
        session = get_db_session()

        confirmation = session.query(PaymentConfirmation).filter(
            PaymentConfirmation.id == confirmation_id,
            PaymentConfirmation.user_id == request.user_id
        ).first()

        if not confirmation:
            return jsonify({
                'success': False,
                'error': 'Payment confirmation not found'
            }), 404

        return jsonify({
            'success': True,
            'confirmation': confirmation.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        session.close()


@payment_confirm_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'payment_confirmation',
        'timestamp': datetime.utcnow().isoformat()
    }), 200
