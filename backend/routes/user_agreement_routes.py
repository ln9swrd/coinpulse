# -*- coding: utf-8 -*-
"""
User Agreement Routes
사용자 동의 API 엔드포인트
"""

from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime
import jwt
import os

from backend.database.connection import get_db_session
from backend.models.user_agreement_models import UserAgreement, AGREEMENT_TYPES, CURRENT_VERSIONS

# Create blueprint
user_agreement_bp = Blueprint('user_agreement', __name__)

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '7DfH2jzRD4lCfQ_llC4CObochoaGzaBBZLeODoftgWk')


def verify_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, 'Token has expired'
    except jwt.InvalidTokenError:
        return None, 'Invalid token'


def get_current_user(request_obj):
    """Get current user from Authorization header"""
    auth_header = request_obj.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return None, 'Authorization header missing or invalid'

    token = auth_header.split(' ')[1]
    payload, error = verify_token(token)

    if error:
        return None, error

    return payload.get('user_id'), None


def require_auth(f):
    """
    Decorator to require JWT authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        # Add user_id to request context
        request.user_id = user_id

        return f(*args, **kwargs)

    return decorated_function


@user_agreement_bp.route('/api/agreements/record', methods=['POST'])
@require_auth
def record_agreement():
    """
    Record user agreement
    사용자 동의 기록

    Request Body:
    {
        "agreement_type": "risk_disclosure",  // Required
        "agreed": true,                        // Required
        "version": "1.0"                       // Optional (uses current version if not provided)
    }

    Response:
    {
        "success": true,
        "message": "Agreement recorded successfully",
        "agreement": {...}
    }
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data or 'agreement_type' not in data or 'agreed' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: agreement_type, agreed'
            }), 400

        agreement_type = data['agreement_type']
        agreed = data['agreed']

        # Validate agreement type
        if agreement_type not in AGREEMENT_TYPES.values():
            return jsonify({
                'success': False,
                'error': f'Invalid agreement_type. Must be one of: {list(AGREEMENT_TYPES.values())}'
            }), 400

        # Get version (use current if not provided)
        version = data.get('version', CURRENT_VERSIONS.get(agreement_type, '1.0'))

        # Get IP address from request
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()

        # Get user agent
        user_agent = request.headers.get('User-Agent', '')

        session = get_db_session()
        try:
            # Check if agreement already exists
            existing = session.query(UserAgreement).filter_by(
                user_id=request.user_id,
                agreement_type=agreement_type
            ).first()

            if existing:
                # Update existing agreement
                existing.agreed = agreed
                existing.version = version
                existing.ip_address = ip_address
                existing.user_agent = user_agent
                existing.agreed_at = datetime.utcnow()
                existing.updated_at = datetime.utcnow()
                session.commit()
                agreement = existing
            else:
                # Create new agreement
                agreement = UserAgreement(
                    user_id=request.user_id,
                    agreement_type=agreement_type,
                    version=version,
                    agreed=agreed,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                session.add(agreement)
                session.commit()

            return jsonify({
                'success': True,
                'message': 'Agreement recorded successfully',
                'agreement': agreement.to_dict()
            }), 200

        finally:
            session.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to record agreement: {str(e)}'
        }), 500


@user_agreement_bp.route('/api/agreements/status', methods=['GET'])
@require_auth
def get_agreement_status():
    """
    Get user agreement status
    사용자 동의 상태 조회

    Query Parameters:
    - agreement_type: Optional. Filter by specific type.

    Response:
    {
        "success": true,
        "agreements": [
            {
                "agreement_type": "risk_disclosure",
                "agreed": true,
                "version": "1.0",
                "agreed_at": "2025-01-01T00:00:00"
            }
        ]
    }
    """
    try:
        agreement_type = request.args.get('agreement_type')

        session = get_db_session()
        try:
            query = session.query(UserAgreement).filter_by(user_id=request.user_id)

            if agreement_type:
                query = query.filter_by(agreement_type=agreement_type)

            agreements = query.all()

            return jsonify({
                'success': True,
                'agreements': [a.to_dict() for a in agreements]
            }), 200

        finally:
            session.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get agreement status: {str(e)}'
        }), 500


@user_agreement_bp.route('/api/agreements/check', methods=['GET'])
@require_auth
def check_required_agreements():
    """
    Check if user has agreed to all required agreements
    필수 동의 확인

    Response:
    {
        "success": true,
        "all_agreed": false,
        "missing": ["risk_disclosure", "auto_trading_risk"],
        "agreements": {
            "terms_of_service": {"agreed": true, "version": "1.0"},
            "risk_disclosure": {"agreed": false, "version": null},
            ...
        }
    }
    """
    try:
        session = get_db_session()
        try:
            # Get all user agreements
            user_agreements = session.query(UserAgreement).filter_by(
                user_id=request.user_id
            ).all()

            # Convert to dict for easy lookup
            agreement_dict = {
                a.agreement_type: {
                    'agreed': a.agreed,
                    'version': a.version,
                    'agreed_at': a.agreed_at.isoformat() if a.agreed_at else None
                }
                for a in user_agreements
            }

            # Check all required agreements
            required_types = [
                'terms_of_service',
                'risk_disclosure',
                'privacy_policy'
            ]

            missing = []
            for req_type in required_types:
                if req_type not in agreement_dict or not agreement_dict[req_type]['agreed']:
                    missing.append(req_type)

            # Build complete status
            status = {}
            for agreement_type in AGREEMENT_TYPES.values():
                status[agreement_type] = agreement_dict.get(agreement_type, {
                    'agreed': False,
                    'version': None,
                    'agreed_at': None
                })

            return jsonify({
                'success': True,
                'all_agreed': len(missing) == 0,
                'missing': missing,
                'agreements': status
            }), 200

        finally:
            session.close()

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to check agreements: {str(e)}'
        }), 500


@user_agreement_bp.route('/api/agreements/versions', methods=['GET'])
def get_current_versions():
    """
    Get current agreement versions (public endpoint)
    현재 약관 버전 조회 (공개 엔드포인트)

    Response:
    {
        "success": true,
        "versions": {
            "terms_of_service": "1.0",
            "risk_disclosure": "1.0",
            ...
        }
    }
    """
    try:
        return jsonify({
            'success': True,
            'versions': CURRENT_VERSIONS
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get versions: {str(e)}'
        }), 500
