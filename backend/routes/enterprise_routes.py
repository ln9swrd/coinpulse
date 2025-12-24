# -*- coding: utf-8 -*-
"""
Enterprise Routes
Enterprise 플랜 상담 신청 API
"""

from flask import Blueprint, request, jsonify
from backend.models.enterprise_inquiry import EnterpriseInquiry
from backend.models.database import db
import re

enterprise_bp = Blueprint('enterprise', __name__, url_prefix='/api/enterprise')

def validate_email(email):
    """이메일 유효성 검사"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """전화번호 유효성 검사"""
    # 010-1234-5678, 01012345678 형식 모두 허용
    pattern = r'^01[0-9]-?[0-9]{3,4}-?[0-9]{4}$'
    return re.match(pattern, phone) is not None

@enterprise_bp.route('/inquiry', methods=['POST'])
def create_inquiry():
    """Enterprise 상담 신청"""
    try:
        data = request.get_json()

        # 필수 필드 검증
        required_fields = ['name', 'email', 'phone', 'trading_volume', 'message']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field} 필드는 필수입니다.'
                }), 400

        # 이메일 유효성 검증
        if not validate_email(data['email']):
            return jsonify({
                'success': False,
                'message': '올바른 이메일 형식이 아닙니다.'
            }), 400

        # 전화번호 유효성 검증
        if not validate_phone(data['phone']):
            return jsonify({
                'success': False,
                'message': '올바른 전화번호 형식이 아닙니다. (예: 010-1234-5678)'
            }), 400

        # 거래량 옵션 검증
        valid_volumes = ['under_10m', '10m_50m', '50m_100m', '100m_500m', 'over_500m']
        if data['trading_volume'] not in valid_volumes:
            return jsonify({
                'success': False,
                'message': '올바른 거래량 옵션을 선택해주세요.'
            }), 400

        # Enterprise Inquiry 생성
        inquiry = EnterpriseInquiry(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            company=data.get('company'),
            trading_volume=data['trading_volume'],
            message=data['message'],
            status='pending'
        )

        db.session.add(inquiry)
        db.session.commit()

        # TODO: 관리자에게 이메일/텔레그램 알림 전송
        # send_admin_notification(inquiry)

        return jsonify({
            'success': True,
            'message': '신청이 완료되었습니다. 24시간 내 담당자가 연락드리겠습니다.',
            'inquiry_id': inquiry.id
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[Enterprise Inquiry] Error: {str(e)}")
        return jsonify({
            'success': False,
            'message': '신청 처리 중 오류가 발생했습니다.'
        }), 500

@enterprise_bp.route('/inquiry/<int:inquiry_id>', methods=['GET'])
def get_inquiry(inquiry_id):
    """Enterprise 상담 신청 조회 (관리자 전용)"""
    try:
        inquiry = EnterpriseInquiry.query.get(inquiry_id)

        if not inquiry:
            return jsonify({
                'success': False,
                'message': '신청 내역을 찾을 수 없습니다.'
            }), 404

        return jsonify({
            'success': True,
            'inquiry': inquiry.to_dict()
        })

    except Exception as e:
        print(f"[Enterprise Inquiry] Get error: {str(e)}")
        return jsonify({
            'success': False,
            'message': '조회 중 오류가 발생했습니다.'
        }), 500

@enterprise_bp.route('/inquiries', methods=['GET'])
def get_inquiries():
    """Enterprise 상담 신청 목록 (관리자 전용)"""
    try:
        # 쿼리 파라미터
        status = request.args.get('status')  # pending, contacted, converted, rejected
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        # 기본 쿼리
        query = EnterpriseInquiry.query

        # 상태 필터
        if status:
            query = query.filter_by(status=status)

        # 최신순 정렬
        query = query.order_by(EnterpriseInquiry.created_at.desc())

        # 페이지네이션
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'success': True,
            'inquiries': [inquiry.to_dict() for inquiry in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        })

    except Exception as e:
        print(f"[Enterprise Inquiry] List error: {str(e)}")
        return jsonify({
            'success': False,
            'message': '목록 조회 중 오류가 발생했습니다.'
        }), 500

@enterprise_bp.route('/inquiry/<int:inquiry_id>/status', methods=['PUT'])
def update_inquiry_status(inquiry_id):
    """Enterprise 상담 신청 상태 업데이트 (관리자 전용)"""
    try:
        inquiry = EnterpriseInquiry.query.get(inquiry_id)

        if not inquiry:
            return jsonify({
                'success': False,
                'message': '신청 내역을 찾을 수 없습니다.'
            }), 404

        data = request.get_json()
        new_status = data.get('status')
        admin_note = data.get('admin_note')

        # 상태 검증
        valid_statuses = ['pending', 'contacted', 'converted', 'rejected']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'message': '올바른 상태를 선택해주세요.'
            }), 400

        # 상태 업데이트
        inquiry.status = new_status

        # 관리자 메모 업데이트
        if admin_note:
            inquiry.admin_note = admin_note

        # 타임스탬프 업데이트
        from datetime import datetime
        if new_status == 'contacted' and not inquiry.contacted_at:
            inquiry.contacted_at = datetime.utcnow()
        elif new_status == 'converted' and not inquiry.converted_at:
            inquiry.converted_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '상태가 업데이트되었습니다.',
            'inquiry': inquiry.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        print(f"[Enterprise Inquiry] Update error: {str(e)}")
        return jsonify({
            'success': False,
            'message': '상태 업데이트 중 오류가 발생했습니다.'
        }), 500
