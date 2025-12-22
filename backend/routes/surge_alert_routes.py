# -*- coding: utf-8 -*-
"""
Surge Alert Routes
급등 알림 기록 조회 및 통계 API

참고 문서: docs/features/SURGE_ALERT_SYSTEM.md
"""

from flask import Blueprint, request, jsonify
import logging

from backend.database.connection import get_db_session
from backend.utils.auth_utils import require_auth
from backend.services.surge_alert_service import get_surge_alert_service
from backend.models.surge_alert_models import SurgeAlert
from backend.models.plan_features import get_user_features

logger = logging.getLogger(__name__)

# Create Blueprint
surge_alert_bp = Blueprint('surge_alerts', __name__, url_prefix='/api/surge/alerts')


@surge_alert_bp.route('', methods=['GET'])
@require_auth
def get_user_alerts(current_user):
    """
    Get user's alert history

    Query parameters:
        - limit: Maximum number of alerts (default: 50)
        - week: Filter by week number (optional)

    Returns:
        JSON response with alerts list
    """
    try:
        session = get_db_session()
        service = get_surge_alert_service(session)

        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        week_number = request.args.get('week', None, type=int)

        # Get alerts
        alerts = service.get_user_alerts(
            user_id=current_user.id,
            limit=limit,
            week_number=week_number
        )

        logger.info(f"[SurgeAlerts] Retrieved {len(alerts)} alerts for user {current_user.id}")

        return jsonify({
            'success': True,
            'alerts': [alert.to_dict() for alert in alerts],
            'count': len(alerts)
        }), 200

    except Exception as e:
        logger.error(f"[SurgeAlerts] Error getting alerts for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get alerts'
        }), 500


@surge_alert_bp.route('/weekly-count', methods=['GET'])
@require_auth
def get_weekly_count(current_user):
    """
    Get user's alert count for current week

    Returns:
        JSON response with weekly count and limits
    """
    try:
        session = get_db_session()
        service = get_surge_alert_service(session)

        # Get user's plan
        plan = current_user.plan or 'free'
        features = get_user_features(plan)

        # Get counts
        current_count = service.get_weekly_alert_count(current_user.id)
        max_alerts_actual = features.get('max_surge_alerts', 0)
        max_alerts_display = features.get('max_alerts_per_week', 0)

        # Calculate remaining
        remaining = max(0, max_alerts_actual - current_count)

        # Get current week number
        current_week = SurgeAlert.get_current_week_number()

        logger.info(f"[SurgeAlerts] User {current_user.id} weekly count: {current_count}/{max_alerts_actual}")

        return jsonify({
            'success': True,
            'current_count': current_count,
            'max_alerts': max_alerts_display,  # Display limit (marketing)
            'max_alerts_actual': max_alerts_actual,  # Actual limit
            'remaining': remaining,
            'week_number': current_week,
            'can_receive': current_count < max_alerts_actual and plan != 'free'
        }), 200

    except Exception as e:
        logger.error(f"[SurgeAlerts] Error getting weekly count for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get weekly count'
        }), 500


@surge_alert_bp.route('/stats', methods=['GET'])
@require_auth
def get_alert_stats(current_user):
    """
    Get alert statistics for user

    Returns:
        JSON response with statistics
    """
    try:
        session = get_db_session()
        service = get_surge_alert_service(session)

        # Get stats
        stats = service.get_alert_stats(current_user.id)

        logger.info(f"[SurgeAlerts] User {current_user.id} stats: {stats}")

        return jsonify({
            'success': True,
            'stats': stats
        }), 200

    except Exception as e:
        logger.error(f"[SurgeAlerts] Error getting stats for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get statistics'
        }), 500


@surge_alert_bp.route('/<int:alert_id>/action', methods=['POST'])
@require_auth
def record_user_action(current_user, alert_id):
    """
    Record user's action on an alert

    Request body:
        {
            "action": "bought" | "ignored" | "added_to_favorites"
        }

    Returns:
        JSON response confirming action recorded
    """
    try:
        session = get_db_session()
        data = request.get_json()

        if not data or 'action' not in data:
            return jsonify({
                'success': False,
                'error': 'Action is required'
            }), 400

        action = data['action']
        valid_actions = ['bought', 'ignored', 'added_to_favorites']

        if action not in valid_actions:
            return jsonify({
                'success': False,
                'error': f'Invalid action. Must be one of: {", ".join(valid_actions)}'
            }), 400

        # Find alert
        alert = session.query(SurgeAlert)\
            .filter(
                SurgeAlert.id == alert_id,
                SurgeAlert.user_id == current_user.id
            )\
            .first()

        if not alert:
            return jsonify({
                'success': False,
                'error': 'Alert not found'
            }), 404

        # Update action
        from datetime import datetime
        alert.user_action = action
        alert.action_timestamp = datetime.utcnow()

        session.commit()

        logger.info(f"[SurgeAlerts] User {current_user.id} action '{action}' on alert {alert_id}")

        return jsonify({
            'success': True,
            'message': 'Action recorded',
            'alert': alert.to_dict()
        }), 200

    except Exception as e:
        session.rollback()
        logger.error(f"[SurgeAlerts] Error recording action for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to record action'
        }), 500


@surge_alert_bp.route('/test', methods=['POST'])
@require_auth
def test_alert(current_user):
    """
    Send a test alert to user (for testing purposes)

    Request body:
        {
            "market": "KRW-BTC",
            "confidence": 85.5
        }

    Returns:
        JSON response with test alert details
    """
    try:
        session = get_db_session()
        service = get_surge_alert_service(session)
        data = request.get_json()

        if not data or 'market' not in data:
            return jsonify({
                'success': False,
                'error': 'Market is required'
            }), 400

        market = data['market']
        coin = market.split('-')[1] if '-' in market else market
        confidence = data.get('confidence', 85.0)
        current_price = data.get('current_price', 50000000)
        target_price = data.get('target_price', 52000000)
        expected_return = ((target_price - current_price) / current_price) * 100

        # Get user plan
        plan = current_user.plan or 'free'

        # Send test alert
        success, alert = service.send_alert_to_user(
            user_id=current_user.id,
            plan=plan,
            market=market,
            coin=coin,
            confidence=confidence,
            current_price=current_price,
            target_price=target_price,
            expected_return=expected_return
        )

        if success:
            return jsonify({
                'success': True,
                'message': 'Test alert sent',
                'alert': alert.to_dict() if alert else None
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send test alert',
                'alert': alert.to_dict() if alert else None
            }), 400

    except Exception as e:
        logger.error(f"[SurgeAlerts] Error sending test alert for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
