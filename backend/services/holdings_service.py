"""
Holdings Service Module

Provides portfolio holdings data retrieval and management functionality.
"""

import time


class HoldingsService:
    """
    Service class for managing portfolio holdings data.

    This class handles:
    - Real holdings data retrieval from Upbit API
    - Fallback holdings data when API fails
    - Coin Korean name mapping
    - Average price calculation
    - Profit/loss calculation
    """

    def __init__(self, upbit_api=None):
        """
        Initialize HoldingsService.

        Args:
            upbit_api: UpbitAPI instance for account and price data
        """
        self.upbit_api = upbit_api

    def get_real_holdings_data(self, legacy_format=True):
        """
        Retrieve real holdings data from Upbit API (including withdrawal history).

        Args:
            legacy_format (bool): If True, returns old format with KRW and TOTAL in list.
                                 If False, returns new structured format.

        Returns:
            list or dict: Holdings data in requested format, or fallback data if error
        """
        if not self.upbit_api:
            print("[HoldingsService] Upbit API keys not configured")
            return self.get_fallback_holdings_data(legacy_format)

        try:
            print("[HoldingsService] Starting real account data retrieval...")
            # Get account information
            accounts = self.upbit_api.get_accounts()
            if not accounts:
                print("[HoldingsService] Unable to get account information")
                return self.get_fallback_holdings_data()

            print(f"[HoldingsService] Account retrieval successful: {len(accounts)} accounts")

            # Get withdrawal history
            print("[HoldingsService] Retrieving withdrawal history...")
            withdraws = self.upbit_api.get_withdraws(state='done', limit=100)

            # Calculate withdrawal totals by coin
            withdraw_amounts = {}
            for withdraw in withdraws:
                currency = withdraw.get('currency')
                amount = float(withdraw.get('amount', 0))
                if currency and amount > 0:
                    withdraw_amounts[currency] = withdraw_amounts.get(currency, 0) + amount

            print(f"[HoldingsService] Withdrawal history retrieved: {len(withdraw_amounts)} coins, {len(withdraws)} total withdrawals")
            for currency, amount in withdraw_amounts.items():
                print(f"  - {currency}: {amount} withdrawn")

            # Filter non-KRW coins (include if balance or locked is greater than 0)
            crypto_accounts = [acc for acc in accounts if acc['currency'] != 'KRW' and (float(acc['balance']) > 0 or float(acc['locked']) > 0)]

            # Add withdrawn coins (zero balance but has withdrawal history)
            existing_currencies = set(acc['currency'] for acc in crypto_accounts)
            for currency, withdraw_amount in withdraw_amounts.items():
                if currency not in existing_currencies and currency != 'KRW':
                    # Display zero-balance withdrawn coins in portfolio (to preserve history)
                    crypto_accounts.append({
                        "currency": currency,
                        "balance": "0",
                        "locked": "0",
                        "avg_buy_price": "0",
                        "unit_state": "withdrawn",
                        "withdraw_only": True
                    })

            # Get current prices (all held coins plus KRW-BTC/ETH)
            markets_to_fetch = [f'KRW-{acc["currency"]}' for acc in crypto_accounts]
            markets_to_fetch.extend(['KRW-BTC', 'KRW-ETH'])  # Include major coins
            markets_to_fetch = list(set(markets_to_fetch))

            current_prices = self.upbit_api.get_current_prices(markets_to_fetch)

            # Real average price calculation cache (minimize API calls)
            avg_prices_cache = {}
            max_calculate = 5  # Calculate real average price for max 5 coins
            calculated_count = 0

            # Check KRW balance (cash assets)
            krw_account = next((acc for acc in accounts if acc['currency'] == 'KRW'), None)
            total_krw_balance = float(krw_account['balance']) if krw_account else 0
            total_krw_locked = float(krw_account['locked']) if krw_account else 0
            total_krw_value = total_krw_balance + total_krw_locked

            holdings_list = []

            # 1. Add KRW (cash assets)
            holdings_list.append({
                "symbol": "KRW",
                "coin": "KRW",
                "name": "Korean Won",
                "amount": total_krw_balance,
                "balance": total_krw_balance,
                "locked": total_krw_locked,
                "avg_price": 1,
                "current_price": 1,
                "total_value": total_krw_value,
                "profit_loss": 0,
                "profit_rate": 0,
                "pnl_pct": 0,
                "upbit_avg_price": 1,
                "market": "KRW-KRW"
            })

            for account in crypto_accounts:
                currency = account['currency']
                market = f'KRW-{currency}'
                balance = float(account['balance'])
                locked = float(account['locked'])
                amount = balance + locked

                # 2. Calculate real average price (max 5 coins with balance)
                should_calculate = (balance > 0 or locked > 0) and calculated_count < max_calculate
                if should_calculate and market not in avg_prices_cache:
                    print(f"[HoldingsService] {calculated_count+1}/{max_calculate} Calculating {currency} real average price...")
                    try:
                        real_avg_price = self.upbit_api.calculate_real_avg_price(market)
                        avg_prices_cache[market] = real_avg_price
                        calculated_count += 1
                        time.sleep(0.05)  # Minimal delay to prevent API overload
                    except Exception as e:
                        print(f"[HoldingsService] {currency} average price calculation failed: {e}")
                        avg_prices_cache[market] = None

                real_avg_price = avg_prices_cache.get(market)

                # Fallback: Use Upbit API provided average price (faster)
                if real_avg_price is None or real_avg_price == 0:
                    avg_buy_price = float(account.get('avg_buy_price', 0))
                    if should_calculate:
                        print(f"[HoldingsService] {currency} Using fallback average price: {avg_buy_price:,.0f} KRW")
                else:
                    avg_buy_price = real_avg_price
                    print(f"[HoldingsService] {currency} Real average price: {avg_buy_price:,.0f} KRW")

                price_info = current_prices.get(market, {})
                current_price = float(price_info.get('trade_price', 0))

                # If current price is 0, try individual query (with delay)
                if current_price == 0 and market != 'KRW-KRW':
                    print(f"[HoldingsService] {currency} current price 0, attempting individual query...")
                    time.sleep(0.1)  # Short delay for individual query
                    try:
                        individual_prices = self.upbit_api.get_current_prices([market])
                        if individual_prices and market in individual_prices:
                            current_price = float(individual_prices[market].get('trade_price', 0))
                            print(f"[HoldingsService] {currency} individual query success: {current_price}")
                        else:
                            print(f"[HoldingsService] {currency} individual query failed")
                    except Exception as e:
                        print(f"[HoldingsService] {currency} individual query error: {e}")
                        current_price = 0

                # Skip withdrawal-only entries (zero balance, zero avg_buy_price)
                if amount == 0 and avg_buy_price == 0 and account.get('withdraw_only', False):
                    # Don't include in withdrawal history (not actual holdings)
                    continue

                # Calculations
                total_value = amount * current_price
                total_buy_price = amount * avg_buy_price  # FIXED: Use amount (balance + locked) instead of balance only
                profit_loss = total_value - total_buy_price
                profit_rate = (profit_loss / total_buy_price) * 100 if total_buy_price > 0 else 0

                holdings_list.append({
                    "symbol": currency,
                    "coin": currency,
                    "name": self.get_coin_korean_name(currency),
                    "amount": amount,
                    "balance": balance,
                    "locked": locked,
                    "avg_price": avg_buy_price,
                    "current_price": current_price,
                    "total_value": total_value,
                    "profit_loss": profit_loss,
                    "profit_rate": profit_rate,
                    "pnl_pct": profit_rate / 100,
                    "upbit_avg_price": float(account.get('avg_buy_price', 0)),  # Original Upbit average price
                    "market": market
                })

            # Calculate total assets excluding KRW
            total_crypto_value = sum(item['total_value'] for item in holdings_list if item['coin'] != 'KRW')
            total_value = total_crypto_value + total_krw_value

            # Calculate total profit based on principal (exclude KRW - no principal)
            # FIXED: Use amount instead of balance, and use crypto_value instead of double-subtracting KRW
            total_buy_base = sum(item['amount'] * item['avg_price'] for item in holdings_list if item['coin'] != 'KRW')
            total_profit = total_crypto_value - total_buy_base  # Simplified: no need to subtract KRW
            total_profit_rate = (total_profit / total_buy_base) * 100 if total_buy_base > 0 else 0

            # Return format based on legacy_format flag
            if legacy_format:
                # Old format: KRW and TOTAL in the list
                holdings_list.append({
                    "symbol": "TOTAL",
                    "coin": "TOTAL",
                    "name": "Total Assets",
                    "amount": None,
                    "balance": None,
                    "locked": None,
                    "avg_price": None,
                    "current_price": None,
                    "total_value": total_value,
                    "profit_loss": total_profit,
                    "profit_rate": total_profit_rate,
                    "pnl_pct": total_profit_rate / 100,
                    "upbit_avg_price": None,
                    "market": "KRW-TOTAL"
                })
                return holdings_list
            else:
                # New format: Structured with separate krw, coins, and summary
                # Extract KRW data and remove from list
                krw_data = next((item for item in holdings_list if item['coin'] == 'KRW'), None)
                crypto_holdings = [item for item in holdings_list if item['coin'] != 'KRW']

                return {
                    "krw": {
                        "balance": krw_data['balance'] if krw_data else 0,
                        "locked": krw_data['locked'] if krw_data else 0,
                        "total": krw_data['total_value'] if krw_data else 0
                    },
                    "coins": crypto_holdings,
                    "summary": {
                        "total_value": total_value,
                        "total_crypto_value": total_crypto_value,
                        "total_profit": total_profit,
                        "profit_rate": total_profit_rate,
                        "coin_count": len(crypto_holdings)
                    }
                }

        except Exception as e:
            print(f"[HoldingsService] Real holdings data retrieval error: {str(e)}")
            return self.get_fallback_holdings_data(legacy_format)

    def get_coin_korean_name(self, symbol):
        """
        Get Korean name for coin symbol (based on Upbit).

        Args:
            symbol (str): Coin symbol (e.g., 'BTC', 'ETH')

        Returns:
            str: Korean name or symbol if not found
        """
        names = {
            'BTC': 'Bitcoin', 'ETH': 'Ethereum', 'XRP': 'Ripple', 'ADA': 'Cardano', 'DOT': 'Polkadot',
            'LINK': 'Chainlink', 'TRX': 'Tron', 'BCH': 'Bitcoin Cash', 'LTC': 'Litecoin', 'ETC': 'Ethereum Classic',
            'DOGE': 'Dogecoin', 'SOL': 'Solana', 'AVAX': 'Avalanche', 'MATIC': 'Polygon', 'NEAR': 'Near Protocol',
            'APT': 'Aptos', 'SUI': 'Sui', 'SEI': 'Sei', 'MINA': 'Mina', 'AAVE': 'Aave',
            'ATOM': 'Cosmos', 'GRT': 'The Graph', 'AXS': 'Axie Infinity', 'SAND': 'Sandbox', 'MANA': 'Decentraland',
            'CHZ': 'Chiliz', 'T': 'Threshold', 'UNI': 'Uniswap'
        }
        return names.get(symbol, symbol)

    def get_fallback_holdings_data(self, legacy_format=True):
        """
        Get fallback holdings data when API fails (includes current price query).

        Args:
            legacy_format (bool): If True, returns old format with KRW and TOTAL in list.
                                 If False, returns new structured format.

        Returns:
            list or dict: Fallback holdings data in requested format
        """
        # Query current prices for major coins
        major_coins = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "KRW-ADA", "KRW-TRX"]
        current_prices = {}
        try:
            if self.upbit_api:
                current_prices = self.upbit_api.get_current_prices(major_coins)
                print(f"[HoldingsService] Fallback current price query success: {len(current_prices)} coins")
        except Exception as e:
            print(f"[HoldingsService] Fallback current price query failed: {e}")

        # Fallback data structure
        # Use default values if current price not retrieved
        btc_price = float(current_prices.get("KRW-BTC", {}).get('trade_price', 46000000))
        eth_price = float(current_prices.get("KRW-ETH", {}).get('trade_price', 3000000))

        holdings = [
            # KRW (cash assets)
            {
                "symbol": "KRW",
                "coin": "KRW",
                "name": "Korean Won",
                "amount": 10000000,
                "balance": 10000000,
                "locked": 0,
                "avg_price": 1,
                "current_price": 1,
                "total_value": 10000000,
                "profit_loss": 0,
                "profit_rate": 0,
                "pnl_pct": 0,
                "upbit_avg_price": 1,
                "market": "KRW-KRW"
            },
            # BTC
            {
                "symbol": "BTC",
                "coin": "BTC",
                "name": "Bitcoin",
                "amount": 0.16,
                "balance": 0.16,
                "locked": 0,
                "avg_price": 42096774,
                "current_price": btc_price,
                "total_value": 0.16 * btc_price,
                "profit_loss": 0.16 * (btc_price - 42096774),
                "profit_rate": ((btc_price - 42096774) / 42096774 * 100) if 42096774 > 0 else 0,
                "pnl_pct": ((btc_price - 42096774) / 42096774 * 100) / 100 if 42096774 > 0 else 0,
                "upbit_avg_price": 42096774,
                "market": "KRW-BTC"
            },
            # ETH
            {
                "symbol": "ETH",
                "coin": "ETH",
                "name": "Ethereum",
                "amount": 1.25,
                "balance": 1.25,
                "locked": 0,
                "avg_price": 2850000,
                "current_price": eth_price,
                "total_value": 1.25 * eth_price,
                "profit_loss": 1.25 * (eth_price - 2850000),
                "profit_rate": ((eth_price - 2850000) / 2850000 * 100) if 2850000 > 0 else 0,
                "pnl_pct": ((eth_price - 2850000) / 2850000 * 100) / 100 if 2850000 > 0 else 0,
                "upbit_avg_price": 2850000,
                "market": "KRW-ETH"
            }
        ]

        # Calculate total assets
        total_crypto_value = sum(item['total_value'] for item in holdings if item['coin'] != 'KRW')
        total_value = sum(item['total_value'] for item in holdings)
        total_buy_base = sum(item['balance'] * item['avg_price'] for item in holdings if item['coin'] != 'KRW')
        total_profit = sum(item['profit_loss'] for item in holdings)
        total_profit_rate = (total_profit / total_buy_base) * 100 if total_buy_base > 0 else 0

        # Return format based on legacy_format flag
        if legacy_format:
            # Old format: KRW and TOTAL in the list
            holdings.append({
                "symbol": "TOTAL",
                "coin": "TOTAL",
                "name": "Total Assets",
                "amount": None,
                "balance": None,
                "locked": None,
                "avg_price": None,
                "current_price": None,
                "total_value": total_value,
                "profit_loss": total_profit,
                "profit_rate": total_profit_rate,
                "pnl_pct": total_profit_rate / 100,
                "upbit_avg_price": None,
                "market": "KRW-TOTAL"
            })
            return holdings
        else:
            # New format: Structured with separate krw, coins, and summary
            krw_data = next((item for item in holdings if item['coin'] == 'KRW'), None)
            crypto_holdings = [item for item in holdings if item['coin'] != 'KRW']

            return {
                "krw": {
                    "balance": krw_data['balance'] if krw_data else 0,
                    "locked": krw_data['locked'] if krw_data else 0,
                    "total": krw_data['total_value'] if krw_data else 0
                },
                "coins": crypto_holdings,
                "summary": {
                    "total_value": total_value,
                    "total_crypto_value": total_crypto_value,
                    "total_profit": total_profit,
                    "profit_rate": total_profit_rate,
                    "coin_count": len(crypto_holdings)
                }
            }
