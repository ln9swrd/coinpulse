"""
⚠️ LEGACY - Swing Trading Engine (JSON-based, Single-user)

DEPRECATED: Use 'db_swing_trading_engine.py' or 'enhanced_auto_trading_engine.py' instead.

This module uses JSON file storage and is designed for single-user environments.
For multi-user production systems with database support, please use:
- backend/services/enhanced_auto_trading_engine.py (recommended)
- backend/services/db_swing_trading_engine.py

3-day holding strategy with automatic buy/sell execution.
Integrates PositionTracker and SurgePredictor.
"""

import json
import os
from datetime import datetime
from .position_tracker import PositionTracker
from .surge_predictor import SurgePredictor


class SwingTradingEngine:
    """
    Swing trading engine for 3-day holding strategy.

    Features:
    - Automatic surge candidate detection
    - Position management
    - Take-profit / Stop-loss automation
    - Test mode simulation
    - Emergency stop system
    """

    def __init__(self, upbit_api, config_file='swing_trading_config.json'):
        self.upbit_api = upbit_api
        self.config_file = config_file
        self.config = self.load_config()

        # Initialize components
        self.position_tracker = PositionTracker(config_file)
        self.surge_predictor = SurgePredictor(self.config)

        # State
        self.enabled = self.config.get('swing_trading_enabled', False)
        self.test_mode = self.config.get('test_mode', True)
        self.emergency_stopped = False

        print(f"[SwingEngine] Initialized - {'TEST MODE' if self.test_mode else 'LIVE MODE'}")

    def load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"[SwingEngine] ERROR loading config: {e}")
            return {}

    def enable(self, enabled=True):
        """Enable/disable swing trading."""
        self.enabled = enabled
        self.config['swing_trading_enabled'] = enabled
        self.save_config()
        print(f"[SwingEngine] {'Enabled' if enabled else 'Disabled'}")

    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SwingEngine] ERROR saving config: {e}")

    def run_cycle(self):
        """
        Run one trading cycle.

        Steps:
        1. Update existing positions
        2. Check exit conditions
        3. Look for new opportunities
        4. Execute buy signals
        """
        if not self.enabled:
            return

        if self.emergency_stopped:
            print("[SwingEngine] Emergency stopped - skipping cycle")
            return

        try:
            print(f"\n[SwingEngine] ========== Cycle Start ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ==========")

            # 1. Update existing positions
            self._update_positions()

            # 2. Check exit conditions
            self._check_exit_conditions()

            # 3. Look for new opportunities
            self._find_opportunities()

            print("[SwingEngine] ========== Cycle End ==========\n")

        except Exception as e:
            print(f"[SwingEngine] ERROR in cycle: {e}")

    def _update_positions(self):
        """Update all open positions with current prices."""
        try:
            positions = self.position_tracker.positions

            if not positions:
                print("[SwingEngine] No open positions")
                return

            print(f"[SwingEngine] Updating {len(positions)} positions...")

            for coin_symbol in list(positions.keys()):
                try:
                    # Get current price
                    current_price = self.upbit_api.get_current_price(coin_symbol)
                    if not current_price:
                        continue

                    # Update position
                    position = self.position_tracker.update_position(coin_symbol, current_price)
                    if position:
                        pl_percent = position['profit_loss_percent']
                        status_emoji = "🟢" if pl_percent > 0 else "🔴" if pl_percent < 0 else "⚪"
                        print(f"[SwingEngine] {status_emoji} {coin_symbol}: {current_price:,.0f} KRW ({pl_percent:+.2f}%)")

                except Exception as e:
                    print(f"[SwingEngine] Error updating {coin_symbol}: {e}")

        except Exception as e:
            print(f"[SwingEngine] ERROR updating positions: {e}")

    def _check_exit_conditions(self):
        """Check if any positions should be closed."""
        try:
            positions = self.position_tracker.positions

            for coin_symbol in list(positions.keys()):
                try:
                    position = positions[coin_symbol]
                    current_price = position['current_price']

                    # Check exit conditions
                    should_exit, reason = self.position_tracker.check_exit_conditions(coin_symbol, current_price)

                    if should_exit:
                        print(f"[SwingEngine] 🔔 Exit signal for {coin_symbol}: {reason}")
                        self._execute_sell(coin_symbol, current_price, reason)

                except Exception as e:
                    print(f"[SwingEngine] Error checking exit for {coin_symbol}: {e}")

        except Exception as e:
            print(f"[SwingEngine] ERROR checking exits: {e}")

    def _find_opportunities(self):
        """Find new buying opportunities."""
        try:
            # Check if we can open new positions
            available_budget = self.position_tracker.get_available_budget()
            min_order = self.config.get('budget', {}).get('min_order_amount', 6000)

            if available_budget < min_order:
                print(f"[SwingEngine] Insufficient budget: {available_budget:,.0f} KRW")
                return

            # Get excluded coins (BTC, ETH, USDT, currently held)
            excluded = set(self.config.get('coin_selection', {}).get('excluded_coins', []))
            excluded.update(self.position_tracker.positions.keys())  # Add currently held coins

            print(f"[SwingEngine] Scanning for opportunities (excluding {len(excluded)} coins)...")

            # Find surge candidates
            candidates = self.surge_predictor.find_surge_candidates(self.upbit_api, list(excluded))

            if not candidates:
                print("[SwingEngine] No surge candidates found")
                return

            # Show top 5 candidates
            print(f"[SwingEngine] Top {min(5, len(candidates))} candidates:")
            for i, candidate in enumerate(candidates[:5], 1):
                print(f"  {i}. {candidate['coin']}: Score {candidate['score']} - {candidate['signals'].get('volume', {}).get('description', '')}")

            # Try to buy top candidates
            max_positions = self.config.get('budget', {}).get('max_concurrent_positions', 3)
            current_positions = len(self.position_tracker.positions)

            for candidate in candidates:
                if current_positions >= max_positions:
                    print(f"[SwingEngine] Max positions ({max_positions}) reached")
                    break

                coin_symbol = candidate['coin']
                current_price = candidate['current_price']
                score = candidate['score']

                # Calculate order amount
                order_amount = self._calculate_order_amount(available_budget)

                if self.position_tracker.can_open_new_position(order_amount):
                    self._execute_buy(coin_symbol, current_price, order_amount, score)
                    current_positions += 1
                    available_budget -= order_amount

        except Exception as e:
            print(f"[SwingEngine] ERROR finding opportunities: {e}")

    def _calculate_order_amount(self, available_budget):
        """Calculate order amount based on available budget."""
        min_order = self.config.get('budget', {}).get('min_order_amount', 6000)
        max_order = self.config.get('budget', {}).get('max_order_amount', 40000)
        max_positions = self.config.get('budget', {}).get('max_concurrent_positions', 3)

        # Divide budget equally among max positions
        target_amount = min(available_budget / max_positions, max_order)

        # Round to nearest 1000
        order_amount = round(target_amount / 1000) * 1000

        # Ensure within limits
        return max(min_order, min(order_amount, max_order, available_budget))

    def _execute_buy(self, coin_symbol, price, amount, score):
        """
        Execute buy order.

        Args:
            coin_symbol: Coin to buy
            price: Current price
            amount: Order amount in KRW
            score: Surge probability score
        """
        try:
            print(f"\n[SwingEngine] 🟢 BUY SIGNAL: {coin_symbol}")
            print(f"  Price: {price:,.0f} KRW")
            print(f"  Amount: {amount:,.0f} KRW")
            print(f"  Score: {score}/100")

            if self.test_mode:
                # Test mode - simulate order
                print(f"[SwingEngine] 📝 TEST MODE - Simulating buy")

                # Calculate quantity (assuming we can buy fractional amounts)
                quantity = amount / price

                # Open position in tracker
                position_id = self.position_tracker.open_position(
                    coin_symbol, price, quantity, amount
                )

                if position_id:
                    print(f"[SwingEngine] ✅ Position opened (TEST): {position_id}")
                else:
                    print(f"[SwingEngine] ❌ Failed to open position")

            else:
                # Live mode - execute real order
                print(f"[SwingEngine] 🔴 LIVE MODE - Executing real order")

                # Call Upbit API to place market buy order
                order_result = self.upbit_api.order(
                    market=coin_symbol,
                    side='bid',  # Buy
                    ord_type='price',  # Market order by price
                    price=amount
                )

                if order_result and 'uuid' in order_result:
                    # Wait for order to complete
                    import time
                    time.sleep(2)

                    # Get order details
                    order_info = self.upbit_api.get_order(order_result['uuid'])

                    if order_info and order_info.get('state') == 'done':
                        executed_volume = float(order_info.get('executed_volume', 0))
                        avg_price = float(order_info.get('trades_price', price))

                        # Open position
                        position_id = self.position_tracker.open_position(
                            coin_symbol, avg_price, executed_volume, amount
                        )

                        if position_id:
                            print(f"[SwingEngine] ✅ Order executed: {position_id}")
                        else:
                            print(f"[SwingEngine] ❌ Order executed but position failed")
                    else:
                        print(f"[SwingEngine] ❌ Order not completed")
                else:
                    print(f"[SwingEngine] ❌ Order failed")

        except Exception as e:
            print(f"[SwingEngine] ERROR executing buy: {e}")

    def _execute_sell(self, coin_symbol, price, reason):
        """
        Execute sell order.

        Args:
            coin_symbol: Coin to sell
            price: Current price
            reason: Reason for selling
        """
        try:
            position = self.position_tracker.positions.get(coin_symbol)
            if not position:
                return

            quantity = position['quantity']
            buy_price = position['buy_price']

            print(f"\n[SwingEngine] 🔴 SELL SIGNAL: {coin_symbol}")
            print(f"  Reason: {reason}")
            print(f"  Buy: {buy_price:,.0f} → Sell: {price:,.0f} KRW")
            print(f"  Quantity: {quantity}")

            if self.test_mode:
                # Test mode - simulate sell
                print(f"[SwingEngine] 📝 TEST MODE - Simulating sell")

                profit_loss = self.position_tracker.close_position(coin_symbol, price, reason)

                if profit_loss is not None:
                    print(f"[SwingEngine] ✅ Position closed (TEST): P/L {profit_loss:,.0f} KRW")

                    # Check emergency stop
                    if reason == 'emergency_stop':
                        self._trigger_emergency_stop()
                else:
                    print(f"[SwingEngine] ❌ Failed to close position")

            else:
                # Live mode - execute real sell
                print(f"[SwingEngine] 🔴 LIVE MODE - Executing real order")

                # Call Upbit API to place market sell order
                order_result = self.upbit_api.order(
                    market=coin_symbol,
                    side='ask',  # Sell
                    ord_type='market',  # Market order
                    volume=quantity
                )

                if order_result and 'uuid' in order_result:
                    # Wait for order to complete
                    import time
                    time.sleep(2)

                    # Get order details
                    order_info = self.upbit_api.get_order(order_result['uuid'])

                    if order_info and order_info.get('state') == 'done':
                        avg_price = float(order_info.get('trades_price', price))

                        # Close position
                        profit_loss = self.position_tracker.close_position(coin_symbol, avg_price, reason)

                        if profit_loss is not None:
                            print(f"[SwingEngine] ✅ Order executed: P/L {profit_loss:,.0f} KRW")

                            # Check emergency stop
                            if reason == 'emergency_stop':
                                self._trigger_emergency_stop()
                        else:
                            print(f"[SwingEngine] ❌ Order executed but close failed")
                    else:
                        print(f"[SwingEngine] ❌ Order not completed")
                else:
                    print(f"[SwingEngine] ❌ Order failed")

        except Exception as e:
            print(f"[SwingEngine] ERROR executing sell: {e}")

    def _trigger_emergency_stop(self):
        """Trigger emergency stop - halt all trading."""
        self.emergency_stopped = True
        self.enabled = False
        print("\n" + "="*50)
        print("🚨 EMERGENCY STOP TRIGGERED 🚨")
        print("All trading has been halted.")
        print("Manual intervention required to restart.")
        print("="*50 + "\n")

    def get_status(self):
        """Get current trading status."""
        summary = self.position_tracker.get_position_summary()
        stats = self.position_tracker.get_statistics()

        return {
            "enabled": self.enabled,
            "test_mode": self.test_mode,
            "emergency_stopped": self.emergency_stopped,
            "positions": summary,
            "statistics": stats,
            "available_budget": self.position_tracker.get_available_budget()
        }
