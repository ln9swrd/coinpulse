"""
Balance History Routes Module

API endpoints for capturing and retrieving balance history snapshots.
"""

from flask import Blueprint, jsonify, request, g
import logging

from backend.middleware.auth_middleware import require_auth
from backend.middleware.user_api_keys import get_user_upbit_api
from backend.services.balance_history_service import BalanceHistoryService

# Create Blueprint
balance_history_bp = Blueprint('balance_history', __name__)

# Logger
logger = logging.getLogger(__name__)


@balance_history_bp.route('/api/balance/snapshot', methods=['POST'])
@require_auth
def capture_snapshot():
    """
    Capture current balance snapshot for the authenticated user.

    Returns:
        200: Snapshot captured successfully
        400: API keys not configured
        500: Error capturing snapshot
    """
    try:
        user_id = g.user_id

        # Get user's Upbit API instance
        user_upbit_api = get_user_upbit_api()

        if not user_upbit_api:
            return jsonify({
                'success': False,
                'error': 'Upbit API keys not configured',
                'code': 'NO_API_KEYS'
            }), 400

        # Create service and capture snapshot
        service = BalanceHistoryService(user_upbit_api)
        snapshot = service.capture_snapshot(user_id)

        if snapshot:
            return jsonify({
                'success': True,
                'message': 'Snapshot captured successfully',
                'snapshot': {
                    'timestamp': snapshot['snapshot_time'].isoformat(),
                    'krw_total': float(snapshot['krw_total']),
                    'krw_balance': float(snapshot['krw_balance']),
                    'total_value': float(snapshot['total_value']),
                    'crypto_value': float(snapshot['crypto_value']),
                    'total_purchase_amount': float(snapshot.get('total_purchase_amount', 0)),
                    'total_profit': float(snapshot['total_profit']),
                    'total_profit_rate': float(snapshot['total_profit_rate']),
                    'coin_count': snapshot['coin_count']
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to capture snapshot',
                'code': 'CAPTURE_FAILED'
            }), 500

    except Exception as e:
        logger.error(f"[BalanceHistory] Error in capture_snapshot: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500


@balance_history_bp.route('/api/balance/history', methods=['GET'])
@require_auth
def get_balance_history():
    """
    Get balance history for the authenticated user.

    Query params:
        days: Number of days to retrieve (default: 30, max: 90)
        grouped: If 'true', group by day (default: false)

    Returns:
        200: History retrieved successfully
        400: API keys not configured
        500: Error retrieving history
    """
    try:
        user_id = g.user_id

        # Get query parameters
        days = request.args.get('days', 30, type=int)
        grouped = request.args.get('grouped', 'false').lower() == 'true'

        # Limit days to max 90
        if days > 90:
            days = 90

        logger.info(f"[BalanceHistory] User {user_id}: Retrieving history (days={days}, grouped={grouped})")

        # Get user's Upbit API instance (for potential future use)
        user_upbit_api = get_user_upbit_api()

        # Create service and get history
        service = BalanceHistoryService(user_upbit_api)

        if grouped:
            history = service.get_daily_grouped_history(user_id, days)
        else:
            history = service.get_history(user_id, days)

        return jsonify({
            'success': True,
            'count': len(history),
            'days': days,
            'grouped': grouped,
            'history': history
        }), 200

    except Exception as e:
        logger.error(f"[BalanceHistory] Error in get_balance_history: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500


@balance_history_bp.route('/api/balance/current', methods=['GET'])
@require_auth
def get_current_balance_summary():
    """
    Get current balance summary (real-time snapshot without saving to DB).

    Returns:
        200: Current balance summary
        400: API keys not configured
        500: Error fetching balance
    """
    try:
        user_id = g.user_id

        # Get user's Upbit API instance
        user_upbit_api = get_user_upbit_api()

        if not user_upbit_api:
            return jsonify({
                'success': False,
                'error': 'Upbit API keys not configured',
                'code': 'NO_API_KEYS'
            }), 400

        # Get accounts from Upbit
        accounts = user_upbit_api.get_accounts()

        if not accounts:
            return jsonify({
                'success': True,
                'krw_total': 0,
                'krw_balance': 0,
                'total_value': 0,
                'total_purchase_amount': 0
            }), 200

        # Extract KRW data
        krw_account = next((acc for acc in accounts if acc['currency'] == 'KRW'), None)
        krw_balance = float(krw_account['balance']) if krw_account else 0
        krw_locked = float(krw_account['locked']) if krw_account else 0
        krw_total = krw_balance + krw_locked

        # Process crypto holdings
        crypto_accounts = [acc for acc in accounts if acc['currency'] != 'KRW'
                         and (float(acc['balance']) > 0 or float(acc['locked']) > 0)]

        if not crypto_accounts:
            return jsonify({
                'success': True,
                'krw_total': krw_total,
                'krw_balance': krw_balance,
                'total_value': krw_total,
                'total_purchase_amount': 0
            }), 200

        # Calculate crypto values
        total_purchase_amount = 0
        crypto_value = 0

        # Get current prices
        markets = [f'KRW-{acc["currency"]}' for acc in crypto_accounts]
        current_prices = user_upbit_api.get_current_prices(markets)

        for account in crypto_accounts:
            currency = account['currency']
            market = f'KRW-{currency}'
            balance = float(account['balance'])
            locked = float(account['locked'])
            amount = balance + locked
            avg_buy_price = float(account.get('avg_buy_price', 0))

            # Get current price
            price_info = current_prices.get(market, {})
            current_price = float(price_info.get('trade_price', 0))
            if current_price == 0:
                current_price = avg_buy_price

            # Calculations
            purchase_amount = amount * avg_buy_price
            current_value = amount * current_price

            total_purchase_amount += purchase_amount
            crypto_value += current_value

        total_value = krw_total + crypto_value

        return jsonify({
            'success': True,
            'krw_total': krw_total,
            'krw_balance': krw_balance,
            'total_value': total_value,
            'crypto_value': crypto_value,
            'total_purchase_amount': total_purchase_amount
        }), 200

    except Exception as e:
        logger.error(f"[BalanceHistory] Error in get_current_balance_summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500
