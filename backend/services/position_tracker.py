"""
⚠️ LEGACY - Position Tracker (JSON-based, Single-user)

DEPRECATED: Use 'db_position_tracker.py' instead.

This module uses JSON file storage and is designed for single-user environments.
For multi-user production systems with database support, please use:
- backend/services/db_position_tracker.py

Manages open positions for swing trading strategy.
Tracks buy/sell history, holding periods, and profit/loss.
"""

import json
import os
from datetime import datetime, timedelta


class PositionTracker:
    """
    Tracks open trading positions and their status.

    Features:
    - Position lifecycle management (open/close)
    - Holding period tracking
    - Profit/loss calculation
    - Emergency stop detection
    """

    def __init__(self, config_file='swing_trading_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.positions_file = 'active_positions.json'
        self.history_file = 'position_history.json'
        self.positions = self.load_positions()
        self.history = self.load_history()

    def load_config(self):
        """Load swing trading configuration."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"[PositionTracker] ERROR loading config: {e}")
            return {}

    def load_positions(self):
        """Load active positions from file."""
        try:
            if os.path.exists(self.positions_file):
                with open(self.positions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"[PositionTracker] ERROR loading positions: {e}")
            return {}

    def load_history(self):
        """Load position history from file."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"[PositionTracker] ERROR loading history: {e}")
            return []

    def save_positions(self):
        """Save active positions to file."""
        try:
            with open(self.positions_file, 'w', encoding='utf-8') as f:
                json.dump(self.positions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[PositionTracker] ERROR saving positions: {e}")

    def save_history(self):
        """Save position history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[PositionTracker] ERROR saving history: {e}")

    def open_position(self, coin_symbol, buy_price, quantity, order_amount):
        """
        Open a new position.

        Args:
            coin_symbol: Coin symbol (e.g., 'KRW-XRP')
            buy_price: Buy price in KRW
            quantity: Quantity purchased
            order_amount: Total order amount in KRW

        Returns:
            Position ID if successful, None otherwise
        """
        try:
            # Check if position already exists
            if coin_symbol in self.positions:
                print(f"[PositionTracker] Position already exists for {coin_symbol}")
                return None

            # Check max concurrent positions
            max_positions = self.config.get('budget', {}).get('max_concurrent_positions', 3)
            if len(self.positions) >= max_positions:
                print(f"[PositionTracker] Max positions ({max_positions}) reached")
                return None

            # Create position
            position_id = f"{coin_symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            self.positions[coin_symbol] = {
                "position_id": position_id,
                "coin_symbol": coin_symbol,
                "buy_price": buy_price,
                "quantity": quantity,
                "order_amount": order_amount,
                "buy_time": datetime.now().isoformat(),
                "status": "open",
                "current_price": buy_price,
                "current_value": order_amount,
                "profit_loss": 0,
                "profit_loss_percent": 0,
                "holding_days": 0,
                "highest_price": buy_price,
                "lowest_price": buy_price,
                "take_profit_triggered": False,
                "stop_loss_triggered": False
            }

            self.save_positions()

            print(f"[PositionTracker] ✅ Opened position: {coin_symbol} @ {buy_price:,.0f} KRW")
            print(f"[PositionTracker] Quantity: {quantity}, Amount: {order_amount:,.0f} KRW")

            return position_id

        except Exception as e:
            print(f"[PositionTracker] ERROR opening position: {e}")
            return None

    def close_position(self, coin_symbol, sell_price, reason="manual"):
        """
        Close an existing position.

        Args:
            coin_symbol: Coin symbol
            sell_price: Sell price in KRW
            reason: Reason for closing (take_profit, stop_loss, manual, holding_period)

        Returns:
            Profit/loss amount if successful, None otherwise
        """
        try:
            if coin_symbol not in self.positions:
                print(f"[PositionTracker] No position found for {coin_symbol}")
                return None

            position = self.positions[coin_symbol]

            # Calculate profit/loss
            buy_price = position['buy_price']
            quantity = position['quantity']
            buy_amount = position['order_amount']
            sell_amount = sell_price * quantity
            profit_loss = sell_amount - buy_amount
            profit_loss_percent = (profit_loss / buy_amount) * 100

            # Update position for history
            position['sell_price'] = sell_price
            position['sell_time'] = datetime.now().isoformat()
            position['sell_amount'] = sell_amount
            position['profit_loss'] = profit_loss
            position['profit_loss_percent'] = profit_loss_percent
            position['close_reason'] = reason
            position['status'] = 'closed'

            # Calculate holding duration
            buy_time = datetime.fromisoformat(position['buy_time'])
            sell_time = datetime.now()
            holding_duration = sell_time - buy_time
            position['holding_hours'] = holding_duration.total_seconds() / 3600
            position['holding_days'] = holding_duration.days

            # Add to history
            self.history.append(position)
            self.save_history()

            # Remove from active positions
            del self.positions[coin_symbol]
            self.save_positions()

            print(f"[PositionTracker] 🔔 Closed position: {coin_symbol}")
            print(f"[PositionTracker] Buy: {buy_price:,.0f} → Sell: {sell_price:,.0f}")
            print(f"[PositionTracker] P/L: {profit_loss:,.0f} KRW ({profit_loss_percent:+.2f}%)")
            print(f"[PositionTracker] Reason: {reason}")

            return profit_loss

        except Exception as e:
            print(f"[PositionTracker] ERROR closing position: {e}")
            return None

    def update_position(self, coin_symbol, current_price):
        """
        Update position with current price.

        Args:
            coin_symbol: Coin symbol
            current_price: Current market price

        Returns:
            Updated position dict if successful, None otherwise
        """
        try:
            if coin_symbol not in self.positions:
                return None

            position = self.positions[coin_symbol]

            # Update current values
            position['current_price'] = current_price
            position['current_value'] = current_price * position['quantity']
            position['profit_loss'] = position['current_value'] - position['order_amount']
            position['profit_loss_percent'] = (position['profit_loss'] / position['order_amount']) * 100

            # Update highest/lowest
            if current_price > position['highest_price']:
                position['highest_price'] = current_price
            if current_price < position['lowest_price']:
                position['lowest_price'] = current_price

            # Update holding days
            buy_time = datetime.fromisoformat(position['buy_time'])
            holding_duration = datetime.now() - buy_time
            position['holding_days'] = holding_duration.days
            position['holding_hours'] = holding_duration.total_seconds() / 3600

            self.save_positions()

            return position

        except Exception as e:
            print(f"[PositionTracker] ERROR updating position: {e}")
            return None

    def check_exit_conditions(self, coin_symbol, current_price):
        """
        Check if position should be closed based on profit/loss targets.

        Args:
            coin_symbol: Coin symbol
            current_price: Current market price

        Returns:
            (should_exit, reason) tuple
        """
        try:
            if coin_symbol not in self.positions:
                return (False, None)

            position = self.positions[coin_symbol]
            buy_price = position['buy_price']
            profit_percent = ((current_price - buy_price) / buy_price) * 100

            # Get profit/loss targets from config
            profit_targets = self.config.get('profit_targets', {})
            take_profit_min = profit_targets.get('take_profit_min', 0.08) * 100  # 8%
            take_profit_max = profit_targets.get('take_profit_max', 0.15) * 100  # 15%
            stop_loss_min = profit_targets.get('stop_loss_min', 0.03) * 100      # 3%
            stop_loss_max = profit_targets.get('stop_loss_max', 0.05) * 100      # 5%

            # Check take profit (8-15%)
            if profit_percent >= take_profit_min:
                print(f"[PositionTracker] 🎯 Take profit triggered: {coin_symbol} (+{profit_percent:.2f}%)")
                return (True, 'take_profit')

            # Check stop loss (3-5%)
            if profit_percent <= -stop_loss_min:
                print(f"[PositionTracker] 🛑 Stop loss triggered: {coin_symbol} ({profit_percent:.2f}%)")
                return (True, 'stop_loss')

            # Check emergency stop (3%)
            emergency_stop = self.config.get('risk_management', {}).get('emergency_stop_loss_per_coin', 0.03) * 100
            if profit_percent <= -emergency_stop:
                print(f"[PositionTracker] 🚨 EMERGENCY STOP: {coin_symbol} ({profit_percent:.2f}%)")
                return (True, 'emergency_stop')

            # Check holding period (3 days)
            holding_period_days = self.config.get('holding_strategy', {}).get('holding_period_days', 3)
            force_sell = self.config.get('holding_strategy', {}).get('force_sell_after_period', False)

            if force_sell and position['holding_days'] >= holding_period_days:
                print(f"[PositionTracker] ⏰ Holding period reached: {coin_symbol} ({position['holding_days']} days)")
                return (True, 'holding_period')

            return (False, None)

        except Exception as e:
            print(f"[PositionTracker] ERROR checking exit conditions: {e}")
            return (False, None)

    def get_position_summary(self):
        """Get summary of all active positions."""
        summary = {
            "total_positions": len(self.positions),
            "total_invested": sum(p['order_amount'] for p in self.positions.values()),
            "total_current_value": sum(p['current_value'] for p in self.positions.values()),
            "total_profit_loss": sum(p['profit_loss'] for p in self.positions.values()),
            "positions": list(self.positions.values())
        }

        if summary['total_invested'] > 0:
            summary['total_profit_loss_percent'] = (summary['total_profit_loss'] / summary['total_invested']) * 100
        else:
            summary['total_profit_loss_percent'] = 0

        return summary

    def get_available_budget(self):
        """Calculate remaining budget for new positions."""
        total_budget = self.config.get('budget', {}).get('total_budget_krw', 40000)
        invested = sum(p['order_amount'] for p in self.positions.values())
        return total_budget - invested

    def can_open_new_position(self, required_amount):
        """Check if new position can be opened."""
        # Check budget
        available = self.get_available_budget()
        if required_amount > available:
            print(f"[PositionTracker] Insufficient budget: {available:,.0f} KRW available, {required_amount:,.0f} required")
            return False

        # Check max positions
        max_positions = self.config.get('budget', {}).get('max_concurrent_positions', 3)
        if len(self.positions) >= max_positions:
            print(f"[PositionTracker] Max positions reached: {len(self.positions)}/{max_positions}")
            return False

        # Check min order amount
        min_order = self.config.get('budget', {}).get('min_order_amount', 6000)
        if required_amount < min_order:
            print(f"[PositionTracker] Order amount too small: {required_amount:,.0f} < {min_order:,.0f}")
            return False

        return True

    def get_statistics(self):
        """Get trading statistics from history."""
        if not self.history:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_profit_loss": 0,
                "avg_profit_loss": 0,
                "best_trade": None,
                "worst_trade": None
            }

        wins = [p for p in self.history if p.get('profit_loss', 0) > 0]
        losses = [p for p in self.history if p.get('profit_loss', 0) <= 0]

        total_pl = sum(p.get('profit_loss', 0) for p in self.history)
        avg_pl = total_pl / len(self.history) if self.history else 0

        best = max(self.history, key=lambda p: p.get('profit_loss', 0))
        worst = min(self.history, key=lambda p: p.get('profit_loss', 0))

        return {
            "total_trades": len(self.history),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": (len(wins) / len(self.history) * 100) if self.history else 0,
            "total_profit_loss": total_pl,
            "avg_profit_loss": avg_pl,
            "best_trade": {
                "coin": best.get('coin_symbol'),
                "profit": best.get('profit_loss'),
                "percent": best.get('profit_loss_percent')
            },
            "worst_trade": {
                "coin": worst.get('coin_symbol'),
                "profit": worst.get('profit_loss'),
                "percent": worst.get('profit_loss_percent')
            }
        }
