"""
Test routes for development and testing
"""
from flask import Blueprint, jsonify
from backend.services.websocket_service import get_websocket_service
import logging

logger = logging.getLogger(__name__)

test_bp = Blueprint('test', __name__, url_prefix='/api/test')


@test_bp.route('/notification', methods=['GET', 'POST'])
def test_notification():
    """Send a test notification via WebSocket"""
    try:
        ws_service = get_websocket_service()

        # Test surge alert data
        test_data = {
            'market': 'KRW-BTC',
            'score': 85,
            'current_price': 50000000,
            'recommendation': '🔔 테스트 알림입니다!'
        }

        # Broadcast to all connected clients
        ws_service.broadcast_surge_alert(test_data)

        logger.info(f"[Test] Sent test surge alert: {test_data['market']}")

        return jsonify({
            'success': True,
            'message': 'Test notification sent!',
            'data': test_data
        })

    except RuntimeError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'WebSocket service not initialized. Please connect a client first.'
        }), 503

    except Exception as e:
        logger.error(f"[Test] Error sending test notification: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@test_bp.route('/websocket-status', methods=['GET'])
def websocket_status():
    """Check WebSocket service status"""
    try:
        ws_service = get_websocket_service()

        status = {
            'initialized': True,
            'price_update_running': ws_service.price_update_thread is not None and ws_service.price_update_thread.is_alive(),
            'subscribed_markets': list(ws_service.price_subscribers.keys()),
            'connected_users': len(ws_service.user_sessions)
        }

        return jsonify({
            'success': True,
            'status': status
        })

    except RuntimeError as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status': {
                'initialized': False
            }
        }), 503
