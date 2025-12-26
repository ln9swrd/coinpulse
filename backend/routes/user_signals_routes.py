# -*- coding: utf-8 -*-
"""
User Signals Routes
사용자 급등 신호 히스토리 API (surge_alerts 기반)
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime
from backend.database.connection import get_db_session
from sqlalchemy import text
from backend.middleware.auth_middleware import require_auth

user_signals_bp = Blueprint('user_signals', __name__)


@user_signals_bp.route('/api/user/signals', methods=['GET'])
@require_auth
def get_user_signals():
    """
    Get user's surge signal history from surge_alerts table

    Query params:
        status: filter by status (all, pending, win, lose, closed, expired)
        execution_status: filter by execution (all, not_executed, executed, failed)
        confidence_min: minimum confidence (0-100, default 0)
        limit: number of results (default 50, max 200)
        offset: pagination offset

    Returns:
        {
            "success": true,
            "signals": [
                {
                    "id": 1,
                    "signal": {
                        "market": "KRW-BTC",
                        "coin": "BTC",
                        "confidence": 0.75,
                        "entry_price": 50000000,
                        "target_price": 55000000,
                        "stop_loss_price": 47500000,
                        "expected_return": 10.0,
                        "reason": "Strong buy signal"
                    },
                    "received_at": "2025-12-21T...",
                    "status": "pending",
                    "profit_loss": null,
                    "profit_loss_percent": null,
                    "exit_price": null,
                    "peak_price": null,
                    "close_reason": null
                }
            ],
            "count": 10,
            "has_more": true
        }
    """
    try:
        user_id = g.user_id
        status_filter = request.args.get('status', 'all')
        execution_filter = request.args.get('execution_status', 'all')
        confidence_min = max(0, min(100, int(request.args.get('confidence_min', 0))))
        limit = min(200, max(1, int(request.args.get('limit', 50))))
        offset = max(0, int(request.args.get('offset', 0)))

        with get_db_session() as session:
            # Build WHERE clause
            where_clauses = ["user_id = :user_id"]
            params = {'user_id': user_id, 'limit': limit, 'offset': offset}

            # Apply status filter
            if status_filter != 'all':
                where_clauses.append("status = :status")
                params['status'] = status_filter

            # Apply execution status filter
            if execution_filter == 'not_executed':
                where_clauses.append("(auto_traded IS NULL OR auto_traded = false)")
            elif execution_filter == 'executed':
                where_clauses.append("auto_traded = true")
            elif execution_filter == 'failed':
                # Failed = executed but resulted in loss
                where_clauses.append("auto_traded = true AND exit_price IS NOT NULL AND exit_price <= entry_price")

            # Apply confidence filter
            if confidence_min > 0:
                where_clauses.append("confidence >= :confidence_min")
                params['confidence_min'] = confidence_min

            where_sql = " AND ".join(where_clauses)

            # Get total count
            count_query = f"SELECT COUNT(*) FROM surge_alerts WHERE {where_sql}"
            total_count = session.execute(text(count_query), params).scalar()

            # Get paginated results
            data_query = f"""
                SELECT
                    id, market, coin, confidence,
                    entry_price, target_price, stop_loss_price, expected_return,
                    current_price, peak_price, exit_price,
                    reason, alert_message,
                    sent_at, status,
                    profit_loss, profit_loss_percent,
                    close_reason, closed_at,
                    auto_traded, trade_amount, order_id
                FROM surge_alerts
                WHERE {where_sql}
                ORDER BY sent_at DESC
                LIMIT :limit OFFSET :offset
            """

            result = session.execute(text(data_query), params)

            # Build signals list
            signals_list = []
            for row in result:
                row_dict = dict(row._mapping)

                signals_list.append({
                    'id': row_dict['id'],
                    'signal': {
                        'market': row_dict['market'],
                        'coin': row_dict['coin'],
                        'confidence': float(row_dict['confidence']) if row_dict['confidence'] else 0,
                        'entry_price': row_dict['entry_price'],
                        'target_price': row_dict['target_price'],
                        'stop_loss_price': row_dict['stop_loss_price'],
                        'expected_return': float(row_dict['expected_return']) if row_dict['expected_return'] else 0,
                        'reason': row_dict['reason'],
                        'alert_message': row_dict['alert_message']
                    },
                    'received_at': row_dict['sent_at'].isoformat() if row_dict['sent_at'] else None,
                    'status': row_dict['status'],
                    'current_price': row_dict['current_price'],
                    'peak_price': row_dict['peak_price'],
                    'exit_price': row_dict['exit_price'],
                    'profit_loss': row_dict['profit_loss'],
                    'profit_loss_percent': float(row_dict['profit_loss_percent']) if row_dict['profit_loss_percent'] else None,
                    'close_reason': row_dict['close_reason'],
                    'closed_at': row_dict['closed_at'].isoformat() if row_dict['closed_at'] else None,
                    'auto_traded': row_dict['auto_traded'],
                    'trade_amount': row_dict['trade_amount'],
                    'order_id': row_dict['order_id'],
                    'execution_status': 'executed' if row_dict['auto_traded'] else 'not_executed',
                    'is_expired': row_dict['status'] in ['expired', 'closed']
                })

            has_more = (offset + limit) < total_count

            return jsonify({
                'success': True,
                'signals': signals_list,
                'count': total_count,
                'has_more': has_more
            }), 200

    except Exception as e:
        print(f"[UserSignals] Error: {e}")
        import traceback
        traceback.print_exc()
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
            "success": true,
            "stats": {
                "total_received": 100,
                "executed": 50,
                "execution_rate": 50.0,
                "win_rate": 60.0,
                "total_profit_loss": 1000000,
                "this_month": 5
            }
        }
    """
    try:
        user_id = g.user_id

        with get_db_session() as session:
            # Get statistics
            # Calculate wins/losses based on actual exit_price vs entry_price
            # NOTE: exit_price <= entry_price is considered a loss (due to trading fees ~0.1%)
            stats_query = text("""
                SELECT
                    COUNT(*) as total_received,
                    COUNT(CASE WHEN auto_traded = true THEN 1 END) as executed,
                    COUNT(CASE WHEN exit_price IS NOT NULL AND exit_price > entry_price THEN 1 END) as wins,
                    COUNT(CASE WHEN exit_price IS NOT NULL AND exit_price <= entry_price THEN 1 END) as losses,
                    SUM(COALESCE(profit_loss, 0)) as total_profit_loss,
                    COUNT(CASE WHEN sent_at >= DATE_TRUNC('month', CURRENT_DATE) THEN 1 END) as this_month
                FROM surge_alerts
                WHERE user_id = :user_id
            """)

            result = session.execute(stats_query, {'user_id': user_id}).fetchone()

            total_received = result[0] or 0
            executed = result[1] or 0
            wins = result[2] or 0
            losses = result[3] or 0
            total_profit_loss = result[4] or 0
            this_month = result[5] or 0

            execution_rate = (executed / total_received * 100) if total_received > 0 else 0
            win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

            return jsonify({
                'success': True,
                'stats': {
                    'total_received': total_received,
                    'executed': executed,
                    'execution_rate': round(execution_rate, 1),
                    'wins': wins,
                    'losses': losses,
                    'win_rate': round(win_rate, 1),
                    'total_profit_loss': int(total_profit_loss),
                    'this_month': this_month
                }
            }), 200

    except Exception as e:
        print(f"[UserSignals] Stats error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_signals_bp.route('/api/user/signals/<int:signal_id>/execute', methods=['POST'])
@require_auth
def execute_signal(signal_id):
    """
    Execute a signal by placing a market buy order

    Request Body (optional):
        {
            "trade_amount": 50000  // Amount in KRW (default: 50000)
        }

    Returns:
        {
            "success": true,
            "message": "Order executed successfully",
            "order": {
                "uuid": "...",
                "market": "KRW-BTC",
                "side": "bid",
                "ord_type": "market",
                "price": "50000",
                "executed_volume": "0.0012"
            },
            "execution_price": 41666667
        }
    """
    try:
        user_id = g.user_id

        # Get user's Upbit API
        from backend.middleware.user_api_keys import get_user_upbit_api
        user_upbit_api = get_user_upbit_api()

        if not user_upbit_api:
            return jsonify({
                'success': False,
                'error': 'Upbit API keys not configured. Please add your API keys in Settings.',
                'error_code': 'NO_API_KEYS'
            }), 400

        with get_db_session() as session:
            # Get signal details
            signal_query = text("""
                SELECT id, market, coin, entry_price, auto_traded
                FROM surge_alerts
                WHERE id = :signal_id AND user_id = :user_id
            """)

            signal = session.execute(signal_query, {
                'signal_id': signal_id,
                'user_id': user_id
            }).fetchone()

            if not signal:
                return jsonify({
                    'success': False,
                    'error': 'Signal not found or access denied'
                }), 404

            # Check if already executed
            if signal.auto_traded:
                return jsonify({
                    'success': False,
                    'error': 'Signal has already been executed'
                }), 400

            # Get trade amount from request or use default
            request_data = request.get_json() or {}
            trade_amount = request_data.get('trade_amount', 50000)  # Default: 50,000 KRW

            # Validate trade amount
            if trade_amount < 5000:
                return jsonify({
                    'success': False,
                    'error': 'Minimum trade amount is 5,000 KRW'
                }), 400

            print(f"[UserSignals] Executing signal {signal_id}: market={signal.market}, amount={trade_amount} KRW")

            # Place market buy order
            order_result = user_upbit_api.place_order(
                market=signal.market,
                side='bid',  # Buy
                price=trade_amount,  # Total amount to spend in KRW
                ord_type='market'
            )

            if not order_result.get('success'):
                error_msg = order_result.get('error', 'Unknown error')
                print(f"[UserSignals] Order failed: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': f'Failed to place order: {error_msg}'
                }), 400

            # Extract order details
            order_data = order_result.get('order', {})
            order_uuid = order_result.get('uuid')
            executed_volume = float(order_data.get('executed_volume', 0))
            avg_price = float(order_data.get('avg_price', 0)) if order_data.get('avg_price') else None

            print(f"[UserSignals] Order success: uuid={order_uuid}, volume={executed_volume}, price={avg_price}")

            # Update surge_alerts with execution details
            update_query = text("""
                UPDATE surge_alerts
                SET auto_traded = true,
                    executed_at = CURRENT_TIMESTAMP,
                    trade_amount = :trade_amount,
                    trade_quantity = :trade_quantity,
                    order_id = :order_id,
                    status = 'executed'
                WHERE id = :signal_id
            """)

            session.execute(update_query, {
                'signal_id': signal_id,
                'trade_amount': trade_amount,
                'trade_quantity': executed_volume,
                'order_id': order_uuid
            })
            session.commit()

            return jsonify({
                'success': True,
                'message': 'Order executed successfully',
                'order': {
                    'uuid': order_uuid,
                    'market': signal.market,
                    'side': 'bid',
                    'ord_type': 'market',
                    'price': str(trade_amount),
                    'executed_volume': str(executed_volume)
                },
                'execution_price': avg_price,
                'trade_amount': trade_amount
            }), 200

    except Exception as e:
        print(f"[UserSignals] Execute error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
