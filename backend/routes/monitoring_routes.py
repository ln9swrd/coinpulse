# -*- coding: utf-8 -*-
"""
Monitoring Routes
System health and scheduler monitoring endpoints
"""

from flask import Blueprint, jsonify
from datetime import datetime, timedelta
from backend.database.connection import get_db_session
from backend.models.trading_signal import TradingSignal, SignalStatus, UserSignalHistory

monitoring_bp = Blueprint('monitoring', __name__)


@monitoring_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint

    Returns:
        {
            "status": "healthy",
            "timestamp": "2025-12-21T08:00:00",
            "uptime": "2h 15m"
        }
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'CoinPulse Signal Generation System'
    })


@monitoring_bp.route('/scheduler/status', methods=['GET'])
def scheduler_status():
    """
    Get scheduler status and next run times

    Returns:
        {
            "running": true,
            "jobs": [
                {
                    "id": "signal_generation",
                    "name": "Surge Analysis + Signal Generation",
                    "next_run": "2025-12-21T08:45:00"
                }
            ]
        }
    """
    try:
        from flask import current_app

        if not hasattr(current_app, 'signal_scheduler'):
            return jsonify({
                'success': False,
                'error': 'Scheduler not initialized'
            }), 500

        scheduler = current_app.signal_scheduler

        jobs = scheduler.get_jobs() if scheduler.is_running else []

        return jsonify({
            'success': True,
            'running': scheduler.is_running,
            'jobs': jobs,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@monitoring_bp.route('/signals/stats', methods=['GET'])
def signal_stats():
    """
    Get signal generation statistics

    Returns:
        {
            "total_signals": 150,
            "active_signals": 12,
            "expired_signals": 138,
            "total_distributions": 450,
            "total_executions": 89,
            "execution_rate": 19.78,
            "last_24h": {
                "signals_generated": 8,
                "users_notified": 45
            }
        }
    """
    try:
        session = get_db_session()

        # Total signals
        total_signals = session.query(TradingSignal).count()

        # Active signals (not expired, valid_until > now)
        active_signals = session.query(TradingSignal).filter(
            TradingSignal.status == SignalStatus.ACTIVE,
            TradingSignal.valid_until > datetime.utcnow()
        ).count()

        # Expired signals
        expired_signals = session.query(TradingSignal).filter(
            TradingSignal.status == SignalStatus.EXPIRED
        ).count()

        # Total distributions
        total_distributions = session.query(TradingSignal).with_entities(
            TradingSignal.distributed_to
        ).all()
        total_distributed = sum(d[0] for d in total_distributions)

        # Total executions
        total_executions = session.query(TradingSignal).with_entities(
            TradingSignal.executed_count
        ).all()
        total_executed = sum(e[0] for e in total_executions)

        # Execution rate
        execution_rate = (total_executed / total_distributed * 100) if total_distributed > 0 else 0

        # Last 24 hours stats
        last_24h_start = datetime.utcnow() - timedelta(hours=24)
        last_24h_signals = session.query(TradingSignal).filter(
            TradingSignal.created_at >= last_24h_start
        ).all()

        last_24h_count = len(last_24h_signals)
        last_24h_distributed = sum(s.distributed_to for s in last_24h_signals)

        session.close()

        return jsonify({
            'success': True,
            'total_signals': total_signals,
            'active_signals': active_signals,
            'expired_signals': expired_signals,
            'total_distributions': total_distributed,
            'total_executions': total_executed,
            'execution_rate': round(execution_rate, 2),
            'last_24h': {
                'signals_generated': last_24h_count,
                'users_notified': last_24h_distributed
            },
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@monitoring_bp.route('/signals/recent', methods=['GET'])
def recent_signals():
    """
    Get recent signals (last 20)

    Returns:
        {
            "signals": [
                {
                    "signal_id": "SIGNAL-20251221-001",
                    "market": "KRW-XRP",
                    "confidence": 85,
                    "entry_price": 650,
                    "target_price": 682,
                    "distributed_to": 15,
                    "executed_count": 3,
                    "status": "active",
                    "created_at": "2025-12-21T08:00:00"
                }
            ]
        }
    """
    try:
        session = get_db_session()

        signals = session.query(TradingSignal).order_by(
            TradingSignal.created_at.desc()
        ).limit(20).all()

        signal_list = []
        for signal in signals:
            signal_list.append({
                'signal_id': signal.signal_id,
                'market': signal.market,
                'confidence': signal.confidence,
                'entry_price': signal.entry_price,
                'target_price': signal.target_price,
                'stop_loss': signal.stop_loss,
                'distributed_to': signal.distributed_to,
                'executed_count': signal.executed_count,
                'execution_rate': signal.get_execution_rate(),
                'status': signal.status.value if signal.status else None,
                'created_at': signal.created_at.isoformat() if signal.created_at else None,
                'valid_until': signal.valid_until.isoformat() if signal.valid_until else None
            })

        session.close()

        return jsonify({
            'success': True,
            'signals': signal_list,
            'count': len(signal_list),
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@monitoring_bp.route('/signals/top-performers', methods=['GET'])
def top_performers():
    """
    Get top performing signals (by execution rate)

    Returns:
        {
            "signals": [
                {
                    "signal_id": "SIGNAL-20251220-001",
                    "market": "KRW-BTC",
                    "confidence": 90,
                    "execution_rate": 75.5
                }
            ]
        }
    """
    try:
        session = get_db_session()

        # Get signals with executions
        signals = session.query(TradingSignal).filter(
            TradingSignal.distributed_to > 0
        ).order_by(
            TradingSignal.created_at.desc()
        ).limit(50).all()

        # Sort by execution rate
        signals_sorted = sorted(
            signals,
            key=lambda s: s.get_execution_rate(),
            reverse=True
        )[:10]

        signal_list = []
        for signal in signals_sorted:
            signal_list.append({
                'signal_id': signal.signal_id,
                'market': signal.market,
                'confidence': signal.confidence,
                'entry_price': signal.entry_price,
                'distributed_to': signal.distributed_to,
                'executed_count': signal.executed_count,
                'execution_rate': round(signal.get_execution_rate(), 2),
                'created_at': signal.created_at.isoformat() if signal.created_at else None
            })

        session.close()

        return jsonify({
            'success': True,
            'signals': signal_list,
            'count': len(signal_list),
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
