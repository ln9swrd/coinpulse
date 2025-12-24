"""
Holdings Routes Module

Handles API endpoints for:
- Holdings data (portfolio) - USER-SPECIFIC
- Current price queries
- Orders history - USER-SPECIFIC

IMPORTANT: All routes use user-specific Upbit API keys from database.
"""

from flask import Blueprint, jsonify, request, g, current_app
import requests
import datetime
from datetime import timezone
import logging
import time

from backend.middleware.user_api_keys import get_user_upbit_api, get_user_from_token
from backend.middleware.auth_middleware import require_auth

# Create Blueprint
holdings_bp = Blueprint('holdings', __name__)

# Get logger
logger = logging.getLogger(__name__)

# Config (will be set by app.py)
UPBIT_BASE_URL = 'https://api.upbit.com'

# User-specific holdings cache (short TTL for real-time updates)
_holdings_cache = {}  # {user_id: {'data': ..., 'timestamp': ...}}
HOLDINGS_CACHE_TTL = 5  # 5 seconds cache


def cleanup_holdings_cache():
    """Remove expired cache entries (called periodically)"""
    now = time.time()
    expired_users = [
        user_id for user_id, entry in _holdings_cache.items()
        if now - entry['timestamp'] > 60  # Remove entries older than 60 seconds
    ]
    for user_id in expired_users:
        del _holdings_cache[user_id]
    if expired_users:
        logger.info(f"[Holdings] Cache cleanup: removed {len(expired_users)} expired entries")


