# -*- coding: utf-8 -*-
"""
User Signals Routes
사용자 시그널 히스토리 및 관리 API
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime, timedelta
from backend.database.connection import get_db_session
from backend.models.trading_signal import TradingSignal, UserSignalHistory, ExecutionStatus, SignalStatus
from backend.middleware.auth_middleware import require_auth

user_signals_bp = Blueprint('user_signals', __name__)


@user_signals_bp.route('/api/user/signals', methods=['GET'])
@require_auth
def get_user_signals():
    """
    Get user's signal history

    Query params:
        status: filter by execution status (all, not_executed, executed, failed)
        limit: number of results (default 50)
        offset: pagination offset

    Returns:
        {
            "signals": [
                {
                    "id": 1,
                    "signal": {...},
                    "received_at": "2025-12-21T...",
                    "is_bonus": false,
                    "execution_status": "not_executed",
                    "executed_at": null,
                    "profit_loss": null
                }
            ],
            "count": 10,
            "has_more": true
        }
    """
    try:
        user_id = g.user_id
        status_filter = request.args.get('status', 'all')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        session = get_db_session()

        # Base query
        query = session.query(UserSignalHistory).filter(
            UserSignalHistory.user_id == user_id
        )

        # Apply status filter
        if status_filter != 'all':
            if status_filter == 'not_executed':
                query = query.filter(UserSignalHistory.execution_status == ExecutionStatus.NOT_EXECUTED)
            elif status_filter == 'executed':
                query = query.filter(UserSignalHistory.execution_status == ExecutionStatus.EXECUTED)
            elif status_filter == 'failed':
                query = query.filter(UserSignalHistory.execution_status == ExecutionStatus.FAILED)
            elif status_filter == 'pending':
                query = query.filter(UserSignalHistory.execution_status == ExecutionStatus.PENDING)

        # Get total count
        total_count = query.count()

        # Get paginated results
        histories = query.order_by(
            UserSignalHistory.received_at.desc()
        ).limit(limit).offset(offset).all()

        # Build response
        signals_list = []
        for history in histories:
            # Get signal details
            signal = session.query(TradingSignal).filter(
                TradingSignal.id == history.signal_id
            ).first()

            if signal:
                signals_list.append({
                    'id': history.id,
                    'signal': {
                        'signal_id': signal.signal_id,
                        'market': signal.market,
                        'confidence': signal.confidence,
                        'entry_price': signal.entry_price,
                        'target_price': signal.target_price,
                        'stop_loss': signal.stop_loss,
                        'expected_return': signal.get_expected_return(),
                        'reason': signal.reason,
                        'created_at': signal.created_at.isoformat() if signal.created_at else None,
                        'valid_until': signal.valid_until.isoformat() if signal.valid_until else None,
                        'is_expired': signal.is_expired()
                    },
                    'received_at': history.received_at.isoformat() if history.received_at else None,
                    'is_bonus': history.is_bonus,
                    'execution_status': history.execution_status.value if history.execution_status else None,
                    'executed_at': history.executed_at.isoformat() if history.executed_at else None,
                    'order_id': history.order_id,
                    'execution_price': history.execution_price,
                    'result_status': history.result_status,
                    'profit_loss': history.profit_loss,
                    'profit_loss_ratio': history.profit_loss_ratio,
                    'notes': history.notes
                })

        session.close()

        has_more = (offset + limit) < total_count

        return jsonify({
            'success': True,
            'signals': signals_list,
            'count': len(signals_list),
            'total': total_count,
            'has_more': has_more,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_signals_bp.route('/api/user/signals/stats', methods=['GET'])
@require_auth
def get_user_signal_stats():
    """
    Get user's signal statistics

    Returns:
        {
            "total_received": 25,
            "executed": 12,
            "not_executed": 13,
            "execution_rate": 48.0,
            "total_profit_loss": 150000,
            "win_count": 9,
            "loss_count": 3,
            "win_rate": 75.0,
            "this_month": {
                "received": 8,
                "executed": 4
            }
        }
    """
    try:
        user_id = g.user_id
        session = get_db_session()

        # Total received
        total_received = session.query(UserSignalHistory).filter(
            UserSignalHistory.user_id == user_id
        ).count()

        # Executed count
        executed_count = session.query(UserSignalHistory).filter(
            UserSignalHistory.user_id == user_id,
            UserSignalHistory.execution_status == ExecutionStatus.EXECUTED
        ).count()

        # Not executed count
        not_executed_count = session.query(UserSignalHistory).filter(
            UserSignalHistory.user_id == user_id,
            UserSignalHistory.execution_status == ExecutionStatus.NOT_EXECUTED
        ).count()

        # Execution rate
        execution_rate = (executed_count / total_received * 100) if total_received > 0 else 0

        # Profit/loss stats
        executed_signals = session.query(UserSignalHistory).filter(
            UserSignalHistory.user_id == user_id,
            UserSignalHistory.execution_status == ExecutionStatus.EXECUTED,
            UserSignalHistory.profit_loss.isnot(None)
        ).all()

        total_profit_loss = sum(s.profit_loss for s in executed_signals if s.profit_loss)
        win_count = sum(1 for s in executed_signals if s.profit_loss and s.profit_loss > 0)
        loss_count = sum(1 for s in executed_signals if s.profit_loss and s.profit_loss < 0)
        win_rate = (win_count / len(executed_signals) * 100) if executed_signals else 0

        # This month stats
        month_start = datetime(datetime.utcnow().year, datetime.utcnow().month, 1)
        this_month_received = session.query(UserSignalHistory).filter(
            UserSignalHistory.user_id == user_id,
            UserSignalHistory.received_at >= month_start
        ).count()

        this_month_executed = session.query(UserSignalHistory).filter(
            UserSignalHistory.user_id == user_id,
            UserSignalHistory.received_at >= month_start,
            UserSignalHistory.execution_status == ExecutionStatus.EXECUTED
        ).count()

        session.close()

        return jsonify({
            'success': True,
            'total_received': total_received,
            'executed': executed_count,
            'not_executed': not_executed_count,
            'execution_rate': round(execution_rate, 2),
            'total_profit_loss': total_profit_loss,
            'win_count': win_count,
            'loss_count': loss_count,
            'win_rate': round(win_rate, 2),
            'this_month': {
                'received': this_month_received,
                'executed': this_month_executed
            },
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_signals_bp.route('/api/user/signals/<int:history_id>/execute', methods=['POST'])
@require_auth
def execute_signal(history_id):
    """
    Execute a trading signal (simulate order placement).

    Request body:
        {
            "execution_price": 650.0,
            "notes": "Manual execution"
        }

    Returns:
        {
            "success": true,
            "message": "Signal executed successfully",
            "history": {...}
        }
    """
    try:
        user_id = g.user_id
        data = request.json or {}

        session = get_db_session()

        # Get the signal history
        history = session.query(UserSignalHistory).filter(
            UserSignalHistory.id == history_id,
            UserSignalHistory.user_id == user_id
        ).first()

        if not history:
            session.close()
            return jsonify({
                'success': False,
                'error': 'Signal not found'
            }), 404

        # Check if already executed
        if history.execution_status == ExecutionStatus.EXECUTED:
            session.close()
            return jsonify({
                'success': False,
                'error': 'Signal already executed'
            }), 400

        # Check if signal is expired
        signal = session.query(TradingSignal).filter(
            TradingSignal.id == history.signal_id
        ).first()

        if signal and signal.is_expired():
            session.close()
            return jsonify({
                'success': False,
                'error': 'Signal has expired'
            }), 400

        # Execute the signal
        execution_price = data.get('execution_price', signal.entry_price if signal else 0)
        notes = data.get('notes', 'Manual execution from web UI')

        history.execution_status = ExecutionStatus.EXECUTED
        history.executed_at = datetime.utcnow()
        history.execution_price = execution_price
        history.notes = notes

        # Update signal executed count
        if signal:
            signal.executed_count += 1

        session.commit()
        session.close()

        return jsonify({
            'success': True,
            'message': 'Signal executed successfully',
            'history': {
                'id': history.id,
                'execution_status': history.execution_status.value,
                'executed_at': history.executed_at.isoformat() if history.executed_at else None,
                'execution_price': history.execution_price,
                'notes': history.notes
            },
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_signals_bp.route('/api/user/signals/<int:history_id>/close', methods=['POST'])
@require_auth
def close_signal_position(history_id):
    """
    Close a signal position and record profit/loss.

    Request body:
        {
            "close_price": 682.0,
            "close_reason": "target_reached",
            "notes": "Target price reached"
        }

    Returns:
        {
            "success": true,
            "message": "Position closed successfully",
            "profit_loss": 150000,
            "profit_loss_ratio": 4.92
        }
    """
    try:
        user_id = g.user_id
        data = request.json or {}

        close_price = data.get('close_price')
        close_reason = data.get('close_reason', 'manual')
        notes = data.get('notes', '')

        if not close_price:
            return jsonify({
                'success': False,
                'error': 'close_price is required'
            }), 400

        session = get_db_session()

        # Get the signal history
        history = session.query(UserSignalHistory).filter(
            UserSignalHistory.id == history_id,
            UserSignalHistory.user_id == user_id
        ).first()

        if not history:
            session.close()
            return jsonify({
                'success': False,
                'error': 'Signal not found'
            }), 404

        # Check if executed
        if history.execution_status != ExecutionStatus.EXECUTED:
            session.close()
            return jsonify({
                'success': False,
                'error': 'Signal not executed yet'
            }), 400

        # Calculate profit/loss
        execution_price = history.execution_price or 0
        profit_loss_ratio = ((close_price - execution_price) / execution_price * 100) if execution_price > 0 else 0

        # Assume 10,000 KRW investment per signal
        investment_amount = 10000
        profit_loss = investment_amount * (profit_loss_ratio / 100)

        # Update history
        history.result_status = close_reason
        history.profit_loss = profit_loss
        history.profit_loss_ratio = profit_loss_ratio
        history.notes = (history.notes or '') + f'\n{notes}' if notes else history.notes

        session.commit()
        session.close()

        return jsonify({
            'success': True,
            'message': 'Position closed successfully',
            'profit_loss': profit_loss,
            'profit_loss_ratio': profit_loss_ratio,
            'close_reason': close_reason,
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_signals_bp.route('/api/user/signals/<int:history_id>/performance', methods=['GET'])
@require_auth
def get_signal_performance(history_id):
    """
    Get real-time performance of an executed signal.

    Returns:
        {
            "success": true,
            "signal": {
                "market": "KRW-XRP",
                "execution_price": 650,
                "current_price": 670,
                "target_price": 682,
                "stop_loss": 637
            },
            "performance": {
                "profit_loss": 200000,
                "profit_loss_ratio": 3.08,
                "status": "in_profit",
                "target_progress": 62.5
            }
        }
    """
    try:
        user_id = g.user_id
        session = get_db_session()

        # Get the signal history
        history = session.query(UserSignalHistory).filter(
            UserSignalHistory.id == history_id,
            UserSignalHistory.user_id == user_id
        ).first()

        if not history:
            session.close()
            return jsonify({
                'success': False,
                'error': 'Signal not found'
            }), 404

        if history.execution_status != ExecutionStatus.EXECUTED:
            session.close()
            return jsonify({
                'success': False,
                'error': 'Signal not executed yet'
            }), 400

        # Get signal details
        signal = session.query(TradingSignal).filter(
            TradingSignal.id == history.signal_id
        ).first()

        if not signal:
            session.close()
            return jsonify({
                'success': False,
                'error': 'Signal data not found'
            }), 404

        # Get current price from Upbit API
        try:
            from backend.common.upbit_api import UpbitAPI
            upbit = UpbitAPI()
            current_prices = upbit.get_current_prices([signal.market])
            current_price = current_prices.get(signal.market, {}).get('trade_price', 0)
        except Exception as e:
            print(f"[Performance] Failed to get current price: {e}")
            current_price = history.execution_price or signal.entry_price

        # Calculate performance
        execution_price = history.execution_price or signal.entry_price
        profit_loss_ratio = ((current_price - execution_price) / execution_price * 100) if execution_price > 0 else 0

        investment_amount = 10000
        profit_loss = investment_amount * (profit_loss_ratio / 100)

        # Calculate target progress
        target_diff = signal.target_price - execution_price
        current_diff = current_price - execution_price
        target_progress = (current_diff / target_diff * 100) if target_diff > 0 else 0

        # Determine status
        if current_price >= signal.target_price:
            status = 'target_reached'
        elif current_price <= signal.stop_loss:
            status = 'stop_loss_hit'
        elif profit_loss_ratio > 0:
            status = 'in_profit'
        else:
            status = 'in_loss'

        session.close()

        return jsonify({
            'success': True,
            'signal': {
                'market': signal.market,
                'execution_price': execution_price,
                'current_price': current_price,
                'target_price': signal.target_price,
                'stop_loss': signal.stop_loss
            },
            'performance': {
                'profit_loss': profit_loss,
                'profit_loss_ratio': profit_loss_ratio,
                'status': status,
                'target_progress': target_progress
            },
            'timestamp': datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
