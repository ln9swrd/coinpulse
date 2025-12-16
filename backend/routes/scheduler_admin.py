"""
Scheduler Admin API

Administrative endpoints for managing subscription renewal scheduler.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime

scheduler_admin_bp = Blueprint('scheduler_admin', __name__)


@scheduler_admin_bp.route('/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """
    Get scheduler status.

    Returns:
        JSON: Scheduler running status and next run time
    """
    try:
        from backend.services.subscription_scheduler import get_scheduler
        import schedule

        scheduler = get_scheduler()

        # Get scheduled jobs
        jobs = schedule.get_jobs()
        next_run = jobs[0].next_run if jobs else None

        return jsonify({
            'success': True,
            'status': {
                'running': scheduler.running,
                'jobs_count': len(jobs),
                'next_run': next_run.isoformat() if next_run else None,
                'current_time': datetime.now().isoformat()
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scheduler_admin_bp.route('/scheduler/trigger', methods=['POST'])
def trigger_scheduler_manually():
    """
    Manually trigger subscription renewal check.

    Admin only endpoint.

    Returns:
        JSON: Success status
    """
    try:
        from backend.services.subscription_scheduler import get_scheduler

        scheduler = get_scheduler()
        scheduler.check_expiring_subscriptions()

        return jsonify({
            'success': True,
            'message': 'Subscription renewal check triggered successfully',
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scheduler_admin_bp.route('/scheduler/start', methods=['POST'])
def start_scheduler_endpoint():
    """
    Start the scheduler (if stopped).

    Admin only endpoint.

    Returns:
        JSON: Success status
    """
    try:
        from backend.services.subscription_scheduler import get_scheduler

        scheduler = get_scheduler()

        if scheduler.running:
            return jsonify({
                'success': False,
                'message': 'Scheduler is already running'
            }), 400

        scheduler.start()

        return jsonify({
            'success': True,
            'message': 'Scheduler started successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@scheduler_admin_bp.route('/scheduler/stop', methods=['POST'])
def stop_scheduler_endpoint():
    """
    Stop the scheduler.

    Admin only endpoint.

    Returns:
        JSON: Success status
    """
    try:
        from backend.services.subscription_scheduler import get_scheduler

        scheduler = get_scheduler()

        if not scheduler.running:
            return jsonify({
                'success': False,
                'message': 'Scheduler is not running'
            }), 400

        scheduler.stop()

        return jsonify({
            'success': True,
            'message': 'Scheduler stopped successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
