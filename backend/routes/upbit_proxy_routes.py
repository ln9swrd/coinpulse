"""
Upbit API Proxy Routes

Proxies requests to Upbit API for chart data and market information.
This avoids CORS issues and provides a unified API interface.
"""

from flask import Blueprint, jsonify, request
import requests
import logging
import jwt
import os
from functools import wraps

# Create Blueprint
upbit_proxy_bp = Blueprint('upbit_proxy', __name__)

# Logger
logger = logging.getLogger(__name__)

# Upbit API base URL
UPBIT_BASE_URL = 'https://api.upbit.com'

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '7DfH2jzRD4lCfQ_llC4CObochoaGzaBBZLeODoftgWk')


def verify_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, 'Token has expired'
    except jwt.InvalidTokenError:
        return None, 'Invalid token'


def get_current_user(request):
    """Get current user from Authorization header"""
    auth_header = request.headers.get('Authorization')

    if not auth_header or not auth_header.startswith('Bearer '):
        return None, 'Authorization header missing or invalid'

    token = auth_header.split(' ')[1]
    payload, error = verify_token(token)

    if error:
        return None, error

    return payload.get('user_id'), None


def require_auth(f):
    """Decorator to require JWT authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id, error = get_current_user(request)

        if error:
            return jsonify({
                'success': False,
                'error': error,
                'code': 'UNAUTHORIZED'
            }), 401

        # Add user_id to request context
        request.user_id = user_id

        return f(*args, **kwargs)

    return decorated_function


@upbit_proxy_bp.route('/api/upbit/candles/<interval>', methods=['GET'])
def get_candles(interval):
    """
    Proxy endpoint for Upbit candle data

    Intervals: minutes, days, weeks, months

    Query params:
        market: Market code (e.g., KRW-BTC)
        count: Number of candles (max 200, default 200)
        unit: Unit for minutes interval (1, 3, 5, 10, 15, 30, 60, 240)
        to: End time (ISO 8601 format, optional)
    """
    try:
        market = request.args.get('market', 'KRW-BTC')
        count = request.args.get('count', 200, type=int)
        unit = request.args.get('unit', type=int)
        to = request.args.get('to')

        # Validate count
        if count > 200:
            count = 200

        # Build Upbit API URL with unit for minutes interval
        if interval == 'minutes' and unit:
            # For minutes candles, append unit to URL
            upbit_url = f"{UPBIT_BASE_URL}/v1/candles/{interval}/{unit}"
        else:
            # For days, weeks, months - no unit needed
            upbit_url = f"{UPBIT_BASE_URL}/v1/candles/{interval}"

        # Build query parameters
        params = {
            'market': market,
            'count': count
        }
        if to:
            params['to'] = to

        logger.info(f"[UpbitProxy] Fetching {interval} candles for {market}, count={count}, unit={unit}")

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


@upbit_proxy_bp.route('/api/upbit/accounts', methods=['GET'])
@require_auth
def get_accounts():
    """
    Get user's Upbit account balances (requires authentication)

    Returns:
        200: List of account balances
        401: Unauthorized
        500: Error fetching accounts
    """
    from backend.common import UpbitAPI
    from backend.database.connection import get_db_session
    from backend.database.models import User

    try:
        user_id = request.user_id

        # Get user's API keys from database
        db = get_db_session()
        try:
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                logger.warning(f"[UpbitProxy] User {user_id} not found")
                return jsonify({
                    'success': False,
                    'error': 'User not found',
                    'code': 'USER_NOT_FOUND'
                }), 404

            access_key = user.upbit_access_key
            secret_key = user.upbit_secret_key

            if not access_key or not secret_key:
                logger.warning(f"[UpbitProxy] No API keys found for user {user_id}")
                return jsonify({
                    'success': False,
                    'error': 'No Upbit API keys configured',
                    'code': 'NO_API_KEYS'
                }), 400

            # Initialize Upbit API with user's keys
            upbit_api = UpbitAPI(access_key, secret_key)

            # Fetch accounts
            accounts = upbit_api.get_accounts()

            if accounts is not None:
                logger.info(f"[UpbitProxy] Fetched {len(accounts)} accounts for user {user_id}")
                return jsonify(accounts), 200
            else:
                logger.error(f"[UpbitProxy] Failed to fetch accounts for user {user_id}")
                return jsonify({
                    'success': False,
                    'error': 'Failed to fetch accounts from Upbit',
                    'code': 'UPBIT_API_ERROR'
                }), 500

        finally:
            db.close()

    except Exception as e:
        logger.error(f"[UpbitProxy] Error fetching accounts: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'code': 'INTERNAL_ERROR'
        }), 500