@holdings_bp.route('/api/holdings')
@require_auth
def get_holdings():
    """Get holdings data from Upbit API (USER-SPECIFIC) with caching"""
    start_time = time.time()

    try:
        # Get user_id early for caching
        user_id = g.user_id

        # Check cache first
        cache_entry = _holdings_cache.get(user_id)
        if cache_entry:
            age = time.time() - cache_entry['timestamp']
            if age < HOLDINGS_CACHE_TTL:
                logger.info(f"[Holdings] User {user_id}: Cache hit (age: {age:.2f}s)")
                return jsonify(cache_entry['data'])

        print(f"[Holdings] User {user_id}: Request received (cache miss)")

        # Get user-specific Upbit API instance
        api_start = time.time()
        user_upbit_api = get_user_upbit_api()

        if not user_upbit_api:
            return jsonify({
                "success": False,
                "error": "Upbit API keys not configured. Please add your API keys in Settings.",
                "error_code": "NO_API_KEYS"
            }), 400

        # Get accounts from user's Upbit API
        accounts = user_upbit_api.get_accounts()
        api_time = time.time() - api_start
        logger.info(f"[Holdings] User {user_id}: Accounts fetch took {api_time:.3f}s")

        if not accounts:
            return jsonify({
                "success": True,
                "krw": 0,
                "coins": [],
                "summary": {
                    "total_value_krw": 0,
                    "total_invested_krw": 0,
                    "total_profit_loss_krw": 0,
                    "total_profit_rate": 0,
                    "coin_count": 0
                }
            })

        # Process holdings data
        krw_balance = 0
        coins = []
        total_value_krw = 0
        total_invested_krw = 0

        # First pass: collect all markets and coin data
        coin_data = []
        markets = []

        for account in accounts:
            currency = account.get('currency', '')
            balance = float(account.get('balance', 0))
            locked = float(account.get('locked', 0))
            avg_buy_price = float(account.get('avg_buy_price', 0))

            if currency == 'KRW':
                krw_balance = balance
                total_value_krw += balance
                continue

            if balance > 0 or locked > 0:
                market = f'KRW-{currency}'
                markets.append(market)
                coin_data.append({
                    'currency': currency,
                    'balance': balance,
                    'locked': locked,
                    'avg_buy_price': avg_buy_price,
                    'market': market
                })

        # Batch fetch all prices at once (prevents rate limiting)
        price_map = {}
        if markets:
            price_start = time.time()
            try:
                # Upbit allows fetching multiple tickers at once
                markets_param = ','.join(markets)
                logger.info(f"[Holdings] User {user_id}: Fetching prices for {len(markets)} markets")
                response = requests.get(
                    f'https://api.upbit.com/v1/ticker',
                    params={'markets': markets_param},
                    timeout=5
                )
                price_time = time.time() - price_start
                logger.info(f"[Holdings] User {user_id}: Price fetch took {price_time:.3f}s (status: {response.status_code})")
                if response.status_code == 200:
                    ticker_data = response.json()
                    logger.info(f"[Holdings] Received {len(ticker_data)} tickers")
                    for ticker in ticker_data:
                        price_map[ticker['market']] = ticker['trade_price']
                elif response.status_code == 404:
                    # Batch request failed (likely due to delisted coins), try individual requests
                    logger.warning(f"[Holdings] Batch fetch failed (404), trying individual requests")
                    for market in markets:
                        try:
                            resp = requests.get(
                                f'https://api.upbit.com/v1/ticker',
                                params={'markets': market},
                                timeout=3
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                if data and len(data) > 0:
                                    price_map[market] = data[0]['trade_price']
                                    logger.debug(f"[Holdings] {market}: ₩{data[0]['trade_price']:,.0f}")
                            else:
                                logger.warning(f"[Holdings] Market {market} returned {resp.status_code} (likely delisted)")
                            # Small delay to avoid rate limiting (Upbit allows 10 req/sec)
                            time.sleep(0.12)
                        except Exception as inner_e:
                            logger.warning(f"[Holdings] Failed to fetch {market}: {inner_e}")
                else:
                    logger.error(f"[Holdings] Failed to fetch prices: {response.text}")
            except Exception as e:
                logger.error(f"[Holdings] Error fetching batch prices: {e}")
                import traceback
                traceback.print_exc()

        # Second pass: calculate values using batch prices
        for coin_info in coin_data:
            currency = coin_info['currency']
            market = coin_info['market']
            balance = coin_info['balance']
            locked = coin_info['locked']
            avg_buy_price = coin_info['avg_buy_price']

            # Get current price from batch fetch (or fallback to avg_buy_price)
            current_price = price_map.get(market, avg_buy_price)

            # Handle None values
            if current_price is None or current_price == 0:
                current_price = avg_buy_price if avg_buy_price else 0
            if avg_buy_price is None:
                avg_buy_price = 0

            total_balance = balance + locked
            current_value = total_balance * current_price
            invested_value = total_balance * avg_buy_price
            profit_loss = current_value - invested_value
            profit_rate = (profit_loss / invested_value * 100) if invested_value > 0 else 0

            coins.append({
                'coin': currency,
                'name': currency,
                'balance': total_balance,
                'avg_price': avg_buy_price,
                'current_price': current_price,
                'total_value': current_value,
                'profit_loss': profit_loss,
                'profit_rate': profit_rate,
                'market': market
            })

            total_value_krw += current_value
            total_invested_krw += invested_value

        total_profit_loss_krw = total_value_krw - total_invested_krw - krw_balance
        total_profit_rate = (total_profit_loss_krw / total_invested_krw * 100) if total_invested_krw > 0 else 0

        # Prepare response
        response_data = {
            "success": True,
            "krw": krw_balance,
            "coins": coins,
            "summary": {
                "total_value_krw": total_value_krw,
                "total_invested_krw": total_invested_krw,
                "total_profit_loss_krw": total_profit_loss_krw,
                "total_profit_rate": total_profit_rate,
                "coin_count": len(coins)
            }
        }

        # Cache the response (5 second TTL)
        _holdings_cache[user_id] = {
            'data': response_data,
            'timestamp': time.time()
        }

        # Log total time
        total_time = time.time() - start_time
        print(f"[Holdings] User {user_id}: {len(coins)} coins, ₩{total_value_krw:,.0f} (total: {total_time:.3f}s)")

        return jsonify(response_data)

    except Exception as e:
        print(f"[Holdings] Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@holdings_bp.route('/api/trading/current-price/<market>')
def get_current_price(market):
    """Get current price for specific market (PUBLIC - no auth needed)"""
    try:
        print(f"[Price] Request: {market}")
        url = f"{UPBIT_BASE_URL}/v1/ticker"
        params = {"markets": market}
        response = requests.get(url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                ticker = data[0]
                return jsonify({
                    "success": True,
                    "price": ticker.get('trade_price', 0),
                    "change_price": ticker.get('change_price', 0),
                    "change_rate": ticker.get('change_rate', 0),
                    "market": market
                })

        return jsonify({"success": False, "error": "No data available"}), 404

    except Exception as e:
        print(f"[Price] Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@holdings_bp.route('/api/account/balance')
@require_auth
def get_account_balance():
    """Get account balance (USER-SPECIFIC)"""
    try:
        print("[Balance] Request received")

        # Get user-specific Upbit API
        user_upbit_api = get_user_upbit_api()

        if not user_upbit_api:
            return jsonify({
                "success": False,
                "error": "API keys not configured",
                "balance": {"krw": 0, "coins": []}
            }), 400

        # Get accounts
        accounts = user_upbit_api.get_accounts()

        if not accounts:
            return jsonify({
                "success": True,
                "balance": {"krw": 0, "coins": []},
                "api_mode": "real"
            })

        krw_balance = 0
        coin_balances = []

        for account in accounts:
            currency = account.get('currency', '')
            balance = float(account.get('balance', 0))
            locked = float(account.get('locked', 0))
            avg_buy_price = float(account.get('avg_buy_price', 0))

            if currency == 'KRW':
                krw_balance = balance
            else:
                if balance > 0 or locked > 0:
                    coin_balances.append({
                        'currency': currency,
                        'balance': balance,
                        'locked': locked,
                        'avg_buy_price': avg_buy_price
                    })

        # Get user_id from Flask g object (set by @require_auth decorator)
        user_id = g.user_id
        print(f"[Balance] User {user_id}: KRW ₩{krw_balance:,.0f}, {len(coin_balances)} coins")

        return jsonify({
            "success": True,
            "balance": {
                "krw": krw_balance,
                "coins": coin_balances
            },
            "api_mode": "real"
        })

    except Exception as e:
        print(f"[Balance] Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@holdings_bp.route('/api/orders')
@holdings_bp.route('/api/trading/orders')
@require_auth
def get_orders():
    """
    Get orders history (USER-SPECIFIC) - DATABASE FIRST strategy.

    Query params:
        market: Filter by market (e.g., KRW-BTC)
        state: Order state (default: done)
        limit: Max results (default: 100)
        use_api: Force API query (default: false)
        order_by: asc or desc (default: desc)
    """
    from backend.database import get_db_session, Order
    from sqlalchemy import desc, asc

    market = request.args.get('market', None)
    state = request.args.get('state', 'done')
    limit = request.args.get('limit', 100, type=int)
    use_api = request.args.get('use_api', 'false').lower() == 'true'
    order_by = request.args.get('order_by', 'desc')

    # Get user_id from Flask g object (set by @require_auth decorator)
    user_id = g.user_id

    try:
        print(f"[Orders] User {user_id}: market={market}, limit={limit}")

        # Strategy 1: Query from DATABASE (fast, no API limit)
        if not use_api:
            db = None
            try:
                db = get_db_session()
                query = db.query(Order).filter(
                    Order.state == state,
                    Order.user_id == user_id  # USER-SPECIFIC FILTER
                )

                if market:
                    query = query.filter(Order.market == market)

                if order_by == 'asc':
                    query = query.order_by(asc(Order.executed_at))
                else:
                    query = query.order_by(desc(Order.executed_at))

                query = query.limit(limit)
                orders_db = query.all()

                if orders_db:
                    processed_orders = []
                    for order in orders_db:
                        processed_orders.append({
                            "uuid": order.uuid,
                            "market": order.market,
                            "coin": order.market.split('-')[-1] if order.market else '',
                            "side": order.side,
                            "ord_type": order.ord_type,
                            "price": float(order.price) if order.price else 0,
                            "volume": float(order.volume) if order.volume else 0,
                            "executed_volume": float(order.executed_volume) if order.executed_volume else 0,
                            "avg_price": float(order.avg_price) if order.avg_price else 0,
                            "state": order.state,
                            "created_at": order.created_at.isoformat() if order.created_at else 'N/A',
                            "executed_at": order.executed_at.isoformat() if order.executed_at else 'N/A',
                            "funds": float(order.executed_funds) if order.executed_funds else 0,
                            "paid_fee": float(order.paid_fee) if order.paid_fee else 0,
                            "kr_time": order.kr_time or 'N/A'
                        })

                    print(f"[Orders] User {user_id}: DB returned {len(processed_orders)} orders")

                    return jsonify({
                        "success": True,
                        "orders": processed_orders,
                        "source": "database",
                        "count": len(processed_orders)
                    })

            except Exception as db_error:
                print(f"[Orders] DB error: {db_error}")
            finally:
                if db:
                    db.close()

        # Strategy 2: Fallback to API
        user_upbit_api = get_user_upbit_api()

        if not user_upbit_api:
            return jsonify({
                "success": False,
                "error": "API keys not configured and no data in database",
                "orders": []
            }), 400

        print(f"[Orders] User {user_id}: Querying from API...")
        orders = user_upbit_api.get_orders_history(
            market=market,
            state=state,
            limit=limit,
            include_trades=False,
            order_by=order_by
        )

        if not orders:
            return jsonify({
                "success": True,
                "orders": [],
                "source": "api"
            })

        # Process API response
        processed_orders = []
        for order in orders:
            timestamp_str = order.get('executed_at') or order.get('traded_at') or order.get('created_at', '')
            created_at_kr = 'N/A'

            if timestamp_str:
                try:
                    if timestamp_str.endswith('Z'):
                        created_at = datetime.datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        created_at = datetime.datetime.fromisoformat(timestamp_str)

                    utc_timezone = datetime.timezone.utc
                    kst_timezone = datetime.timezone(datetime.timedelta(hours=9))
                    created_at_utc = created_at.astimezone(utc_timezone)
                    created_at_kst = created_at_utc.astimezone(kst_timezone)
                    created_at_kr = created_at_kst.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    created_at_kr = timestamp_str

            processed_order = {
                "uuid": order.get('uuid', ''),
                "market": order.get('market', ''),
                "coin": order.get('market', '').split('-')[-1] if order.get('market') else '',
                "side": order.get('side', ''),
                "ord_type": order.get('ord_type', ''),
                "price": float(order.get('price', 0)),
                "volume": float(order.get('volume', 0)),
                "executed_volume": float(order.get('executed_volume', 0)),
                "avg_price": float(order.get('avg_price', 0)),
                "state": order.get('state', ''),
                "created_at": order.get('created_at', 'N/A'),
                "executed_at": order.get('executed_at', 'N/A'),
                "funds": float(order.get('funds', 0)),
                "paid_fee": float(order.get('paid_fee', 0)),
                "kr_time": created_at_kr
            }
            processed_orders.append(processed_order)

        print(f"[Orders] User {user_id}: API returned {len(processed_orders)} orders")
        return jsonify({
            "success": True,
            "orders": processed_orders,
            "source": "api"
        })

    except Exception as e:
        print(f"[Orders] Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@holdings_bp.route('/api/order/<uuid>')
@require_auth
def get_order_by_uuid(uuid):
    """Get specific order details by UUID (USER-SPECIFIC)"""
    try:
        user_upbit_api = get_user_upbit_api()

        if not user_upbit_api:
            return jsonify({"success": False, "error": "API keys not configured"}), 400

        order = user_upbit_api.get_order_by_uuid(uuid)

        if order:
            return jsonify({"success": True, "order": order})
        else:
            return jsonify({"success": False, "error": "Order not found"}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@holdings_bp.route('/api/trading/buy', methods=['POST'])
@require_auth
def place_buy_order():
    """
    Place a limit buy order

    Expected JSON body:
    {
        "market": "KRW-BTC",
        "price": "50000000",
        "volume": "0.001"
    }
    """
    try:
        data = request.get_json()

        if not data or 'market' not in data or 'price' not in data or 'volume' not in data:
            return jsonify({"success": False, "error": "Missing required fields: market, price, volume"}), 400

        user_upbit_api = get_user_upbit_api()
        if not user_upbit_api:
            return jsonify({"success": False, "error": "API keys not configured"}), 400

        market = data['market']
        price = str(data['price'])
        volume = str(data['volume'])

        logger.info(f"[Trading] Placing buy order: {market} @ {price} x {volume}")

        # Use place_order with side='bid' for buy orders
        result = user_upbit_api.place_order(
            market=market,
            side='bid',
            volume=volume,
            price=price,
            ord_type='limit'
        )

        if result:
            logger.info(f"[Trading] Buy order placed successfully: {result.get('uuid')}")
            return jsonify({"success": True, "order": result})
        else:
            logger.error(f"[Trading] Failed to place buy order")
            return jsonify({"success": False, "error": "Failed to place order"}), 500

    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Trading] Error placing buy order: {error_msg}")

        # Handle specific error types
        if '429' in error_msg or 'Too Many Requests' in error_msg or 'rate limit' in error_msg.lower():
            return jsonify({
                "success": False,
                "error": "API 요청 한도 초과: 잠시 후 다시 시도해주세요 (30초 대기 권장)",
                "error_code": "RATE_LIMIT_EXCEEDED"
            }), 429
        elif '401' in error_msg or 'Unauthorized' in error_msg:
            return jsonify({
                "success": False,
                "error": "인증 실패: API 키를 확인해주세요",
                "error_code": "UNAUTHORIZED"
            }), 401
        else:
            return jsonify({"success": False, "error": error_msg}), 500


@holdings_bp.route('/api/trading/sell', methods=['POST'])
@require_auth
def place_sell_order():
    """
    Place a limit sell order

    Expected JSON body:
    {
        "market": "KRW-BTC",
        "price": "50000000",
        "volume": "0.001"
    }
    """
    try:
        data = request.get_json()

        if not data or 'market' not in data or 'price' not in data or 'volume' not in data:
            return jsonify({"success": False, "error": "Missing required fields: market, price, volume"}), 400

        user_upbit_api = get_user_upbit_api()
        if not user_upbit_api:
            return jsonify({"success": False, "error": "API keys not configured"}), 400

        market = data['market']
        price = str(data['price'])
        volume = str(data['volume'])

        logger.info(f"[Trading] Placing sell order: {market} @ {price} x {volume}")

        # Use place_order with side='ask' for sell orders
        result = user_upbit_api.place_order(
            market=market,
            side='ask',
            volume=volume,
            price=price,
            ord_type='limit'
        )

        if result:
            logger.info(f"[Trading] Sell order placed successfully: {result.get('uuid')}")
            return jsonify({"success": True, "order": result})
        else:
            logger.error(f"[Trading] Failed to place sell order")
            return jsonify({"success": False, "error": "Failed to place order"}), 500

    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Trading] Error placing sell order: {error_msg}")

        # Handle specific error types
        if '429' in error_msg or 'Too Many Requests' in error_msg or 'rate limit' in error_msg.lower():
            return jsonify({
                "success": False,
                "error": "API 요청 한도 초과: 잠시 후 다시 시도해주세요 (30초 대기 권장)",
                "error_code": "RATE_LIMIT_EXCEEDED"
            }), 429
        elif '401' in error_msg or 'Unauthorized' in error_msg:
            return jsonify({
                "success": False,
                "error": "인증 실패: API 키를 확인해주세요",
                "error_code": "UNAUTHORIZED"
            }), 401
        else:
            return jsonify({"success": False, "error": error_msg}), 500


@holdings_bp.route('/api/trading/cancel/<uuid>', methods=['DELETE'])
@require_auth
def cancel_order(uuid):
    """
    Cancel an existing order by UUID

    URL parameter:
    - uuid: Order UUID to cancel
    """
    try:
        if not uuid:
            return jsonify({"success": False, "error": "Order UUID is required"}), 400

        user_upbit_api = get_user_upbit_api()
        if not user_upbit_api:
            return jsonify({"success": False, "error": "API keys not configured"}), 400

        logger.info(f"[Trading] Canceling order: {uuid}")

        result = user_upbit_api.cancel_order(uuid)

        if result:
            logger.info(f"[Trading] Order canceled successfully: {uuid}")
            return jsonify({"success": True, "order": result})
        else:
            logger.error(f"[Trading] Failed to cancel order: {uuid}")
            return jsonify({"success": False, "error": "Failed to cancel order"}), 500

    except Exception as e:
        logger.error(f"[Trading] Error canceling order {uuid}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
