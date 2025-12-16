"""
User Suspension Admin API Routes
사용자 이용 정지 관리 API
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from backend.database import db
from backend.models.user_suspension import UserSuspension
from backend.middleware.auth import admin_required

suspension_admin_bp = Blueprint('suspension_admin', __name__, url_prefix='/api/admin/suspensions')

@suspension_admin_bp.route('', methods=['GET'])
@admin_required
def get_suspensions():
    """정지 목록 조회"""
    try:
        status = request.args.get('status')
        email = request.args.get('email')
        suspension_type = request.args.get('type')
        
        query = UserSuspension.query
        
        if status:
            query = query.filter_by(status=status)
        if email:
            query = query.filter_by(email=email)
        if suspension_type:
            query = query.filter_by(suspension_type=suspension_type)
        
        suspensions = query.order_by(UserSuspension.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'suspensions': [s.to_dict() for s in suspensions],
            'count': len(suspensions)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@suspension_admin_bp.route('', methods=['POST'])
@admin_required
def create_suspension():
    """사용자 정지"""
    try:
        data = request.json
        
        # 종료일 계산
        end_date = None
        severity = data.get('severity', 'temporary')
        
        if severity == 'temporary':
            duration_days = int(data.get('duration_days', 7))
            end_date = datetime.utcnow() + timedelta(days=duration_days)
        elif 'end_date' in data:
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        # permanent는 end_date = None
        
        suspension = UserSuspension(
            email=data['email'],
            suspension_type=data.get('suspension_type', 'account'),
            severity=severity,
            reason=data['reason'],
            description=data.get('description', ''),
            notes=data.get('notes', ''),
            start_date=datetime.utcnow(),
            end_date=end_date,
            suspended_by=data.get('suspended_by', 'admin'),
            status='active'
        )
        
        db.session.add(suspension)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'suspension': suspension.to_dict(),
            'message': f'User {data["email"]} suspended successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@suspension_admin_bp.route('/<int:suspension_id>/lift', methods=['POST'])
@admin_required
def lift_suspension(suspension_id):
    """정지 해제"""
    try:
        data = request.json
        lifted_by = data.get('lifted_by', 'admin')
        
        success = UserSuspension.lift_suspension(suspension_id, lifted_by)
        
        if success:
            suspension = UserSuspension.query.get(suspension_id)
            return jsonify({
                'success': True,
                'suspension': suspension.to_dict(),
                'message': 'Suspension lifted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Suspension not found or already lifted'
            }), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@suspension_admin_bp.route('/<int:suspension_id>', methods=['PUT'])
@admin_required
def update_suspension(suspension_id):
    """정지 정보 수정"""
    try:
        suspension = UserSuspension.query.get(suspension_id)
        if not suspension:
            return jsonify({'success': False, 'error': 'Suspension not found'}), 404
        
        data = request.json
        
        # 업데이트 가능한 필드
        if 'description' in data:
            suspension.description = data['description']
        if 'notes' in data:
            suspension.notes = data['notes']
        if 'end_date' in data:
            suspension.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        if 'severity' in data:
            suspension.severity = data['severity']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'suspension': suspension.to_dict(),
            'message': 'Suspension updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@suspension_admin_bp.route('/<int:suspension_id>', methods=['DELETE'])
@admin_required
def delete_suspension(suspension_id):
    """정지 기록 삭제 (권장하지 않음, lift 사용 권장)"""
    try:
        suspension = UserSuspension.query.get(suspension_id)
        if not suspension:
            return jsonify({'success': False, 'error': 'Suspension not found'}), 404
        
        db.session.delete(suspension)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Suspension deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@suspension_admin_bp.route('/check', methods=['POST'])
@admin_required
def check_suspension():
    """사용자 정지 여부 확인"""
    try:
        data = request.json
        email = data['email']
        feature = data.get('feature', 'account')
        
        is_suspended = UserSuspension.is_suspended(email, feature)
        active_suspensions = UserSuspension.get_active_suspensions(email)
        can_access = UserSuspension.can_access(email, feature)
        
        return jsonify({
            'success': True,
            'email': email,
            'feature': feature,
            'is_suspended': is_suspended,
            'can_access': can_access,
            'active_suspensions': [s.to_dict() for s in active_suspensions],
            'count': len(active_suspensions)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@suspension_admin_bp.route('/expire', methods=['POST'])
@admin_required
def expire_suspensions():
    """만료된 정지 일괄 처리"""
    try:
        result = db.session.execute(db.text("SELECT expire_user_suspensions()"))
        expired_count = result.scalar()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'expired_count': expired_count,
            'message': f'{expired_count} suspensions expired'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@suspension_admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_suspension_stats():
    """정지 통계"""
    try:
        total = UserSuspension.query.count()
        active = UserSuspension.query.filter_by(status='active').count()
        lifted = UserSuspension.query.filter_by(status='lifted').count()
        expired = UserSuspension.query.filter_by(status='expired').count()
        
        # 타입별
        by_type = db.session.query(
            UserSuspension.suspension_type,
            db.func.count(UserSuspension.id)
        ).group_by(UserSuspension.suspension_type).all()
        
        # 사유별
        by_reason = db.session.query(
            UserSuspension.reason,
            db.func.count(UserSuspension.id)
        ).group_by(UserSuspension.reason).all()
        
        # 수준별
        by_severity = db.session.query(
            UserSuspension.severity,
            db.func.count(UserSuspension.id)
        ).group_by(UserSuspension.severity).all()
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'active': active,
                'lifted': lifted,
                'expired': expired,
                'by_type': {t: count for t, count in by_type},
                'by_reason': {r: count for r, count in by_reason},
                'by_severity': {s: count for s, count in by_severity}
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@suspension_admin_bp.route('/user/<email>', methods=['GET'])
@admin_required
def get_user_suspensions(email):
    """특정 사용자의 모든 정지 내역"""
    try:
        suspensions = UserSuspension.query.filter_by(email=email).all()
        active_suspensions = UserSuspension.get_active_suspensions(email)
        
        return jsonify({
            'success': True,
            'email': email,
            'all_suspensions': [s.to_dict() for s in suspensions],
            'active_suspensions': [s.to_dict() for s in active_suspensions],
            'count': {
                'total': len(suspensions),
                'active': len(active_suspensions)
            },
            'can_access': {
                'account': UserSuspension.can_access(email, 'account'),
                'trading': UserSuspension.can_access(email, 'trading'),
                'payment': UserSuspension.can_access(email, 'payment'),
                'withdrawal': UserSuspension.can_access(email, 'withdrawal')
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500