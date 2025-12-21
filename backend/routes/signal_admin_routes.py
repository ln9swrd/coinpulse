# -*- coding: utf-8 -*-
"""
Signal Admin Routes
Admin panel API endpoints for signal management
"""

from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from backend.database.connection import get_db_session
from backend.models.trading_signal import TradingSignal, UserSignalHistory, ExecutionStatus, SignalStatus
from backend.database.models import User
from backend.middleware.security import token_required, admin_required
from sqlalchemy import func, desc

signal_admin_bp = Blueprint('signal_admin', __name__)


@signal_admin_bp.route('/api/admin/signals', methods=['GET'])
@token_required
@admin_required
def get_all_signals(current_user):
    """
    Get all signals with filtering and pagination (admin only).

    Query params:
        status: filter by status (all, active, expired)
        limit: number of results (default 50)
        offset: pagination offset

    Returns:
        {
            "success": true,
            "signals": [...],
            "count": 50,
            "total": 150
        }
    """
    try:
        status_filter = request.args.get('status', 'all')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        session = get_db_session()

        # Base query
        query = session.query(TradingSignal)

        # Apply status filter
        if status_filter == 'active':
            query = query.filter(
                TradingSignal.status == SignalStatus.ACTIVE,
                TradingSignal.valid_until > datetime.utcnow()
            )
        elif status_filter == 'expired':
            query = query.filter(TradingSignal.status == SignalStatus.EXPIRED)

        # Get total count
        total_count = query.count()

        # Get paginated results
        signals = query.order_by(desc(TradingSignal.created_at)).limit(limit).offset(offset).all()

        # Build response
        signals_list = []
        for signal in signals:
            signals_list.append({
                'id': signal.id,
                'signal_id': signal.signal_id,
                'market': signal.market,
                'confidence': signal.confidence,
                'entry_price': signal.entry_price,
                'target_price': signal.target_price,
                'stop_loss': signal.stop_loss,
                'expected_return': signal.get_expected_return(),
                'distributed_to': signal.distributed_to,
                'executed_count': signal.executed_count,
                'execution_rate': signal.get_execution_rate(),
                'status': signal.status.value if signal.status else None,
                'created_at': signal.created_at.isoformat() if signal.created_at else None,
                'valid_until': signal.valid_until.isoformat() if signal.valid_until else None,
                'is_expired': signal.is_expired()
            })

        session.close()

        return jsonify({
            'success': True,
            'signals': signals_list,
            'count': len(signals_list),
            'total': total_count,
            'has_more': (offset + limit) < total_count,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@signal_admin_bp.route('/api/admin/signals/<int:signal_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_signal(current_user, signal_id):
    """
    Delete a signal and its user history (admin only).

    Returns:
        {
            "success": true,
            "message": "Signal deleted successfully"
        }
    """
    try:
        session = get_db_session()

        signal = session.query(TradingSignal).filter(TradingSignal.id == signal_id).first()

        if not signal:
            session.close()
            return jsonify({
                'success': False,
                'error': 'Signal not found'
            }), 404

        # Delete user history first (foreign key constraint)
        session.query(UserSignalHistory).filter(
            UserSignalHistory.signal_id == signal_id
        ).delete()

        # Delete signal
        session.delete(signal)
        session.commit()
        session.close()

        return jsonify({
            'success': True,
            'message': 'Signal deleted successfully',
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@signal_admin_bp.route('/api/admin/signals/users', methods=['GET'])
@token_required
@admin_required
def get_user_signal_stats(current_user):
    """
    Get signal statistics by user (admin only).

    Returns:
        {
            "success": true,
            "users": [
                {
                    "user_id": 1,
                    "username": "user@example.com",
                    "total_received": 25,
                    "executed": 12,
                    "execution_rate": 48.0
                }
            ]
        }
    """
    try:
        session = get_db_session()

        # Get all users with signal history
        user_stats = session.query(
            UserSignalHistory.user_id,
            func.count(UserSignalHistory.id).label('total_received'),
            func.sum(
                func.case(
                    (UserSignalHistory.execution_status == ExecutionStatus.EXECUTED, 1),
                    else_=0
                )
            ).label('executed')
        ).group_by(UserSignalHistory.user_id).all()

        # Build response with user details
        users_list = []
        for stat in user_stats:
            user = session.query(User).filter(User.id == stat.user_id).first()

            execution_rate = (stat.executed / stat.total_received * 100) if stat.total_received > 0 else 0

            users_list.append({
                'user_id': stat.user_id,
                'username': user.username if user else 'Unknown',
                'email': user.email if user else 'Unknown',
                'total_received': stat.total_received,
                'executed': stat.executed,
                'execution_rate': round(execution_rate, 2)
            })

        # Sort by total received
        users_list.sort(key=lambda x: x['total_received'], reverse=True)

        session.close()

        return jsonify({
            'success': True,
            'users': users_list,
            'count': len(users_list),
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@signal_admin_bp.route('/api/admin/signals/scheduler/status', methods=['GET'])
@token_required
@admin_required
def get_scheduler_status(current_user):
    """
    Get signal scheduler status (admin only).

    Returns:
        {
            "success": true,
            "running": true,
            "jobs": [...]
        }
    """
    try:
        if not hasattr(current_app, 'signal_scheduler'):
            return jsonify({
                'success': False,
                'error': 'Signal scheduler not initialized'
            }), 500

        scheduler = current_app.signal_scheduler

        return jsonify({
            'success': True,
            'running': scheduler.is_running,
            'jobs': scheduler.get_jobs() if scheduler.is_running else [],
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@signal_admin_bp.route('/api/admin/signals/scheduler/start', methods=['POST'])
@token_required
@admin_required
def start_scheduler(current_user):
    """
    Start signal scheduler (admin only).

    Returns:
        {
            "success": true,
            "message": "Scheduler started successfully"
        }
    """
    try:
        if not hasattr(current_app, 'signal_scheduler'):
            return jsonify({
                'success': False,
                'error': 'Signal scheduler not initialized'
            }), 500

        scheduler = current_app.signal_scheduler

        if scheduler.is_running:
            return jsonify({
                'success': False,
                'error': 'Scheduler is already running'
            }), 400

        scheduler.start()

        return jsonify({
            'success': True,
            'message': 'Scheduler started successfully',
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@signal_admin_bp.route('/api/admin/signals/scheduler/stop', methods=['POST'])
@token_required
@admin_required
def stop_scheduler(current_user):
    """
    Stop signal scheduler (admin only).

    Returns:
        {
            "success": true,
            "message": "Scheduler stopped successfully"
        }
    """
    try:
        if not hasattr(current_app, 'signal_scheduler'):
            return jsonify({
                'success': False,
                'error': 'Signal scheduler not initialized'
            }), 500

        scheduler = current_app.signal_scheduler

        if not scheduler.is_running:
            return jsonify({
                'success': False,
                'error': 'Scheduler is not running'
            }), 400

        scheduler.stop()

        return jsonify({
            'success': True,
            'message': 'Scheduler stopped successfully',
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@signal_admin_bp.route('/api/admin/signals/create', methods=['POST'])
@token_required
@admin_required
def create_manual_signal(current_user):
    """
    Create a manual signal (admin only).

    Request body:
        {
            "market": "KRW-XRP",
            "confidence": 85,
            "entry_price": 650,
            "target_price": 682,
            "stop_loss": 637,
            "reason": "Manual signal for testing",
            "valid_hours": 4
        }

    Returns:
        {
            "success": true,
            "signal": {...}
        }
    """
    try:
        data = request.json

        required_fields = ['market', 'confidence', 'entry_price', 'target_price', 'stop_loss', 'reason']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        session = get_db_session()

        # Generate signal ID
        signal_id = f"MANUAL-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        # Create signal
        valid_hours = data.get('valid_hours', 4)
        valid_until = datetime.utcnow() + timedelta(hours=valid_hours)

        signal = TradingSignal(
            signal_id=signal_id,
            market=data['market'],
            confidence=data['confidence'],
            entry_price=data['entry_price'],
            target_price=data['target_price'],
            stop_loss=data['stop_loss'],
            expected_return=((data['target_price'] - data['entry_price']) / data['entry_price'] * 100),
            reason=data['reason'],
            status=SignalStatus.ACTIVE,
            created_at=datetime.utcnow(),
            valid_until=valid_until,
            distributed_to=0,
            executed_count=0
        )

        session.add(signal)
        session.commit()

        signal_dict = {
            'id': signal.id,
            'signal_id': signal.signal_id,
            'market': signal.market,
            'confidence': signal.confidence,
            'entry_price': signal.entry_price,
            'target_price': signal.target_price,
            'stop_loss': signal.stop_loss,
            'expected_return': signal.expected_return,
            'reason': signal.reason,
            'created_at': signal.created_at.isoformat(),
            'valid_until': signal.valid_until.isoformat()
        }

        session.close()

        return jsonify({
            'success': True,
            'message': 'Signal created successfully',
            'signal': signal_dict,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@signal_admin_bp.route('/api/admin/signals/stats', methods=['GET'])
@token_required
@admin_required
def get_admin_stats(current_user):
    """
    Get comprehensive admin statistics (admin only).

    Returns:
        {
            "success": true,
            "stats": {
                "total_signals": 150,
                "active_signals": 12,
                "total_users": 25,
                "total_distributions": 450,
                "total_executions": 89,
                "overall_execution_rate": 19.78
            }
        }
    """
    try:
        session = get_db_session()

        # Total signals
        total_signals = session.query(TradingSignal).count()

        # Active signals
        active_signals = session.query(TradingSignal).filter(
            TradingSignal.status == SignalStatus.ACTIVE,
            TradingSignal.valid_until > datetime.utcnow()
        ).count()

        # Total users with signals
        total_users = session.query(UserSignalHistory.user_id).distinct().count()

        # Total distributions
        total_distributions = session.query(
            func.sum(TradingSignal.distributed_to)
        ).scalar() or 0

        # Total executions
        total_executions = session.query(
            func.sum(TradingSignal.executed_count)
        ).scalar() or 0

        # Overall execution rate
        overall_execution_rate = (total_executions / total_distributions * 100) if total_distributions > 0 else 0

        # Last 24 hours
        last_24h = datetime.utcnow() - timedelta(hours=24)
        last_24h_signals = session.query(TradingSignal).filter(
            TradingSignal.created_at >= last_24h
        ).count()

        session.close()

        return jsonify({
            'success': True,
            'stats': {
                'total_signals': total_signals,
                'active_signals': active_signals,
                'total_users': total_users,
                'total_distributions': total_distributions,
                'total_executions': total_executions,
                'overall_execution_rate': round(overall_execution_rate, 2),
                'last_24h_signals': last_24h_signals
            },
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
