"""
Unified Upbit API Client

Provides authentication and API calls to Upbit exchange.
Merges functionality from both chart and trading servers.
"""

import requests
import jwt
import hashlib
import uuid
import time
import sys
from urllib.parse import urlencode


class UpbitAPI:
    """
    Unified Upbit API client for all server operations.

    Provides:
    - Account queries
    - Order management (place, cancel, history)
    - Price queries (current, candles)
    - Deposits/Withdraws history
    """

    def __init__(self, access_key, secret_key, base_url='https://api.upbit.com'):
        """
        Initialize Upbit API client.

        Args:
            access_key (str): Upbit API access key
            secret_key (str): Upbit API secret key
            base_url (str): Upbit API base URL (default: https://api.upbit.com)
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.base_url = base_url

    def _get_headers(self, query_hash=None):
        """
        Generate JWT authentication headers.

        Args:
            query_hash (str, optional): SHA512 hash of query parameters

        Returns:
            dict: Headers with JWT authorization
        """
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
        }

        if query_hash:
            payload['query_hash'] = query_hash
            payload['query_hash_alg'] = 'SHA512'

        jwt_token = jwt.encode(payload, self.secret_key, algorithm='HS256')

        return {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }

    # ==================== Account Operations ====================

    def get_accounts(self):
        """
        Get account information (balances).

        Returns:
            list: List of account balances or None on error
        """
        try:
            headers = self._get_headers()
            response = requests.get(f'{self.base_url}/v1/accounts', headers=headers)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"[UpbitAPI] Account query failed: {response.status_code}, {response.text}")
                return None
        except Exception as e:
            print(f"[UpbitAPI] Account query error: {str(e)}")
            return None

    # ==================== Market Information ====================

    def get_markets(self):
        """
        Get list of available markets.

        Returns:
            list: List of market information dicts or empty list on error
                Each dict contains: market, korean_name, english_name
        """
        try:
            response = requests.get(f'{self.base_url}/v1/market/all')

            if response.status_code == 200:
                return response.json()
            else:
                print(f"[UpbitAPI] Markets query failed: {response.status_code}, {response.text}")
                return []
        except Exception as e:
            print(f"[UpbitAPI] Markets query error: {str(e)}")
            return []

    # ==================== Price Queries ====================

    def get_current_price(self, market):
        """
        Get current price for single market.

        Args:
            market (str): Market code (e.g., 'KRW-BTC')

        Returns:
            float: Current price or None on error
        """
        try:
            response = requests.get(f'{self.base_url}/v1/ticker?markets={market}')

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return float(data[0]['trade_price'])
                else:
                    print(f"[UpbitAPI] Price query failed: {market} no data")
                    return None
            else:
                print(f"[UpbitAPI] Price query failed: {response.status_code}, {response.text}")
                return None
        except Exception as e:
            print(f"[UpbitAPI] Price query error: {str(e)}")
            return None

    def get_current_prices(self, markets):
        """
        Get current prices for multiple markets.

        Args:
            markets (list): List of market codes (e.g., ['KRW-BTC', 'KRW-ETH'])

        Returns:
            dict: Dictionary of {market: price_data} or empty dict on error
        """
        try:
            markets_str = ','.join(markets)
            print(f"[UpbitAPI] Price query for: {markets_str}")
            response = requests.get(f'{self.base_url}/v1/ticker?markets={markets_str}')

            if response.status_code == 200:
                data = response.json()
                print(f"[UpbitAPI] Price query success: {len(data)} coins")
                return {item['market']: item for item in data}
            else:
                print(f"[UpbitAPI] Price query failed: {response.status_code}, {response.text}")
                return {}
        except Exception as e:
            print(f"[UpbitAPI] Price query error: {str(e)}")
            return {}

    def get_ticker(self, markets='ALL'):
        """
        Get ticker information for markets.

        Args:
            markets (str or list): 'ALL' for all KRW markets, or list/string of specific markets

        Returns:
            list: List of ticker data or empty list on error
                Each ticker contains: market, trade_price, acc_trade_price_24h, etc.
        """
        try:
            if markets == 'ALL':
                # Get all KRW markets first
                all_markets = self.get_markets()
                krw_markets = [m['market'] for m in all_markets if m['market'].startswith('KRW-')]
                markets_str = ','.join(krw_markets)
            elif isinstance(markets, list):
                markets_str = ','.join(markets)
            else:
                markets_str = markets

            response = requests.get(f'{self.base_url}/v1/ticker?markets={markets_str}')

            if response.status_code == 200:
                return response.json()
            else:
                print(f"[UpbitAPI] Ticker query failed: {response.status_code}, {response.text}")
                return []
        except Exception as e:
            print(f"[UpbitAPI] Ticker query error: {str(e)}")
            return []

    # ==================== Candle Data ====================

    def get_candles_days(self, market, count=200, to=None):
        """
        Get daily candle data.

        Args:
            market (str): Market code (e.g., 'KRW-BTC')
            count (int): Number of candles (default: 200, max: 200)
            to (str, optional): End datetime (YYYY-MM-DD HH:mm:ss)

        Returns:
            list: List of candle data or empty list on error
        """
        try:
            query_params = {
                'market': market,
                'count': count
            }

            if to:
                query_params['to'] = to

            response = requests.get(f'{self.base_url}/v1/candles/days', params=query_params)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"[UpbitAPI] Daily candle query failed: {response.status_code}, {response.text}")
                return []
        except Exception as e:
            print(f"[UpbitAPI] Daily candle query error: {str(e)}")
            return []

    # ==================== Order Management ====================

    def place_order(self, market, side, volume=None, price=None, ord_type='limit'):
        """
        Place order.

        Args:
            market (str): Market code (e.g., 'KRW-BTC')
            side (str): 'bid' (buy) or 'ask' (sell)
            volume (float, optional): Order volume
            price (float, optional): Order price
            ord_type (str): 'limit' or 'market' (default: 'limit')

        Returns:
            dict: Order result with 'success' field
        """
        try:
            query_params = {
                'market': market,
                'side': side,
                'ord_type': ord_type
            }

            if ord_type == 'limit':
                if not price:
                    raise ValueError("Price required for limit order")
                query_params['price'] = str(price)
                if volume:
                    query_params['volume'] = str(volume)
            elif ord_type == 'market':
                if side == 'bid':  # Buy: need total amount
                    if not price:
                        raise ValueError("Price (total amount) required for market buy")
                    query_params['price'] = str(price)
                else:  # Sell: need volume
                    if not volume:
                        raise ValueError("Volume required for market sell")
                    query_params['volume'] = str(volume)
            elif ord_type == 'price':
                # Market buy with specific KRW amount
                if not price:
                    raise ValueError("Price (KRW amount) required for price order")
                query_params['price'] = str(price)

            query_string = urlencode(query_params, doseq=True)
            query_hash = hashlib.sha512(query_string.encode('utf-8')).hexdigest()

            headers = self._get_headers(query_hash)
            print(f"[UpbitAPI] Order API call: {self.base_url}/v1/orders, params: {query_params}")
            response = requests.post(f'{self.base_url}/v1/orders', json=query_params, headers=headers)

            print(f"[UpbitAPI] Order API response: {response.status_code}")
            if response.status_code == 201:
                order_result = response.json()
                print(f"[UpbitAPI] Order success: {order_result}")
                return {
                    'success': True,
                    'order': order_result,
                    'uuid': order_result.get('uuid'),
                    'market': order_result.get('market'),
                    'side': order_result.get('side'),
                    'ord_type': order_result.get('ord_type'),
                    'price': order_result.get('price'),
                    'volume': order_result.get('volume')
                }
            else:
                error_msg = response.text
                print(f"[UpbitAPI] Order failed: {response.status_code}, {error_msg}")
                return {
                    'success': False,
                    'error': f"Order failed: {response.status_code}",
                    'details': error_msg
                }
        except Exception as e:
            print(f"[UpbitAPI] Order error: {str(e)}")
            return {
                'success': False,
                'error': f"Order error: {str(e)}"
            }

    def cancel_order(self, order_uuid):
        """
        Cancel order by UUID.

        Args:
            order_uuid (str): Order UUID

        Returns:
            dict: Result with 'success' field
        """
        try:
            query_params = {'uuid': order_uuid}
            query_string = urlencode(query_params, doseq=True)
            query_hash = hashlib.sha512(query_string.encode('utf-8')).hexdigest()

            headers = self._get_headers(query_hash)
            print(f"[UpbitAPI] Cancel order API call: uuid={order_uuid}")
            response = requests.delete(f'{self.base_url}/v1/order', params=query_params, headers=headers)

            print(f"[UpbitAPI] Cancel order response: {response.status_code}")
            if response.status_code == 200:
                cancel_result = response.json()
                print(f"[UpbitAPI] Cancel order success: {cancel_result}")
                return {
                    'success': True,
                    'cancelled_order': cancel_result
                }
            else:
                error_msg = response.text
                print(f"[UpbitAPI] Cancel order failed: {response.status_code}, {error_msg}")
                return {
                    'success': False,
                    'error': f"Cancel order failed: {response.status_code}",
                    'details': error_msg
                }
        except Exception as e:
            print(f"[UpbitAPI] Cancel order error: {str(e)}")
            return {
                'success': False,
                'error': f"Cancel order error: {str(e)}"
            }

    def get_order_by_uuid(self, order_uuid):
        """
        Get order detail by UUID.

        Args:
            order_uuid (str): Order UUID

        Returns:
            dict: Order detail or None on error
        """
        try:
            query_params = {'uuid': order_uuid}
            query_string = urlencode(query_params)
            query_hash = hashlib.sha512(query_string.encode('utf-8')).hexdigest()
            headers = self._get_headers(query_hash)

            print(f"[UpbitAPI] Query order by UUID: {order_uuid}", file=sys.stderr, flush=True)
            response = requests.get(f'{self.base_url}/v1/order', params=query_params, headers=headers)

            print(f"[UpbitAPI] UUID query response: {response.status_code}", file=sys.stderr, flush=True)
            if response.status_code == 200:
                order = response.json()
                print(f"[UpbitAPI] Order found: {order.get('created_at')} {order.get('market')} {order.get('state')}", file=sys.stderr, flush=True)
                return order
            else:
                print(f"[UpbitAPI] UUID query failed: {response.text}", file=sys.stderr, flush=True)
                return None
        except Exception as e:
            print(f"[UpbitAPI] UUID query error: {str(e)}", file=sys.stderr, flush=True)
            return None

    def get_orders_history(self, market=None, state='done', limit=100, page=1, include_trades=False, order_by='desc'):
        """
        Get order history.

        Args:
            market (str, optional): Market code to filter
            state (str): Order state ('done', 'wait', 'cancel')
            limit (int): Number of orders per page (max: 100)
            page (int): Page number
            include_trades (bool): Include trade execution details
            order_by (str): Sort order ('asc' for oldest first, 'desc' for newest first)

        Returns:
            list: List of orders or empty list on error
        """
        try:
            query_params = {
                'state': state,
                'limit': limit,
                'page': page,
                'order_by': order_by
            }

            if market:
                query_params['market'] = market

            query_string = urlencode(query_params, doseq=True)
            query_hash = hashlib.sha512(query_string.encode('utf-8')).hexdigest()

            headers = self._get_headers(query_hash)
            print(f"[UpbitAPI] Orders API call: {self.base_url}/v1/orders, params: {query_params}")
            response = requests.get(f'{self.base_url}/v1/orders', params=query_params, headers=headers)

            print(f"[UpbitAPI] API response: {response.status_code}", file=sys.stderr, flush=True)
            if response.status_code == 200:
                orders = response.json()
                print(f"[UpbitAPI] Orders retrieved: {len(orders)}", file=sys.stderr, flush=True)

                # include_trades: Get detailed execution info
                if include_trades and orders:
                    print(f"[UpbitAPI] Fetching trade details...", file=sys.stderr, flush=True)
                    detailed_orders = []

                    for order in orders:
                        order_uuid = order.get('uuid')
                        detail = self.get_order_by_uuid(order_uuid)

                        if detail and 'trades' in detail and detail['trades']:
                            # Create separate entry for each trade
                            for trade in detail['trades']:
                                detailed_orders.append({
                                    'uuid': order_uuid,
                                    'side': order.get('side'),
                                    'ord_type': order.get('ord_type'),
                                    'market': order.get('market'),
                                    'state': order.get('state'),
                                    'order_created_at': order.get('created_at'),
                                    'executed_at': trade.get('created_at'),
                                    'price': trade.get('price'),
                                    'volume': trade.get('volume'),
                                    'funds': trade.get('funds'),
                                    'avg_price': order.get('avg_price'),
                                    'executed_volume': order.get('executed_volume'),
                                    'paid_fee': order.get('paid_fee')
                                })
                        else:
                            detailed_orders.append(order)

                        time.sleep(0.05)  # Rate limiting

                    # Sort by execution time
                    detailed_orders.sort(
                        key=lambda x: x.get('executed_at', x.get('order_created_at', '')),
                        reverse=True
                    )

                    print(f"[UpbitAPI] Trade details retrieved: {len(detailed_orders)} trades", file=sys.stderr, flush=True)
                    return detailed_orders
                else:
                    return orders
            else:
                print(f"[UpbitAPI] Orders query failed: {response.status_code}, {response.text}")
                return []
        except Exception as e:
            print(f"[UpbitAPI] Orders query error: {str(e)}")
            return []

    # ==================== Advanced Operations ====================

    def calculate_real_avg_price(self, market):
        """
        Calculate real average buy price from all buy orders.

        Args:
            market (str): Market code (e.g., 'KRW-BTC')

        Returns:
            float: Average buy price or None on error
        """
        try:
            print(f"[UpbitAPI] Calculating avg price for {market}")

            all_buy_orders = []
            page = 1

            while True:
                orders = self.get_orders_history(market=market, state='done', limit=100, page=page)
                if not orders:
                    break

                buy_orders = [order for order in orders if order.get('side') == 'bid']
                all_buy_orders.extend(buy_orders)

                if len(orders) < 100:
                    break

                page += 1
                time.sleep(0.1)

            if not all_buy_orders:
                print(f"[UpbitAPI] No buy history for {market}")
                return None

            total_cost = 0
            total_volume = 0

            for order in all_buy_orders:
                executed_volume = float(order.get('executed_volume', 0))
                avg_price = float(order.get('avg_price', 0))
                total_cost += executed_volume * avg_price
                total_volume += executed_volume

            if total_volume == 0:
                print(f"[UpbitAPI] Total volume is 0 for {market}")
                return None

            real_avg_price = total_cost / total_volume
            print(f"[UpbitAPI] Avg price calculated: {real_avg_price:.2f} (from {len(all_buy_orders)} orders)")

            return real_avg_price

        except Exception as e:
            print(f"[UpbitAPI] Avg price calculation error: {str(e)}")
            return None

    # ==================== Deposits & Withdraws ====================

    def get_deposits(self, currency=None, state=None, limit=100):
        """
        Get deposit history.

        Args:
            currency (str, optional): Currency code to filter
            state (str, optional): Deposit state (None=all, 'submitting', 'submitted', 'almost_accepted', 'rejected', 'accepted', 'processing')
            limit (int): Number of records (max: 100)

        Returns:
            list: List of deposits or empty list on error
        """
        try:
            query_params = {
                'limit': limit
            }

            if state:
                query_params['state'] = state

            if currency:
                query_params['currency'] = currency

            query_string = urlencode(query_params, doseq=True)
            query_hash = hashlib.sha512(query_string.encode('utf-8')).hexdigest()

            headers = self._get_headers(query_hash)
            response = requests.get(f'{self.base_url}/v1/deposits', params=query_params, headers=headers)

            if response.status_code == 200:
                deposits = response.json()
                print(f"[UpbitAPI] Deposits retrieved: {len(deposits)}")
                return deposits
            else:
                print(f"[UpbitAPI] Deposits query failed: {response.status_code}, {response.text}")
                return []
        except Exception as e:
            print(f"[UpbitAPI] Deposits query error: {str(e)}")
            return []

    def get_withdraws(self, currency=None, state=None, limit=100):
        """
        Get withdrawal history.

        Args:
            currency (str, optional): Currency code to filter
            state (str, optional): Withdraw state (None=all, 'submitting', 'submitted', 'almost_accepted', 'rejected', 'accepted', 'processing', 'done', 'canceled')
            limit (int): Number of records (max: 100)

        Returns:
            list: List of withdrawals or empty list on error
        """
        try:
            query_params = {
                'limit': limit
            }

            if state:
                query_params['state'] = state

            if currency:
                query_params['currency'] = currency

            query_string = urlencode(query_params, doseq=True)
            query_hash = hashlib.sha512(query_string.encode('utf-8')).hexdigest()

            headers = self._get_headers(query_hash)
            response = requests.get(f'{self.base_url}/v1/withdraws', params=query_params, headers=headers)

            if response.status_code == 200:
                withdraws = response.json()
                print(f"[UpbitAPI] Withdraws retrieved: {len(withdraws)}")
                return withdraws
            else:
                print(f"[UpbitAPI] Withdraws query failed: {response.status_code}, {response.text}")
                return []
        except Exception as e:
            print(f"[UpbitAPI] Withdraws query error: {str(e)}")
            return []
