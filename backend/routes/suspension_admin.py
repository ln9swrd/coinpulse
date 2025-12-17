"""
User Suspension Admin API Routes
사용자 이용 정지 관리 API
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from backend.database.connection import get_db_session
from backend.models.user_suspension import UserSuspension
from backend.middleware.auth import admin_required
from sqlalchemy import func, text

suspension_admin_bp = Blueprint('suspension_admin', __name__, url_prefix='/api/admin/suspensions')

@suspension_admin_bp.route('', methods=['GET'])
@admin_required
def get_suspensions():
    """정지 목록 조회"""
    session = get_db_session()
    try:
        status = request.args.get('status')
        email = request.args.get('email')
        suspension_type = request.args.get('type')

        query = session.query(UserSuspension)

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
    finally:
        session.close()

@suspension_admin_bp.route('', methods=['POST'])
@admin_required
def create_suspension():
    """사용자 정지"""
    session = get_db_session()
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

        session.add(suspension)
        session.commit()

        return jsonify({
            'success': True,
            'suspension': suspension.to_dict(),
            'message': f'User {data["email"]} suspended successfully'
        })
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@suspension_admin_bp.route('/<int:suspension_id>/lift', methods=['POST'])
@admin_required
def lift_suspension(suspension_id):
    """정지 해제"""
    session = get_db_session()
    try:
        data = request.json
        lifted_by = data.get('lifted_by', 'admin')

        success = UserSuspension.lift_suspension(suspension_id, lifted_by, session)

        if success:
            suspension = session.query(UserSuspension).filter_by(id=suspension_id).first()
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
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@suspension_admin_bp.route('/<int:suspension_id>', methods=['PUT'])
@admin_required
def update_suspension(suspension_id):
    """정지 정보 수정"""
    session = get_db_session()
    try:
        suspension = session.query(UserSuspension).filter_by(id=suspension_id).first()
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

        session.commit()

        return jsonify({
            'success': True,
            'suspension': suspension.to_dict(),
            'message': 'Suspension updated successfully'
        })
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@suspension_admin_bp.route('/<int:suspension_id>', methods=['DELETE'])
@admin_required
def delete_suspension(suspension_id):
    """정지 기록 삭제 (권장하지 않음, lift 사용 권장)"""
    session = get_db_session()
    try:
        suspension = session.query(UserSuspension).filter_by(id=suspension_id).first()
        if not suspension:
            return jsonify({'success': False, 'error': 'Suspension not found'}), 404

        session.delete(suspension)
        session.commit()

        return jsonify({
            'success': True,
            'message': 'Suspension deleted successfully'
        })
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@suspension_admin_bp.route('/check', methods=['POST'])
@admin_required
def check_suspension():
    """사용자 정지 여부 확인"""
    session = get_db_session()
    try:
        data = request.json
        email = data['email']
        feature = data.get('feature', 'account')

        is_suspended = UserSuspension.is_suspended(email, feature, session)
        active_suspensions = UserSuspension.get_active_suspensions(email, session)
        can_access = UserSuspension.can_access(email, feature, session)

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
    finally:
        session.close()

@suspension_admin_bp.route('/expire', methods=['POST'])
@admin_required
def expire_suspensions():
    """만료된 정지 일괄 처리"""
    session = get_db_session()
    try:
        result = session.execute(text("SELECT expire_user_suspensions()"))
        expired_count = result.scalar()
        session.commit()

        return jsonify({
            'success': True,
            'expired_count': expired_count,
            'message': f'{expired_count} suspensions expired'
        })
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@suspension_admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_suspension_stats():
    """정지 통계"""
    session = get_db_session()
    try:
        total = session.query(UserSuspension).count()
        active = session.query(UserSuspension).filter_by(status='active').count()
        lifted = session.query(UserSuspension).filter_by(status='lifted').count()
        expired = session.query(UserSuspension).filter_by(status='expired').count()

        # 타입별
        by_type = session.query(
            UserSuspension.suspension_type,
            func.count(UserSuspension.id)
        ).group_by(UserSuspension.suspension_type).all()

        # 사유별
        by_reason = session.query(
            UserSuspension.reason,
            func.count(UserSuspension.id)
        ).group_by(UserSuspension.reason).all()

        # 수준별
        by_severity = session.query(
            UserSuspension.severity,
            func.count(UserSuspension.id)
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
    finally:
        session.close()

@suspension_admin_bp.route('/user/<email>', methods=['GET'])
@admin_required
def get_user_suspensions(email):
    """특정 사용자의 모든 정지 내역"""
    session = get_db_session()
    try:
        suspensions = session.query(UserSuspension).filter_by(email=email).all()
        active_suspensions = UserSuspension.get_active_suspensions(email, session)

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
                'account': UserSuspension.can_access(email, 'account', session),
                'trading': UserSuspension.can_access(email, 'trading', session),
                'payment': UserSuspension.can_access(email, 'payment', session),
                'withdrawal': UserSuspension.can_access(email, 'withdrawal', session)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()
