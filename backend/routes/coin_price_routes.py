"""
Coin Price History Routes Module

API endpoints for retrieving shared coin price history (BTC/ETH/XRP).
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime, timedelta

from backend.database.connection import get_db_session
from sqlalchemy import text

# Create Blueprint
coin_price_bp = Blueprint('coin_price', __name__)

# Logger
logger = logging.getLogger(__name__)


@coin_price_bp.route('/api/coin-prices/history', methods=['GET'])
def get_coin_price_history():
    """
    Get historical coin prices for BTC/ETH/XRP.

    Query params:
        markets: Comma-separated market codes (e.g., 'KRW-BTC,KRW-ETH,KRW-XRP')
        days: Number of days to retrieve (default: 30, max: 365)

    Returns:
        200: Price history retrieved successfully
        400: Invalid parameters
        500: Error retrieving data
    """
    try:
        # Get query parameters
        markets_param = request.args.get('markets', 'KRW-BTC,KRW-ETH,KRW-XRP')
        days = request.args.get('days', 30, type=int)

        # Parse markets
        markets = [m.strip() for m in markets_param.split(',')]

        # Validate markets
        valid_markets = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
        markets = [m for m in markets if m in valid_markets]

        if not markets:
            return jsonify({
                'success': False,
                'error': 'No valid markets specified',
                'valid_markets': valid_markets
            }), 400

        # days=0 means all available data (no limit)
        # Otherwise limit to reasonable range (max 5000 days)
        if days > 0 and days > 5000:
            days = 5000

        logger.info(f"[CoinPrice] Retrieving {len(markets)} markets for {days} days")

        # Get database session
        db = get_db_session()

        # Build query with optional date filter
        if days > 0:
            # Calculate cutoff date
            cutoff_date = datetime.now() - timedelta(days=days)

            # Query price history with date filter
            query = text("""
                SELECT
                    market,
                    date,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume
                FROM coin_price_history
                WHERE market = ANY(:markets)
                AND date >= :cutoff_date
                ORDER BY date ASC
            """)

            result = db.execute(query, {
                'markets': markets,
                'cutoff_date': cutoff_date.date()
            })
        else:
            # Query all available data (no date filter)
            query = text("""
                SELECT
                    market,
                    date,
                    open_price,
                    high_price,
                    low_price,
                    close_price,
                    volume
                FROM coin_price_history
                WHERE market = ANY(:markets)
                ORDER BY date ASC
            """)

            result = db.execute(query, {
                'markets': markets
            })

        # Group results by market
        price_data = {}
        for row in result:
            market = row[0]
            if market not in price_data:
                price_data[market] = []

            price_data[market].append({
                'date': row[1].isoformat(),
                'open_price': float(row[2]) if row[2] else None,
                'high_price': float(row[3]) if row[3] else None,
                'low_price': float(row[4]) if row[4] else None,
                'close_price': float(row[5]),
                'volume': float(row[6]) if row[6] else None
            })

        db.close()

        return jsonify({
            'success': True,
            'markets': markets,
            'days': days,
            'data': price_data
        }), 200

    except Exception as e:
        logger.error(f"[CoinPrice] Error in get_coin_price_history: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500


@coin_price_bp.route('/api/coin-prices/latest', methods=['GET'])
def get_latest_coin_prices():
    """
    Get latest coin prices for BTC/ETH/XRP.

    Query params:
        markets: Comma-separated market codes (default: 'KRW-BTC,KRW-ETH,KRW-XRP')

    Returns:
        200: Latest prices retrieved successfully
        400: Invalid parameters
        500: Error retrieving data
    """
    try:
        # Get query parameters
        markets_param = request.args.get('markets', 'KRW-BTC,KRW-ETH,KRW-XRP')

        # Parse markets
        markets = [m.strip() for m in markets_param.split(',')]

        # Validate markets
        valid_markets = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']
        markets = [m for m in markets if m in valid_markets]

        if not markets:
            return jsonify({
                'success': False,
                'error': 'No valid markets specified',
                'valid_markets': valid_markets
            }), 400

        # Get database session
        db = get_db_session()

        # Query latest price for each market
        latest_prices = {}

        for market in markets:
            query = text("""
                SELECT
                    date,
                    close_price
                FROM coin_price_history
                WHERE market = :market
                ORDER BY date DESC
                LIMIT 1
            """)

            result = db.execute(query, {'market': market})
            row = result.fetchone()

            if row:
                latest_prices[market] = {
                    'date': row[0].isoformat(),
                    'price': float(row[1])
                }

        db.close()

        return jsonify({
            'success': True,
            'prices': latest_prices
        }), 200

    except Exception as e:
        logger.error(f"[CoinPrice] Error in get_latest_coin_prices: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500
