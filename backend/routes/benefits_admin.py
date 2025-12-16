"""
User Benefits Admin API Routes
범용 사용자 혜택 관리 API
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from backend.database import db
from backend.models.user_benefit import UserBenefit
from backend.middleware.auth import admin_required
import secrets

benefits_admin_bp = Blueprint('benefits_admin', __name__, url_prefix='/api/admin/benefits')

@benefits_admin_bp.route('', methods=['GET'])
@admin_required
def get_benefits():
    """혜택 목록 조회 (필터링 가능)"""
    try:
        category = request.args.get('category')
        status = request.args.get('status')
        email = request.args.get('email')
        
        query = UserBenefit.query
        
        if category:
            query = query.filter_by(category=category)
        if status:
            query = query.filter_by(status=status)
        if email:
            query = query.filter_by(email=email)
        
        benefits = query.order_by(UserBenefit.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'benefits': [b.to_dict() for b in benefits],
            'count': len(benefits)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@benefits_admin_bp.route('', methods=['POST'])
@admin_required
def create_benefit():
    """새 혜택 생성"""
    try:
        data = request.json
        
        # 코드 자동 생성 (제공되지 않은 경우)
        code = data.get('code')
        if not code and data.get('category') == 'coupon':
            code = f"COUP-{secrets.token_hex(4).upper()}"
        
        # 종료일 계산
        end_date = None
        if 'duration_days' in data:
            end_date = datetime.utcnow() + timedelta(days=int(data['duration_days']))
        elif 'end_date' in data:
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        
        # 혜택 생성
        benefit = UserBenefit(
            email=data['email'],
            category=data.get('category', 'promotion'),
            code=code,
            benefit_type=data['benefit_type'],
            benefit_value=int(data.get('benefit_value', 0)),
            applicable_to=data.get('applicable_to', 'all'),
            start_date=datetime.utcnow(),
            end_date=end_date,
            usage_limit=int(data.get('usage_limit', 1)),
            priority=int(data.get('priority', 100)),
            stackable=data.get('stackable', False),
            title=data.get('title', ''),
            description=data.get('description', ''),
            notes=data.get('notes', ''),
            status='active'
        )
        
        db.session.add(benefit)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'benefit': benefit.to_dict(),
            'message': 'Benefit created successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@benefits_admin_bp.route('/<int:benefit_id>', methods=['PUT'])
@admin_required
def update_benefit(benefit_id):
    """혜택 수정"""
    try:
        benefit = UserBenefit.query.get(benefit_id)
        if not benefit:
            return jsonify({'success': False, 'error': 'Benefit not found'}), 404
        
        data = request.json
        
        # 업데이트 가능한 필드
        updatable_fields = [
            'title', 'description', 'notes', 'status',
            'benefit_value', 'usage_limit', 'priority',
            'stackable', 'applicable_to'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(benefit, field, data[field])
        
        if 'end_date' in data:
            benefit.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'benefit': benefit.to_dict(),
            'message': 'Benefit updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@benefits_admin_bp.route('/<int:benefit_id>', methods=['DELETE'])
@admin_required
def delete_benefit(benefit_id):
    """혜택 삭제"""
    try:
        benefit = UserBenefit.query.get(benefit_id)
        if not benefit:
            return jsonify({'success': False, 'error': 'Benefit not found'}), 404
        
        db.session.delete(benefit)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Benefit deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@benefits_admin_bp.route('/bulk', methods=['POST'])
@admin_required
def bulk_create_benefits():
    """대량 혜택 생성 (프로모션용)"""
    try:
        data = request.json
        emails = data.get('emails', [])
        
        if not emails:
            return jsonify({'success': False, 'error': 'No emails provided'}), 400
        
        created = []
        
        for email in emails:
            # 코드 생성
            code = None
            if data.get('generate_codes'):
                code = f"{data.get('code_prefix', 'PROMO')}-{secrets.token_hex(4).upper()}"
            
            # 종료일 계산
            end_date = None
            if 'duration_days' in data:
                end_date = datetime.utcnow() + timedelta(days=int(data['duration_days']))
            
            benefit = UserBenefit(
                email=email,
                category=data.get('category', 'promotion'),
                code=code,
                benefit_type=data['benefit_type'],
                benefit_value=int(data.get('benefit_value', 0)),
                applicable_to=data.get('applicable_to', 'all'),
                end_date=end_date,
                usage_limit=int(data.get('usage_limit', 1)),
                stackable=data.get('stackable', False),
                title=data.get('title', ''),
                description=data.get('description', ''),
                status='active'
            )
            
            db.session.add(benefit)
            created.append(benefit)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'created_count': len(created),
            'benefits': [b.to_dict() for b in created],
            'message': f'{len(created)} benefits created successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@benefits_admin_bp.route('/expire', methods=['POST'])
@admin_required
def expire_benefits():
    """만료된 혜택 일괄 처리"""
    try:
        # SQL 함수 실행
        result = db.session.execute(db.text("SELECT expire_user_benefits()"))
        expired_count = result.scalar()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'expired_count': expired_count,
            'message': f'{expired_count} benefits expired'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@benefits_admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_benefit_stats():
    """혜택 통계"""
    try:
        total = UserBenefit.query.count()
        active = UserBenefit.query.filter_by(status='active').count()
        used = UserBenefit.query.filter_by(status='used').count()
        expired = UserBenefit.query.filter_by(status='expired').count()
        
        # 카테고리별
        by_category = db.session.query(
            UserBenefit.category,
            db.func.count(UserBenefit.id)
        ).group_by(UserBenefit.category).all()
        
        # 타입별
        by_type = db.session.query(
            UserBenefit.benefit_type,
            db.func.count(UserBenefit.id)
        ).group_by(UserBenefit.benefit_type).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'active': active,
                'used': used,
                'expired': expired,
                'by_category': {cat: count for cat, count in by_category},
                'by_type': {typ: count for typ, count in by_type}
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@benefits_admin_bp.route('/user/<email>', methods=['GET'])
@admin_required
def get_user_benefits(email):
    """특정 사용자의 모든 혜택 조회"""
    try:
        benefits = UserBenefit.query.filter_by(email=email).all()
        active_benefits = UserBenefit.get_active_benefits(email)
        
        # 적용 가능한 총 할인율
        total_discount = UserBenefit.calculate_total_discount(email)
        
        return jsonify({
            'success': True,
            'email': email,
            'all_benefits': [b.to_dict() for b in benefits],
            'active_benefits': [b.to_dict() for b in active_benefits],
            'total_discount': total_discount,
            'count': {
                'total': len(benefits),
                'active': len(active_benefits)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500