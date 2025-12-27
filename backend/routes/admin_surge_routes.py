# -*- coding: utf-8 -*-
"""
Admin Surge Settings Routes
관리자 급등 감지 시스템 설정 API
"""
from flask import Blueprint, jsonify, request
from backend.database.connection import get_db_session
from backend.models.surge_system_settings import SurgeSystemSettings
from backend.middleware.auth_middleware import require_admin
from sqlalchemy import text

admin_surge_bp = Blueprint('admin_surge', __name__)


@admin_surge_bp.route('/api/admin/surge/settings', methods=['GET'])
@require_admin
def get_surge_settings():
    """
    Get current surge system settings

    Returns:
        {
            "success": true,
            "settings": {...}
        }
    """
    try:
        with get_db_session() as session:
            settings = session.query(SurgeSystemSettings).filter_by(id=1).first()

            if not settings:
                # Create default settings if not exists
                settings = SurgeSystemSettings(id=1)
                settings.set_analysis_config(SurgeSystemSettings.get_default_analysis_config())
                session.add(settings)
                session.commit()

            return jsonify({
                'success': True,
                'settings': settings.to_dict()
            }), 200

    except Exception as e:
        print(f"[AdminSurge] Get settings error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_surge_bp.route('/api/admin/surge/settings', methods=['PUT'])
@require_admin
def update_surge_settings():
    """
    Update surge system settings

    Request body:
        {
            "base_min_score": 60,
            "telegram_min_score": 70,
            "db_save_threshold": 60,
            "check_interval": 300,
            "monitor_coins_count": 50,
            "duplicate_alert_hours": 24,
            "analysis_config": {
                "volume_increase_threshold": 1.5,
                "rsi_oversold_level": 35,
                ...
            },
            "worker_enabled": true,
            "scheduler_enabled": true,
            "notes": "Updated by admin"
        }

    Returns:
        {
            "success": true,
            "message": "Settings updated",
            "settings": {...}
        }
    """
    try:
        data = request.get_json()
        admin_email = request.user_email  # From middleware

        with get_db_session() as session:
            settings = session.query(SurgeSystemSettings).filter_by(id=1).first()

            if not settings:
                settings = SurgeSystemSettings(id=1)
                session.add(settings)

            # Update fields
            if 'base_min_score' in data:
                settings.base_min_score = int(data['base_min_score'])
            if 'telegram_min_score' in data:
                settings.telegram_min_score = int(data['telegram_min_score'])
            if 'db_save_threshold' in data:
                settings.db_save_threshold = int(data['db_save_threshold'])
            if 'check_interval' in data:
                settings.check_interval = int(data['check_interval'])
            if 'monitor_coins_count' in data:
                settings.monitor_coins_count = int(data['monitor_coins_count'])
            if 'duplicate_alert_hours' in data:
                settings.duplicate_alert_hours = int(data['duplicate_alert_hours'])
            if 'worker_enabled' in data:
                settings.worker_enabled = bool(data['worker_enabled'])
            if 'scheduler_enabled' in data:
                settings.scheduler_enabled = bool(data['scheduler_enabled'])
            if 'analysis_config' in data:
                settings.set_analysis_config(data['analysis_config'])
            if 'notes' in data:
                settings.notes = data['notes']

            settings.updated_by = admin_email

            session.commit()

            return jsonify({
                'success': True,
                'message': 'Settings updated successfully',
                'settings': settings.to_dict()
            }), 200

    except Exception as e:
        print(f"[AdminSurge] Update settings error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_surge_bp.route('/api/admin/surge/status', methods=['GET'])
@require_admin
def get_surge_status():
    """
    Get current surge system status

    Returns:
        {
            "success": true,
            "status": {
                "worker_running": true,
                "scheduler_running": true,
                "last_scan": "2025-12-27T...",
                "active_signals": 5,
                "monitored_coins": 50,
                "settings": {...}
            }
        }
    """
    try:
        with get_db_session() as session:
            # Get settings
            settings = session.query(SurgeSystemSettings).filter_by(id=1).first()

            # Get active signals count
            active_count_query = text("""
                SELECT COUNT(*) FROM surge_alerts
                WHERE status = 'pending'
            """)
            active_count = session.execute(active_count_query).scalar() or 0

            # Get last scan time (최근 알림 발송 시간)
            last_scan_query = text("""
                SELECT MAX(sent_at) FROM surge_alerts
            """)
            last_scan = session.execute(last_scan_query).scalar()

            # Get monitored coins (from cache)
            monitored_query = text("""
                SELECT COUNT(DISTINCT market) FROM surge_candidates_cache
            """)
            monitored_coins = session.execute(monitored_query).scalar() or 0

            return jsonify({
                'success': True,
                'status': {
                    'worker_running': True,  # TODO: Check actual worker status
                    'scheduler_running': True,  # TODO: Check actual scheduler status
                    'last_scan': last_scan.isoformat() if last_scan else None,
                    'active_signals': active_count,
                    'monitored_coins': monitored_coins,
                    'settings': settings.to_dict() if settings else None
                }
            }), 200

    except Exception as e:
        print(f"[AdminSurge] Get status error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_surge_bp.route('/api/admin/surge/restart', methods=['POST'])
@require_admin
def restart_surge_worker():
    """
    Restart surge worker and scheduler
    (실제 구현은 app.py에서 워커 재시작 로직 필요)

    Returns:
        {
            "success": true,
            "message": "Worker restart initiated"
        }
    """
    try:
        # TODO: Implement actual worker restart logic
        # This would require:
        # 1. Stop current worker/scheduler threads
        # 2. Reload settings from DB
        # 3. Start new worker/scheduler with updated settings

        return jsonify({
            'success': True,
            'message': 'Worker restart initiated (manual restart required for now)',
            'note': 'Please restart the application to apply new settings'
        }), 200

    except Exception as e:
        print(f"[AdminSurge] Restart error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_surge_bp.route('/api/admin/surge/test', methods=['POST'])
@require_admin
def test_surge_detection():
    """
    Test surge detection with current settings

    Request body:
        {
            "market": "KRW-BTC"  (optional, test specific coin)
        }

    Returns:
        {
            "success": true,
            "test_results": {
                "market": "KRW-BTC",
                "score": 75,
                "signals": {...},
                "recommendation": "..."
            }
        }
    """
    try:
        data = request.get_json() or {}
        test_market = data.get('market', 'KRW-BTC')

        # TODO: Implement test logic
        # 1. Get current settings
        # 2. Run surge predictor on test market
        # 3. Return analysis results

        return jsonify({
            'success': True,
            'message': 'Test feature coming soon',
            'test_market': test_market
        }), 200

    except Exception as e:
        print(f"[AdminSurge] Test error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
