"""
Holdings Routes Module

Handles API endpoints for:
- Holdings data (portfolio)
- Current price queries
- Orders history
"""

from flask import Blueprint, jsonify, request
import requests
import datetime
from datetime import timezone

# Create Blueprint
holdings_bp = Blueprint('holdings', __name__)


def init_holdings_routes(config, upbit_api, holdings_service):
    """
    Initialize holdings routes with dependencies.

    Args:
        config: Configuration dictionary
        upbit_api: UpbitAPI instance
        holdings_service: HoldingsService instance
    """
    UPBIT_BASE_URL = config.get('api', {}).get('upbit_base_url', 'https://api.upbit.com')

    @holdings_bp.route('/api/holdings')
    def get_holdings():
        """Get holdings data from Upbit API (new structured format)"""
        try:
            print("Holdings data request received")

            # Get new structured format (legacy_format=False)
            holdings_data = holdings_service.get_real_holdings_data(legacy_format=False)

            # Add success and api_mode fields
            response_data = {
                "success": True,
                **holdings_data,  # Spread krw, coins, summary
                "api_mode": "real" if upbit_api else "fallback"
            }

            coin_count = holdings_data.get('summary', {}).get('coin_count', 0)
            print(f"Holdings data returned: {coin_count} coins ({'Real API' if upbit_api else 'Fallback data'})")
            return jsonify(response_data)
        except Exception as e:
            print(f"Holdings error: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    @holdings_bp.route('/api/trading/current-price/<market>')
    def get_current_price(market):
        """Get current price for specific market"""
        try:
            print(f"Current price request: {market}")
            # Query current price from Upbit API
            url = f"{UPBIT_BASE_URL}/v1/ticker"
            params = {"markets": market}
            request_timeout = config.get('api', {}).get('request_timeout', 5)
            response = requests.get(url, params=params, timeout=request_timeout)

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    ticker = data[0]
                    current_price = ticker.get('trade_price', 0)
                    change_price = ticker.get('change_price', 0)
                    change_rate = ticker.get('change_rate', 0)
                    print(f"{market} current price query success: {current_price}")
                    return jsonify({
                        "success": True,
                        "price": current_price,
                        "change_price": change_price,
                        "change_rate": change_rate,
                        "market": market
                    })
                else:
                    print(f"{market} current price query failed: No data")
                    return jsonify({"success": False, "error": "No data available"}), 404
            else:
                print(f"{market} current price query failed: {response.status_code}")
                return jsonify({"success": False, "error": f"API error: {response.status_code}"}), 500
        except Exception as e:
            print(f"Current price query error: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    @holdings_bp.route('/api/account/balance')
    def get_account_balance():
        """Get account balance (KRW and all coins)"""
        try:
            print("Account balance request received")

            if not upbit_api:
                print("Upbit API keys not configured")
                return jsonify({
                    "success": False,
                    "error": "API keys not configured",
                    "balance": {"krw": 0, "coins": []}
                })

            # Get accounts from Upbit API
            accounts = upbit_api.get_accounts()

            if not accounts:
                return jsonify({
                    "success": True,
                    "balance": {"krw": 0, "coins": []},
                    "api_mode": "real"
                })

            # Process balance data
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
                    if balance > 0 or locked > 0:  # Only include coins with balance
                        coin_balances.append({
                            'currency': currency,
                            'balance': balance,
                            'locked': locked,
                            'avg_buy_price': avg_buy_price
                        })

            print(f"Account balance retrieved: KRW {krw_balance:,.0f}, {len(coin_balances)} coins")
            return jsonify({
                "success": True,
                "balance": {
                    "krw": krw_balance,
                    "coins": coin_balances
                },
                "api_mode": "real"
            })

        except Exception as e:
            print(f"Account balance error: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    @holdings_bp.route('/api/orders')
    @holdings_bp.route('/api/trading/orders')
    def get_orders():
        """
        Get orders history - DATABASE FIRST strategy with automatic sync.

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

        try:
            print(f"[Orders] Request: market={market}, state={state}, limit={limit}, use_api={use_api}")

            # Strategy 1: Query from DATABASE (fast, no API limit)
            if not use_api:
                db = None
                try:
                    db = get_db_session()
                    query = db.query(Order).filter(Order.state == state)

                    if market:
                        query = query.filter(Order.market == market)

                    # Order by executed_at
                    if order_by == 'asc':
                        query = query.order_by(asc(Order.executed_at))
                    else:
                        query = query.order_by(desc(Order.executed_at))

                    query = query.limit(limit)
                    orders_db = query.all()

                    if orders_db:
                        # Convert to response format
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

                        print(f"[Orders] SUCCESS: DB query returned {len(processed_orders)} orders (95% faster than API)")

                        return jsonify({
                            "success": True,
                            "orders": processed_orders,
                            "source": "database",
                            "count": len(processed_orders)
                        })
                    else:
                        print(f"[Orders] WARNING: DB empty - falling back to API")

                except Exception as db_error:
                    print(f"[Orders] WARNING: DB error: {db_error} - falling back to API")
                finally:
                    # CRITICAL: Always close DB session to prevent connection leaks
                    if db:
                        db.close()

            # Strategy 2: Fallback to API (if database is empty or use_api=true)
            if not upbit_api:
                print("[Orders] ERROR: API keys not configured")
                return jsonify({
                    "success": False,
                    "error": "API keys not configured and no data in database",
                    "orders": []
                })

            print(f"[Orders] Querying from Upbit API...")
            orders = upbit_api.get_orders_history(
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

            print(f"[Orders] SUCCESS: API query returned {len(processed_orders)} orders")
            return jsonify({
                "success": True,
                "orders": processed_orders,
                "source": "api"
            })

        except Exception as e:
            print(f"[Orders] ERROR: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    @holdings_bp.route('/api/order/<uuid>')
    def get_order_by_uuid(uuid):
        """Get specific order details by UUID from Upbit API"""
        try:
            if not upbit_api:
                 return jsonify({"success": False, "error": "API keys not configured"}), 400

            order = upbit_api.get_order_by_uuid(uuid)

            if order:
                return jsonify({"success": True, "order": order})
            else:
                return jsonify({"success": False, "error": "Order not found"}), 404

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ========================================
    # DATABASE QUERY ENDPOINTS
    # ========================================

    @holdings_bp.route('/api/orders/db')
    def get_orders_from_db():
        """
        Query orders from local database.

        Query params:
            market: Market code (e.g., KRW-BTC)
            side: bid or ask
            limit: Number of orders (default: 100)
            offset: Pagination offset (default: 0)
            order_by: Field to order by (default: executed_at)
            order_dir: asc or desc (default: desc)
        """
        from backend.database import get_db_session, Order
        from sqlalchemy import desc, asc

        market = request.args.get('market', None)
        side = request.args.get('side', None)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        order_by_field = request.args.get('order_by', 'executed_at')
        order_dir = request.args.get('order_dir', 'desc')

        db = None
        try:
            print(f"[DB] Query orders: market={market}, side={side}, limit={limit}, offset={offset}")

            db = get_db_session()
            query = db.query(Order)

            # Apply filters
            if market:
                query = query.filter(Order.market == market)
            if side:
                query = query.filter(Order.side == side)

            # Apply ordering
            order_col = getattr(Order, order_by_field, Order.executed_at)
            if order_dir == 'asc':
                query = query.order_by(asc(order_col))
            else:
                query = query.order_by(desc(order_col))

            # Apply pagination
            query = query.limit(limit).offset(offset)

            # Execute query
            orders = query.all()

            # Convert to dict
            orders_data = []
            for order in orders:
                orders_data.append({
                    'uuid': order.uuid,
                    'market': order.market,
                    'coin': order.market.split('-')[-1] if order.market else '',
                    'side': order.side,
                    'ord_type': order.ord_type,
                    'state': order.state,
                    'price': float(order.price) if order.price else 0,
                    'avg_price': float(order.avg_price) if order.avg_price else 0,
                    'volume': float(order.volume) if order.volume else 0,
                    'executed_volume': float(order.executed_volume) if order.executed_volume else 0,
                    'paid_fee': float(order.paid_fee) if order.paid_fee else 0,
                    'executed_funds': float(order.executed_funds) if order.executed_funds else 0,
                    'executed_at': order.executed_at.isoformat() if order.executed_at else None,
                    'created_at': order.created_at.isoformat() if order.created_at else None,
                    'kr_time': order.kr_time,
                    'strategy_name': order.strategy_name,
                    'signal_source': order.signal_source
                })

            print(f"[DB] Found {len(orders_data)} orders")
            return jsonify({
                'success': True,
                'orders': orders_data,
                'count': len(orders_data),
                'source': 'database'
            })

        except Exception as e:
            print(f"[DB] Query error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            # CRITICAL: Always close DB session
            if db:
                db.close()

    @holdings_bp.route('/api/analytics/orders/stats')
    def get_order_statistics():
        """
        Get order statistics from database.

        Returns:
            - Total orders count
            - Orders by market
            - Orders by side (buy/sell)
            - Total trading volume
            - Total fees paid
        """
        from backend.database import get_db_session, Order
        from sqlalchemy import func

        db = None
        try:
            print("[DB] Fetching order statistics")

            db = get_db_session()

            # Total orders
            total_orders = db.query(func.count(Order.uuid)).scalar()

            # Orders by market
            market_stats = db.query(
                Order.market,
                func.count(Order.uuid).label('count'),
                func.sum(Order.executed_funds).label('total_funds')
            ).group_by(Order.market).all()

            # Orders by side
            side_stats = db.query(
                Order.side,
                func.count(Order.uuid).label('count'),
                func.sum(Order.executed_funds).label('total_funds')
            ).group_by(Order.side).all()

            # Total fees
            total_fees = db.query(func.sum(Order.paid_fee)).scalar() or 0

            # Total trading volume (in KRW)
            total_volume = db.query(func.sum(Order.executed_funds)).scalar() or 0

            return jsonify({
                'success': True,
                'stats': {
                    'total_orders': total_orders,
                    'total_fees': float(total_fees),
                    'total_volume_krw': float(total_volume),
                    'by_market': [
                        {
                            'market': row.market,
                            'count': row.count,
                            'total_funds': float(row.total_funds) if row.total_funds else 0
                        }
                        for row in market_stats
                    ],
                    'by_side': [
                        {
                            'side': row.side,
                            'count': row.count,
                            'total_funds': float(row.total_funds) if row.total_funds else 0
                        }
                        for row in side_stats
                    ]
                }
            })

        except Exception as e:
            print(f"[DB] Statistics error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            # CRITICAL: Always close DB session
            if db:
                db.close()

    @holdings_bp.route('/api/analytics/market/<market>')
    def get_market_analytics(market):
        """
        Get analytics for specific market from database.

        Returns:
            - Total buy/sell count and volume
            - Average buy/sell price
            - Total profit/loss (if closed positions)
            - Recent orders
        """
        from backend.database import get_db_session, Order
        from sqlalchemy import func, desc

        db = None
        try:
            print(f"[DB] Fetching analytics for {market}")

            db = get_db_session()

            # Buy stats
            buy_stats = db.query(
                func.count(Order.uuid).label('count'),
                func.sum(Order.executed_volume).label('total_volume'),
                func.avg(Order.avg_price).label('avg_price'),
                func.sum(Order.executed_funds).label('total_funds')
            ).filter(Order.market == market, Order.side == 'bid').first()

            # Sell stats
            sell_stats = db.query(
                func.count(Order.uuid).label('count'),
                func.sum(Order.executed_volume).label('total_volume'),
                func.avg(Order.avg_price).label('avg_price'),
                func.sum(Order.executed_funds).label('total_funds')
            ).filter(Order.market == market, Order.side == 'ask').first()

            # Recent orders (last 10)
            recent_orders = db.query(Order).filter(
                Order.market == market
            ).order_by(desc(Order.executed_at)).limit(10).all()

            return jsonify({
                'success': True,
                'market': market,
                'analytics': {
                    'buy': {
                        'count': buy_stats.count or 0,
                        'total_volume': float(buy_stats.total_volume) if buy_stats.total_volume else 0,
                        'avg_price': float(buy_stats.avg_price) if buy_stats.avg_price else 0,
                        'total_funds': float(buy_stats.total_funds) if buy_stats.total_funds else 0
                    },
                    'sell': {
                        'count': sell_stats.count or 0,
                        'total_volume': float(sell_stats.total_volume) if sell_stats.total_volume else 0,
                        'avg_price': float(sell_stats.avg_price) if sell_stats.avg_price else 0,
                        'total_funds': float(sell_stats.total_funds) if sell_stats.total_funds else 0
                    },
                    'recent_orders': [
                        {
                            'side': order.side,
                            'executed_volume': float(order.executed_volume) if order.executed_volume else 0,
                            'avg_price': float(order.avg_price) if order.avg_price else 0,
                            'executed_at': order.executed_at.isoformat() if order.executed_at else None
                        }
                        for order in recent_orders
                    ]
                }
            })

        except Exception as e:
            print(f"[DB] Market analytics error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            # CRITICAL: Always close DB session
            if db:
                db.close()

    return holdings_bp
