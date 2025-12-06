"""
Database Swing Trading Engine

Multi-user swing trading engine with database backend.
Supports 100+ concurrent users.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.services.db_position_tracker import DBPositionTracker
from backend.services.surge_predictor import SurgePredictor
from backend.database import get_db_session, UserConfig


class DBSwingTradingEngine:
    """
    Multi-user swing trading engine with database backend.

    Features:
    - Supports 100+ concurrent users
    - User-specific configurations
    - Excludes user's held coins from trading
    - Database-backed position tracking
    - Emergency stop per user
    """

    def __init__(self, upbit_api):
        """
        Initialize the swing trading engine.

        Args:
            upbit_api: UpbitAPI instance (can be None for test mode)
        """
        self.upbit_api = upbit_api
        self.position_tracker = DBPositionTracker()

        print("[DBSwingEngine] Initialized (multi-user mode)")

    def get_user_config(self, user_id):
        """
        Get user configuration from database.

        Args:
            user_id: User ID

        Returns:
            dict: User configuration
        """
        session = get_db_session()
        try:
            config = session.query(UserConfig).filter_by(user_id=user_id).first()
            if config:
                # Convert to dict with surge prediction settings
                config_dict = config.to_dict()

                # Add surge prediction settings
                config_dict['surge_prediction'] = {
                    'min_surge_probability_score': 60,
                    'volume_increase_threshold': 1.5,
                    'rsi_oversold_level': 35,
                    'rsi_buy_zone_max': 50,
                    'support_level_proximity': 0.02,
                    'uptrend_confirmation_days': 3
                }

                # Add coin selection settings
                config_dict['coin_selection'] = {
                    'excluded_coins': ['KRW-BTC', 'KRW-ETH', 'KRW-USDT', 'KRW-USDC']
                }

                return config_dict

            return None

        except Exception as e:
            print(f"[DBSwingEngine] ERROR getting config for user {user_id}: {e}")
            return None
        finally:
            session.close()

    def get_user_held_coins(self, user_id):
        """
        Get coins currently held by user from Upbit API.

        Args:
            user_id: User ID

        Returns:
            list: List of coin symbols (e.g., ['KRW-BTC', 'KRW-ETH'])
        """
        try:
            if not self.upbit_api:
                return []

            # Get user's Upbit accounts
            accounts = self.upbit_api.get_accounts()
            if not accounts:
                return []

            # Extract KRW markets from holdings
            held_coins = []
            for account in accounts:
                currency = account.get('currency')
                balance = float(account.get('balance', 0))

                # Only include coins with positive balance (not KRW)
                if currency != 'KRW' and balance > 0:
                    market_symbol = f'KRW-{currency}'
                    held_coins.append(market_symbol)

            return held_coins

        except Exception as e:
            print(f"[DBSwingEngine] ERROR getting held coins for user {user_id}: {e}")
            return []

    def run_cycle_for_user(self, user_id):
        """
        Run one trading cycle for a specific user.

        Args:
            user_id: User ID

        Returns:
            dict: Cycle results
        """
        try:
            # Get user config
            config = self.get_user_config(user_id)
            if not config:
                print(f"[DBSwingEngine] User {user_id} config not found")
                return {'error': 'User config not found'}

            # Check if swing trading is enabled for this user
            if not config.get('swing_trading_enabled', False):
                return {'status': 'disabled', 'message': 'Swing trading disabled for this user'}

            test_mode = config.get('test_mode', True)

            print(f"\n[DBSwingEngine] ========== User {user_id} Cycle ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ==========")
            print(f"[DBSwingEngine] Mode: {'TEST' if test_mode else 'LIVE'}")

            # Initialize surge predictor with user config
            surge_predictor = SurgePredictor(config)

            # 1. Update existing positions
            results = {'updated': 0, 'closed': 0, 'opened': 0}
            results['updated'] = self._update_positions(user_id)

            # 2. Check exit conditions
            results['closed'] = self._check_exit_conditions(user_id, config, test_mode)

            # 3. Look for new opportunities
            results['opened'] = self._find_opportunities(user_id, config, surge_predictor, test_mode)

            print(f"[DBSwingEngine] User {user_id} Cycle Complete: {results}")
            print("[DBSwingEngine] ========== Cycle End ==========\n")

            return results

        except Exception as e:
            print(f"[DBSwingEngine] ERROR in cycle for user {user_id}: {e}")
            return {'error': str(e)}

    def _update_positions(self, user_id):
        """
        Update all open positions for a user.

        Args:
            user_id: User ID

        Returns:
            int: Number of positions updated
        """
        try:
            positions = self.position_tracker.get_open_positions(user_id)

            if not positions:
                print(f"[DBSwingEngine] User {user_id}: No open positions")
                return 0

            print(f"[DBSwingEngine] User {user_id}: Updating {len(positions)} position(s)...")

            updated_count = 0
            for position in positions:
                try:
                    coin_symbol = position['coin_symbol']

                    # Get current price
                    if self.upbit_api:
                        current_price = self.upbit_api.get_current_price(coin_symbol)
                        if not current_price:
                            continue
                    else:
                        # Test mode - simulate small price change
                        current_price = position['buy_price'] * 1.01

                    # Update position
                    updated = self.position_tracker.update_position(user_id, coin_symbol, current_price)
                    if updated:
                        pl_pct = updated['profit_loss_percent']
                        status = "+" if pl_pct > 0 else "-" if pl_pct < 0 else " "
                        print(f"[DBSwingEngine] User {user_id} - {coin_symbol}: {current_price:,.0f} KRW ({status}{abs(pl_pct):.2f}%)")
                        updated_count += 1

                except Exception as e:
                    print(f"[DBSwingEngine] Error updating position {position.get('coin_symbol')}: {e}")

            return updated_count

        except Exception as e:
            print(f"[DBSwingEngine] ERROR updating positions for user {user_id}: {e}")
            return 0

    def _check_exit_conditions(self, user_id, config, test_mode):
        """
        Check exit conditions for all positions.

        Args:
            user_id: User ID
            config: User configuration
            test_mode: Test mode flag

        Returns:
            int: Number of positions closed
        """
        try:
            positions = self.position_tracker.get_open_positions(user_id)

            closed_count = 0
            for position in positions:
                try:
                    coin_symbol = position['coin_symbol']
                    current_price = position['current_price']

                    # Check exit conditions
                    should_exit, reason = self.position_tracker.check_exit_conditions(
                        user_id, coin_symbol, current_price
                    )

                    if should_exit:
                        print(f"[DBSwingEngine] User {user_id} - Exit signal for {coin_symbol}: {reason}")
                        self._execute_sell(user_id, coin_symbol, current_price, reason, test_mode)
                        closed_count += 1

                except Exception as e:
                    print(f"[DBSwingEngine] Error checking exit for {position.get('coin_symbol')}: {e}")

            return closed_count

        except Exception as e:
            print(f"[DBSwingEngine] ERROR checking exits for user {user_id}: {e}")
            return 0

    def _find_opportunities(self, user_id, config, surge_predictor, test_mode):
        """
        Find and execute buying opportunities.

        Args:
            user_id: User ID
            config: User configuration
            surge_predictor: SurgePredictor instance
            test_mode: Test mode flag

        Returns:
            int: Number of positions opened
        """
        try:
            # Check available budget
            available_budget = self.position_tracker.get_available_budget(user_id)
            min_order = config.get('min_order_amount', 6000)

            if available_budget < min_order:
                print(f"[DBSwingEngine] User {user_id}: Insufficient budget ({available_budget:,.0f} KRW)")
                return 0

            # Get excluded coins
            excluded = set(config.get('coin_selection', {}).get('excluded_coins', []))

            # Add user's held coins to exclusion list
            held_coins = self.get_user_held_coins(user_id)
            excluded.update(held_coins)

            # Add currently traded coins
            open_positions = self.position_tracker.get_open_positions(user_id)
            excluded.update([pos['coin_symbol'] for pos in open_positions])

            print(f"[DBSwingEngine] User {user_id}: Scanning (excluding {len(excluded)} coins)...")

            # Find surge candidates
            if not self.upbit_api:
                print(f"[DBSwingEngine] Test mode: No API available for scanning")
                return 0

            candidates = surge_predictor.find_surge_candidates(self.upbit_api, list(excluded))

            if not candidates:
                print(f"[DBSwingEngine] User {user_id}: No surge candidates found")
                return 0

            # Show top candidates
            print(f"[DBSwingEngine] User {user_id}: Found {len(candidates)} candidate(s)")
            for i, candidate in enumerate(candidates[:5], 1):
                print(f"  {i}. {candidate['coin']}: Score {candidate['score']}")

            # Try to buy top candidates
            max_positions = config.get('max_concurrent_positions', 3)
            current_positions = len(open_positions)
            opened_count = 0

            for candidate in candidates:
                if current_positions >= max_positions:
                    print(f"[DBSwingEngine] User {user_id}: Max positions ({max_positions}) reached")
                    break

                coin_symbol = candidate['coin']
                current_price = candidate['current_price']
                score = candidate['score']

                # Calculate order amount
                order_amount = self._calculate_order_amount(user_id, available_budget, config)

                if self.position_tracker.can_open_new_position(user_id, order_amount):
                    success = self._execute_buy(user_id, coin_symbol, current_price, order_amount, score, test_mode)
                    if success:
                        opened_count += 1
                        current_positions += 1
                        available_budget -= order_amount

            return opened_count

        except Exception as e:
            print(f"[DBSwingEngine] ERROR finding opportunities for user {user_id}: {e}")
            return 0

    def _calculate_order_amount(self, user_id, available_budget, config):
        """
        Calculate order amount based on available budget.

        Args:
            user_id: User ID
            available_budget: Available budget
            config: User configuration

        Returns:
            float: Order amount
        """
        min_order = config.get('min_order_amount', 6000)
        max_order = config.get('max_order_amount', 40000)
        max_positions = config.get('max_concurrent_positions', 3)

        # Divide budget equally among max positions
        target_amount = min(available_budget / max_positions, max_order)

        # Round to nearest 1000
        order_amount = round(target_amount / 1000) * 1000

        # Ensure within limits
        return max(min_order, min(order_amount, max_order, available_budget))

    def _execute_buy(self, user_id, coin_symbol, price, amount, score, test_mode):
        """
        Execute buy order.

        Args:
            user_id: User ID
            coin_symbol: Coin symbol
            price: Current price
            amount: Order amount in KRW
            score: Surge probability score
            test_mode: Test mode flag

        Returns:
            bool: True if successful
        """
        try:
            print(f"\n[DBSwingEngine] User {user_id} - BUY SIGNAL: {coin_symbol}")
            print(f"  Price: {price:,.0f} KRW")
            print(f"  Amount: {amount:,.0f} KRW")
            print(f"  Score: {score}/100")

            if test_mode:
                # Test mode - simulate order
                print(f"[DBSwingEngine] TEST MODE - Simulating buy")

                quantity = amount / price

                position_id = self.position_tracker.open_position(
                    user_id, coin_symbol, price, quantity, amount
                )

                if position_id:
                    print(f"[DBSwingEngine] Position opened (TEST): {position_id}")
                    return True
                else:
                    print(f"[DBSwingEngine] Failed to open position")
                    return False

            else:
                # Live mode - execute real order
                print(f"[DBSwingEngine] LIVE MODE - Executing real order")

                if not self.upbit_api:
                    print(f"[DBSwingEngine] No API available for live trading")
                    return False

                order_result = self.upbit_api.order(
                    market=coin_symbol,
                    side='bid',
                    ord_type='price',
                    price=amount
                )

                if order_result and 'uuid' in order_result:
                    import time
                    time.sleep(2)

                    order_info = self.upbit_api.get_order(order_result['uuid'])

                    if order_info and order_info.get('state') == 'done':
                        executed_volume = float(order_info.get('executed_volume', 0))
                        avg_price = float(order_info.get('trades_price', price))

                        position_id = self.position_tracker.open_position(
                            user_id, coin_symbol, avg_price, executed_volume, amount
                        )

                        if position_id:
                            print(f"[DBSwingEngine] Order executed: {position_id}")
                            return True

                print(f"[DBSwingEngine] Order failed")
                return False

        except Exception as e:
            print(f"[DBSwingEngine] ERROR executing buy for user {user_id}: {e}")
            return False

    def _execute_sell(self, user_id, coin_symbol, price, reason, test_mode):
        """
        Execute sell order.

        Args:
            user_id: User ID
            coin_symbol: Coin symbol
            price: Current price
            reason: Sell reason
            test_mode: Test mode flag

        Returns:
            bool: True if successful
        """
        try:
            positions = self.position_tracker.get_open_positions(user_id)
            position = next((p for p in positions if p['coin_symbol'] == coin_symbol), None)

            if not position:
                return False

            quantity = position['quantity']
            buy_price = position['buy_price']

            print(f"\n[DBSwingEngine] User {user_id} - SELL SIGNAL: {coin_symbol}")
            print(f"  Reason: {reason}")
            print(f"  Buy: {buy_price:,.0f} -> Sell: {price:,.0f} KRW")

            if test_mode:
                # Test mode - simulate sell
                print(f"[DBSwingEngine] TEST MODE - Simulating sell")

                profit_loss = self.position_tracker.close_position(user_id, coin_symbol, price, reason)

                if profit_loss is not None:
                    status = "PROFIT" if profit_loss > 0 else "LOSS"
                    print(f"[DBSwingEngine] Position closed (TEST): {status} {abs(profit_loss):,.0f} KRW")
                    return True

            else:
                # Live mode - execute real sell
                print(f"[DBSwingEngine] LIVE MODE - Executing real order")

                if not self.upbit_api:
                    return False

                order_result = self.upbit_api.order(
                    market=coin_symbol,
                    side='ask',
                    ord_type='market',
                    volume=quantity
                )

                if order_result and 'uuid' in order_result:
                    import time
                    time.sleep(2)

                    order_info = self.upbit_api.get_order(order_result['uuid'])

                    if order_info and order_info.get('state') == 'done':
                        avg_price = float(order_info.get('trades_price', price))

                        profit_loss = self.position_tracker.close_position(user_id, coin_symbol, avg_price, reason)

                        if profit_loss is not None:
                            status = "PROFIT" if profit_loss > 0 else "LOSS"
                            print(f"[DBSwingEngine] Order executed: {status} {abs(profit_loss):,.0f} KRW")
                            return True

            return False

        except Exception as e:
            print(f"[DBSwingEngine] ERROR executing sell for user {user_id}: {e}")
            return False

    def get_user_status(self, user_id):
        """
        Get current trading status for a user.

        Args:
            user_id: User ID

        Returns:
            dict: User trading status
        """
        try:
            config = self.get_user_config(user_id)
            positions = self.position_tracker.get_open_positions(user_id)
            stats = self.position_tracker.get_statistics(user_id)
            available_budget = self.position_tracker.get_available_budget(user_id)

            return {
                'user_id': user_id,
                'enabled': config.get('swing_trading_enabled', False) if config else False,
                'test_mode': config.get('test_mode', True) if config else True,
                'open_positions': len(positions),
                'positions': positions,
                'statistics': stats,
                'available_budget': available_budget,
                'config': config
            }

        except Exception as e:
            print(f"[DBSwingEngine] ERROR getting status for user {user_id}: {e}")
            return {'error': str(e)}
