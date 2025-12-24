"""
Feedback API Routes
사용자 피드백 수집 API
"""
from flask import Blueprint, request, jsonify
from backend.database.connection import get_db_session
from backend.models.feedback import Feedback
from backend.middleware.auth import admin_required
from backend.utils.auth_utils import require_auth
from backend.database.models import User
import logging

logger = logging.getLogger(__name__)

feedback_bp = Blueprint('feedback', __name__, url_prefix='/api/feedback')


@feedback_bp.route('', methods=['POST'])
@require_auth
def submit_feedback():
    """
    피드백 제출 (사용자)

    Request Body:
    {
        "type": "bug" | "feature" | "general",
        "priority": "urgent" | "high" | "normal" | "low",
        "subject": "피드백 제목",
        "content": "피드백 내용",
        "screenshot_url": "https://..." (optional)
    }
    """
    try:
        user_id = request.user_id
        data = request.get_json()

        # 필수 필드 검증
        required_fields = ['type', 'subject', 'content']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # 유효성 검증
        valid_types = ['bug', 'feature', 'general']
        valid_priorities = ['urgent', 'high', 'normal', 'low']

        if data['type'] not in valid_types:
            return jsonify({
                'success': False,
                'error': f'Invalid type. Must be one of: {", ".join(valid_types)}'
            }), 400

        priority = data.get('priority', 'normal')
        if priority not in valid_priorities:
            return jsonify({
                'success': False,
                'error': f'Invalid priority. Must be one of: {", ".join(valid_priorities)}'
            }), 400

        session = get_db_session()
        try:
            # 피드백 생성
            feedback = Feedback(
                user_id=user_id,
                type=data['type'],
                priority=priority,
                subject=data['subject'],
                content=data['content'],
                screenshot_url=data.get('screenshot_url'),
                status='new'
            )

            session.add(feedback)
            session.commit()
            session.refresh(feedback)

            logger.info(f"[Feedback] New feedback submitted: ID={feedback.id}, User={user_id}, Type={data['type']}, Priority={priority}")

            # 텔레그램 알림 전송 (비동기)
            try:
                from backend.services.telegram_bot import get_telegram_bot
                bot = get_telegram_bot()
                if bot:
                    # 사용자 정보 조회
                    user = session.query(User).filter(User.id == user_id).first()
                    username = user.username if user else f"User {user_id}"

                    # 우선순위 이모지
                    priority_emoji = {
                        'urgent': '🚨',
                        'high': '⚠️',
                        'normal': 'ℹ️',
                        'low': '💬'
                    }

                    # 타입 이모지
                    type_emoji = {
                        'bug': '🐛',
                        'feature': '💡',
                        'general': '💭'
                    }

                    message = f"""
{type_emoji.get(data['type'], '')} **새로운 피드백**

**사용자**: {username} (ID: {user_id})
**유형**: {data['type']}
**우선순위**: {priority_emoji.get(priority, '')} {priority}
**제목**: {data['subject']}
**내용**:
{data['content'][:200]}{'...' if len(data['content']) > 200 else ''}

**관리 페이지**: https://coinpulse.sinsi.ai/admin.html#feedback
                    """
                    bot.send_admin_notification(message.strip())
            except Exception as e:
                logger.warning(f"[Feedback] Failed to send Telegram notification: {e}")

            return jsonify({
                'success': True,
                'feedback_id': feedback.id,
                'message': '피드백이 성공적으로 제출되었습니다. 소중한 의견 감사합니다!'
            }), 201

        finally:
            session.close()

    except Exception as e:
        logger.error(f"[Feedback] Error submitting feedback: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@feedback_bp.route('/my', methods=['GET'])
@require_auth
def get_my_feedback(current_user):
    """내가 제출한 피드백 목록 조회 (사용자)"""
    try:
        user_id = current_user.id

        session = get_db_session()
        try:
            feedback_list = session.query(Feedback)\
                .filter(Feedback.user_id == user_id)\
                .order_by(Feedback.created_at.desc())\
                .all()

            return jsonify({
                'success': True,
                'feedback': [f.to_dict() for f in feedback_list],
                'count': len(feedback_list)
            })

        finally:
            session.close()

    except Exception as e:
        logger.error(f"[Feedback] Error getting my feedback: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================
# 관리자 전용 엔드포인트
# ============================================

@feedback_bp.route('/admin', methods=['GET'])
@admin_required
def get_all_feedback(current_user):
    """모든 피드백 목록 조회 (관리자)"""
    try:
        session = get_db_session()
        try:
            # 필터 파라미터
            status_filter = request.args.get('status')  # new, in_progress, resolved, closed
            type_filter = request.args.get('type')  # bug, feature, general
            priority_filter = request.args.get('priority')  # urgent, high, normal, low

            query = session.query(Feedback, User)\
                .join(User, Feedback.user_id == User.id)

            if status_filter:
                query = query.filter(Feedback.status == status_filter)
            if type_filter:
                query = query.filter(Feedback.type == type_filter)
            if priority_filter:
                query = query.filter(Feedback.priority == priority_filter)

            results = query.order_by(Feedback.created_at.desc()).all()

            feedback_list = []
            for feedback, user in results:
                feedback_dict = feedback.to_dict()
                feedback_dict['user'] = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
                feedback_list.append(feedback_dict)

            return jsonify({
                'success': True,
                'feedback': feedback_list,
                'count': len(feedback_list)
            })

        finally:
            session.close()

    except Exception as e:
        logger.error(f"[Feedback] Error getting all feedback: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@feedback_bp.route('/admin/<int:feedback_id>', methods=['PUT'])
@admin_required
def update_feedback(current_user, feedback_id):
    """
    피드백 상태/메모 업데이트 (관리자)

    Request Body:
    {
        "status": "new" | "in_progress" | "resolved" | "closed",
        "admin_notes": "관리자 메모"
    }
    """
    try:
        data = request.get_json()

        session = get_db_session()
        try:
            feedback = session.query(Feedback).filter(Feedback.id == feedback_id).first()

            if not feedback:
                return jsonify({
                    'success': False,
                    'error': 'Feedback not found'
                }), 404

            # 상태 업데이트
            if 'status' in data:
                valid_statuses = ['new', 'in_progress', 'resolved', 'closed']
                if data['status'] not in valid_statuses:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
                    }), 400
                feedback.status = data['status']

            # 관리자 메모 업데이트
            if 'admin_notes' in data:
                feedback.admin_notes = data['admin_notes']

            session.commit()

            logger.info(f"[Feedback] Feedback updated: ID={feedback_id}, Status={feedback.status}")

            return jsonify({
                'success': True,
                'message': 'Feedback updated successfully',
                'feedback': feedback.to_dict()
            })

        finally:
            session.close()

    except Exception as e:
        logger.error(f"[Feedback] Error updating feedback: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@feedback_bp.route('/admin/<int:feedback_id>', methods=['DELETE'])
@admin_required
def delete_feedback(current_user, feedback_id):
    """피드백 삭제 (관리자)"""
    try:
        session = get_db_session()
        try:
            feedback = session.query(Feedback).filter(Feedback.id == feedback_id).first()

            if not feedback:
                return jsonify({
                    'success': False,
                    'error': 'Feedback not found'
                }), 404

            session.delete(feedback)
            session.commit()

            logger.info(f"[Feedback] Feedback deleted: ID={feedback_id}")

            return jsonify({
                'success': True,
                'message': 'Feedback deleted successfully'
            })

        finally:
            session.close()

    except Exception as e:
        logger.error(f"[Feedback] Error deleting feedback: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
