"""
Enhanced Auto Trading Engine with Real Execution

Features:
- Real order execution via Upbit API
- Database-backed position tracking (multi-user)
- Automated stop-loss and take-profit
- Risk management
- Comprehensive logging
"""

import sys
import os
from datetime import datetime
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.database import get_db_session, UserConfig, SwingTradingLog
from backend.services.db_position_tracker import DBPositionTracker


class EnhancedAutoTradingEngine:
    """
    Enhanced auto trading engine with real order execution.

    Key improvements over original:
    - Real order execution (not just logging)
    - Multi-user support with user_id
    - Database-backed state (no file I/O)
    - Automated stop-loss/take-profit
    - Risk management per user
    """

    def __init__(self, upbit_api):
        """
        Initialize the enhanced trading engine.

        Args:
            upbit_api: UpbitAPI instance for order execution
        """
        self.upbit_api = upbit_api
        self.position_tracker = DBPositionTracker()
        print("[EnhancedAutoTradingEngine] Initialized with real execution support")

    def get_user_config(self, user_id):
        """
        Get user configuration from database.

        Args:
            user_id: User ID

        Returns:
            dict: User configuration or None
        """
        session = get_db_session()
        try:
            config = session.query(UserConfig).filter_by(user_id=user_id).first()
            if config:
                return config.to_dict()
            return None
        except Exception as e:
            print(f"[EnhancedAutoTradingEngine] ERROR getting config for user {user_id}: {e}")
            return None
        finally:
            session.close()

    def analyze_market_conditions(self, coin_symbol, current_price, historical_data):
        """
        Analyze market conditions using technical indicators.

        Args:
            coin_symbol: Coin symbol (e.g., 'KRW-BTC')
            current_price: Current market price
            historical_data: List of candle data (last 20+)

        Returns:
            dict: Analysis result with signal and indicators
        """
        try:
            if not historical_data or len(historical_data) < 20:
                return {
                    "signal": "hold",
                    "confidence": 0.0,
                    "reason": "Insufficient data",
                    "indicators": {}
                }

            # Extract prices
            recent_data = historical_data[:20]
            prices = [float(candle['trade_price']) for candle in recent_data]

            # Calculate moving averages
            sma_5 = sum(prices[:5]) / 5
            sma_10 = sum(prices[:10]) / 10
            sma_20 = sum(prices) / 20

            # Price position relative to SMAs
            price_vs_sma5 = (current_price - sma_5) / sma_5
            price_vs_sma20 = (current_price - sma_20) / sma_20

            # Calculate RSI (14-period)
            gains = []
            losses = []
            for i in range(1, min(15, len(prices))):
                change = prices[i-1] - prices[i]
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))

            avg_gain = sum(gains) / len(gains) if gains else 0.001
            avg_loss = sum(losses) / len(losses) if losses else 0.001
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            # Calculate MACD (simplified)
            ema_12 = sum(prices[:12]) / 12
            ema_26 = sum(prices[:26] if len(prices) >= 26 else prices) / min(26, len(prices))
            macd = ema_12 - ema_26

            # Generate signal
            signal = "hold"
            confidence = 0.0
            reason = "Neutral market"

            # BUY conditions
            buy_score = 0
            if price_vs_sma5 > 0.01:  # Price above short-term SMA
                buy_score += 1
            if price_vs_sma20 > 0.005:  # Price above long-term SMA
                buy_score += 1
            if 30 < rsi < 60:  # RSI in moderate range (not overbought)
                buy_score += 1
            if macd > 0:  # Positive MACD
                buy_score += 1

            # SELL conditions
            sell_score = 0
            if price_vs_sma5 < -0.01:  # Price below short-term SMA
                sell_score += 1
            if price_vs_sma20 < -0.005:  # Price below long-term SMA
                sell_score += 1
            if rsi > 70:  # Overbought
                sell_score += 2  # Higher weight
            if macd < 0:  # Negative MACD
                sell_score += 1

            # Decision logic
            if buy_score >= 3:
                signal = "buy"
                confidence = min(buy_score / 4, 1.0)
                reason = f"Strong buy signal (score: {buy_score}/4, RSI: {rsi:.1f})"
            elif sell_score >= 3:
                signal = "sell"
                confidence = min(sell_score / 5, 1.0)
                reason = f"Strong sell signal (score: {sell_score}/5, RSI: {rsi:.1f})"
            else:
                reason = f"Neutral (buy: {buy_score}, sell: {sell_score}, RSI: {rsi:.1f})"

            return {
                "signal": signal,
                "confidence": confidence,
                "reason": reason,
                "indicators": {
                    "sma_5": sma_5,
                    "sma_10": sma_10,
                    "sma_20": sma_20,
                    "rsi": rsi,
                    "macd": macd,
                    "price_vs_sma5": price_vs_sma5,
                    "price_vs_sma20": price_vs_sma20,
                    "buy_score": buy_score,
                    "sell_score": sell_score
                }
            }

        except Exception as e:
            print(f"[EnhancedAutoTradingEngine] ERROR analyzing {coin_symbol}: {e}")
            return {
                "signal": "hold",
                "confidence": 0.0,
                "reason": f"Analysis error: {e}",
                "indicators": {}
            }

    def execute_buy_order(self, user_id, coin_symbol, current_price, config):
        """
        Execute a buy order with real API call.

        Args:
            user_id: User ID
            coin_symbol: Coin symbol
            current_price: Current market price
            config: User configuration

        Returns:
            dict: Execution result
        """
        try:
            # Calculate order amount
            budget_per_position = config.get('budget_per_position_krw', 10000)
            available_budget = self.position_tracker.get_available_budget(user_id)

            order_amount = min(budget_per_position, available_budget)

            # Check minimum order amount (Upbit minimum: 5,000 KRW)
            if order_amount < 5000:
                return {
                    "success": False,
                    "reason": f"Order amount too small: {order_amount:,.0f} KRW < 5,000 KRW"
                }

            # Check if can open new position
            if not self.position_tracker.can_open_new_position(user_id, order_amount):
                return {
                    "success": False,
                    "reason": "Cannot open new position (budget or max positions)"
                }

            # Calculate quantity
            quantity = order_amount / current_price

            # Execute order via Upbit API
            print(f"[EnhancedAutoTradingEngine] EXECUTING BUY: {coin_symbol} {quantity:.8f} @ {current_price:,.0f} KRW")

            order_result = self.upbit_api.place_order(
                market=coin_symbol,
                side='bid',
                volume=None,
                price=order_amount,  # Market order by total price
                ord_type='price'
            )

            if order_result and 'uuid' in order_result:
                # Open position in tracker
                position_id = self.position_tracker.open_position(
                    user_id=user_id,
                    coin_symbol=coin_symbol,
                    buy_price=current_price,
                    quantity=quantity,
                    order_amount=order_amount
                )

                # Log to database
                self._log_action(user_id, 'buy_executed', coin_symbol, current_price, order_amount,
                               f"Auto buy executed (order: {order_result['uuid']})")

                return {
                    "success": True,
                    "action": "buy",
                    "order_uuid": order_result['uuid'],
                    "position_id": position_id,
                    "amount": order_amount,
                    "quantity": quantity,
                    "price": current_price
                }
            else:
                return {
                    "success": False,
                    "reason": "Order placement failed"
                }

        except Exception as e:
            print(f"[EnhancedAutoTradingEngine] ERROR executing buy: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "reason": f"Execution error: {e}"
            }

    def execute_sell_order(self, user_id, coin_symbol, current_price, reason="auto_signal"):
        """
        Execute a sell order with real API call.

        Args:
            user_id: User ID
            coin_symbol: Coin symbol
            current_price: Current market price
            reason: Sell reason (auto_signal, stop_loss, take_profit)

        Returns:
            dict: Execution result
        """
        try:
            # Get open position
            positions = self.position_tracker.get_open_positions(user_id)
            position = next((p for p in positions if p['coin_symbol'] == coin_symbol), None)

            if not position:
                return {
                    "success": False,
                    "reason": f"No open position for {coin_symbol}"
                }

            quantity = float(position['quantity'])

            # Execute order via Upbit API
            print(f"[EnhancedAutoTradingEngine] EXECUTING SELL: {coin_symbol} {quantity:.8f} @ {current_price:,.0f} KRW (reason: {reason})")

            order_result = self.upbit_api.place_order(
                market=coin_symbol,
                side='ask',
                volume=quantity,
                price=None,
                ord_type='market'
            )

            if order_result and 'uuid' in order_result:
                # Close position in tracker
                profit_loss = self.position_tracker.close_position(
                    user_id=user_id,
                    coin_symbol=coin_symbol,
                    sell_price=current_price,
                    reason=reason
                )

                # Log to database
                self._log_action(user_id, 'sell_executed', coin_symbol, current_price,
                               quantity * current_price,
                               f"Auto sell executed (reason: {reason}, order: {order_result['uuid']})")

                return {
                    "success": True,
                    "action": "sell",
                    "order_uuid": order_result['uuid'],
                    "quantity": quantity,
                    "price": current_price,
                    "profit_loss": profit_loss,
                    "reason": reason
                }
            else:
                return {
                    "success": False,
                    "reason": "Order placement failed"
                }

        except Exception as e:
            print(f"[EnhancedAutoTradingEngine] ERROR executing sell: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "reason": f"Execution error: {e}"
            }

    def check_stop_loss_take_profit(self, user_id):
        """
        Check all open positions for stop-loss or take-profit triggers.

        Args:
            user_id: User ID

        Returns:
            list: List of closed positions
        """
        closed_positions = []

        try:
            # Get all open positions for user
            positions = self.position_tracker.get_open_positions(user_id)

            for position in positions:
                coin_symbol = position['coin_symbol']

                try:
                    # Get current price
                    current_price = self.upbit_api.get_current_price(coin_symbol)
                    if not current_price:
                        continue

                    # Update position with current price
                    self.position_tracker.update_position(user_id, coin_symbol, current_price)

                    # Check exit conditions
                    should_exit, reason = self.position_tracker.check_exit_conditions(
                        user_id, coin_symbol, current_price
                    )

                    if should_exit:
                        print(f"[EnhancedAutoTradingEngine] {reason.upper()} triggered for {coin_symbol}")

                        # Execute sell order
                        result = self.execute_sell_order(user_id, coin_symbol, current_price, reason)

                        if result['success']:
                            closed_positions.append({
                                "coin_symbol": coin_symbol,
                                "reason": reason,
                                "profit_loss": result.get('profit_loss', 0)
                            })

                except Exception as e:
                    print(f"[EnhancedAutoTradingEngine] ERROR checking {coin_symbol}: {e}")
                    continue

            return closed_positions

        except Exception as e:
            print(f"[EnhancedAutoTradingEngine] ERROR checking stop-loss/take-profit: {e}")
            return []

    def run_auto_trading_cycle(self, user_id):
        """
        Run one cycle of auto trading for a user.

        Args:
            user_id: User ID

        Returns:
            dict: Cycle results
        """
        try:
            print(f"\n[EnhancedAutoTradingEngine] === Starting auto trading cycle for user {user_id} ===")

            # Get user config
            config = self.get_user_config(user_id)
            if not config:
                return {"status": "error", "message": "User config not found"}

            if not config.get('auto_trading_enabled', False):
                return {"status": "disabled", "message": "Auto trading disabled for user"}

            results = {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "signals_generated": 0,
                "orders_executed": 0,
                "positions_closed": 0,
                "actions": []
            }

            # Step 1: Check stop-loss and take-profit on existing positions
            closed_positions = self.check_stop_loss_take_profit(user_id)
            results["positions_closed"] = len(closed_positions)
            results["actions"].extend(closed_positions)

            # Step 2: Analyze monitored coins for new signals
            monitored_coins = config.get('monitored_coins', [])

            for coin_symbol in monitored_coins:
                try:
                    # Get current price
                    current_price = self.upbit_api.get_current_price(coin_symbol)
                    if not current_price:
                        continue

                    # Get historical data
                    historical_data = self.upbit_api.get_candles_days(coin_symbol, count=30)
                    if not historical_data:
                        continue

                    # Analyze market
                    analysis = self.analyze_market_conditions(coin_symbol, current_price, historical_data)

                    print(f"[EnhancedAutoTradingEngine] {coin_symbol}: {analysis['signal']} "
                          f"(confidence: {analysis['confidence']:.2f}) - {analysis['reason']}")

                    results["signals_generated"] += 1

                    # Execute based on signal
                    if analysis['signal'] == 'buy' and analysis['confidence'] >= 0.6:
                        result = self.execute_buy_order(user_id, coin_symbol, current_price, config)
                        if result['success']:
                            results["orders_executed"] += 1
                            results["actions"].append(result)

                    elif analysis['signal'] == 'sell' and analysis['confidence'] >= 0.6:
                        result = self.execute_sell_order(user_id, coin_symbol, current_price, "auto_signal")
                        if result['success']:
                            results["orders_executed"] += 1
                            results["actions"].append(result)

                except Exception as e:
                    print(f"[EnhancedAutoTradingEngine] ERROR processing {coin_symbol}: {e}")
                    continue

            print(f"[EnhancedAutoTradingEngine] Cycle complete: {results['signals_generated']} signals, "
                  f"{results['orders_executed']} orders, {results['positions_closed']} closed")

            results["status"] = "success"
            return results

        except Exception as e:
            print(f"[EnhancedAutoTradingEngine] ERROR in trading cycle: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def _log_action(self, user_id, action, coin_symbol, price, amount, reason):
        """Log trading action to database."""
        session = get_db_session()
        try:
            log = SwingTradingLog(
                user_id=user_id,
                action=action,
                coin_symbol=coin_symbol,
                price=Decimal(str(price)),
                amount=Decimal(str(amount)),
                reason=reason
            )
            session.add(log)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"[EnhancedAutoTradingEngine] ERROR logging action: {e}")
        finally:
            session.close()

    def get_user_statistics(self, user_id):
        """
        Get trading statistics for a user.

        Args:
            user_id: User ID

        Returns:
            dict: Statistics
        """
        try:
            stats = self.position_tracker.get_statistics(user_id)

            # Add open positions info
            open_positions = self.position_tracker.get_open_positions(user_id)
            stats['open_positions_count'] = len(open_positions)
            stats['open_positions_value'] = sum(float(p.get('current_value', 0)) for p in open_positions)

            return stats

        except Exception as e:
            print(f"[EnhancedAutoTradingEngine] ERROR getting statistics: {e}")
            return {}
