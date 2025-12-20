"""
Upbit API Proxy Routes

Proxies requests to Upbit API for chart data and market information.
This avoids CORS issues and provides a unified API interface.
"""

from flask import Blueprint, jsonify, request
import requests
import logging

# Create Blueprint
upbit_proxy_bp = Blueprint('upbit_proxy', __name__)

# Logger
logger = logging.getLogger(__name__)

# Upbit API base URL
UPBIT_BASE_URL = 'https://api.upbit.com'


@upbit_proxy_bp.route('/api/upbit/candles/<interval>', methods=['GET'])
def get_candles(interval):
    """
    Proxy endpoint for Upbit candle data

    Intervals: minutes/1, minutes/3, minutes/5, minutes/10, minutes/15,
               minutes/30, minutes/60, minutes/240, days, weeks, months

    Query params:
        market: Market code (e.g., KRW-BTC)
        count: Number of candles (max 200, default 200)
        to: End time (ISO 8601 format, optional)
    """
    try:
        market = request.args.get('market', 'KRW-BTC')
        count = request.args.get('count', 200, type=int)
        to = request.args.get('to')

        # Validate count
        if count > 200:
            count = 200

        # Build Upbit API URL
        upbit_url = f"{UPBIT_BASE_URL}/v1/candles/{interval}"

        # Build query parameters
        params = {
            'market': market,
            'count': count
        }
        if to:
            params['to'] = to

        logger.info(f"[UpbitProxy] Fetching {interval} candles for {market}, count={count}")

        # Make request to Upbit API
        response = requests.get(upbit_url, params=params, timeout=10)

        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            logger.error(f"[UpbitProxy] Upbit API error: {response.status_code}")
            return jsonify({
                'success': False,
                'error': f'Upbit API returned {response.status_code}'
            }), response.status_code

    except Exception as e:
        logger.error(f"[UpbitProxy] Error fetching candles: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@upbit_proxy_bp.route('/api/upbit/market/all', methods=['GET'])
def get_market_all():
    """
    Proxy endpoint for Upbit market list

    Query params:
        isDetails: Include market details (default: false)
    """
    try:
        is_details = request.args.get('isDetails', 'false')

        upbit_url = f"{UPBIT_BASE_URL}/v1/market/all"
        params = {'isDetails': is_details}

        logger.info(f"[UpbitProxy] Fetching market list")

        response = requests.get(upbit_url, params=params, timeout=10)

        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            logger.error(f"[UpbitProxy] Upbit API error: {response.status_code}")
            return jsonify({
                'success': False,
                'error': f'Upbit API returned {response.status_code}'
            }), response.status_code

    except Exception as e:
        logger.error(f"[UpbitProxy] Error fetching market list: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@upbit_proxy_bp.route('/api/upbit/ticker', methods=['GET'])
def get_ticker():
    """
    Proxy endpoint for Upbit ticker (current price)

    Query params:
        markets: Comma-separated market codes (e.g., KRW-BTC,KRW-ETH)
    """
    try:
        markets = request.args.get('markets', 'KRW-BTC')

        upbit_url = f"{UPBIT_BASE_URL}/v1/ticker"
        params = {'markets': markets}

        logger.debug(f"[UpbitProxy] Fetching ticker for {markets}")

        response = requests.get(upbit_url, params=params, timeout=10)

        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            logger.error(f"[UpbitProxy] Upbit API error: {response.status_code}")
            return jsonify({
                'success': False,
                'error': f'Upbit API returned {response.status_code}'
            }), response.status_code

    except Exception as e:
        logger.error(f"[UpbitProxy] Error fetching ticker: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@upbit_proxy_bp.route('/api/upbit/orderbook', methods=['GET'])
def get_orderbook():
    """
    Proxy endpoint for Upbit orderbook

    Query params:
        markets: Comma-separated market codes (e.g., KRW-BTC,KRW-ETH)
    """
    try:
        markets = request.args.get('markets', 'KRW-BTC')

        upbit_url = f"{UPBIT_BASE_URL}/v1/orderbook"
        params = {'markets': markets}

        logger.debug(f"[UpbitProxy] Fetching orderbook for {markets}")

        response = requests.get(upbit_url, params=params, timeout=10)

        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            logger.error(f"[UpbitProxy] Upbit API error: {response.status_code}")
            return jsonify({
                'success': False,
                'error': f'Upbit API returned {response.status_code}'
            }), response.status_code

    except Exception as e:
        logger.error(f"[UpbitProxy] Error fetching orderbook: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
