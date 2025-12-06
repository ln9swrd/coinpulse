"""
Database Position Tracker Module

Manages swing trading positions using database instead of JSON files.
Supports 100+ concurrent users with thread-safe operations.
"""

from datetime import datetime, timedelta
from decimal import Decimal
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.database import get_db_session, User, UserConfig, SwingPosition, SwingPositionHistory, SwingTradingLog


class DBPositionTracker:
    """
    Database-backed position tracker for swing trading.

    Features:
    - Multi-user support with user_id parameter
    - Thread-safe database operations
    - Full position lifecycle management
    - Comprehensive logging
    - Configurable per-user settings
    """

    def __init__(self):
        """Initialize the position tracker."""
        print("[DBPositionTracker] Initialized (multi-user mode)")

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
            print(f"[DBPositionTracker] ERROR getting config for user {user_id}: {e}")
            return None
        finally:
            session.close()

    def open_position(self, user_id, coin_symbol, buy_price, quantity, order_amount):
        """
        Open a new position for a user.

        Args:
            user_id: User ID
            coin_symbol: Coin symbol (e.g., 'KRW-BTC')
            buy_price: Buy price
            quantity: Quantity purchased
            order_amount: Total order amount in KRW

        Returns:
            int: Position ID if successful, None otherwise
        """
        session = get_db_session()
        try:
            # Check if position already exists for this user and coin
            existing = session.query(SwingPosition).filter_by(
                user_id=user_id,
                coin_symbol=coin_symbol,
                status='open'
            ).first()

            if existing:
                print(f"[DBPositionTracker] User {user_id} already has open position for {coin_symbol}")
                return None

            # Create new position
            position = SwingPosition(
                user_id=user_id,
                coin_symbol=coin_symbol,
                buy_price=Decimal(str(buy_price)),
                quantity=Decimal(str(quantity)),
                order_amount=Decimal(str(order_amount)),
                buy_time=datetime.utcnow(),
                status='open',
                current_price=Decimal(str(buy_price)),
                current_value=Decimal(str(order_amount)),
                profit_loss=Decimal('0'),
                profit_loss_percent=Decimal('0'),
                highest_price=Decimal(str(buy_price)),
                lowest_price=Decimal(str(buy_price))
            )

            session.add(position)

            # Log the action
            log = SwingTradingLog(
                user_id=user_id,
                action='buy_executed',
                coin_symbol=coin_symbol,
                price=Decimal(str(buy_price)),
                amount=Decimal(str(order_amount)),
                reason='New position opened',
                details={'quantity': float(quantity)}
            )

            session.add(log)
            session.commit()

            position_id = position.position_id
            print(f"[DBPositionTracker] User {user_id} opened position {position_id}: {coin_symbol} @ {buy_price:,.0f} KRW")

            return position_id

        except Exception as e:
            session.rollback()
            print(f"[DBPositionTracker] ERROR opening position for user {user_id}: {e}")
            return None
        finally:
            session.close()

    def update_position(self, user_id, coin_symbol, current_price):
        """
        Update position with current price.

        Args:
            user_id: User ID
            coin_symbol: Coin symbol
            current_price: Current market price

        Returns:
            dict: Updated position data or None
        """
        session = get_db_session()
        try:
            position = session.query(SwingPosition).filter_by(
                user_id=user_id,
                coin_symbol=coin_symbol,
                status='open'
            ).first()

            if not position:
                return None

            # Update prices
            current_price_decimal = Decimal(str(current_price))
            position.current_price = current_price_decimal
            position.current_value = current_price_decimal * position.quantity

            # Update highest/lowest
            if current_price_decimal > position.highest_price:
                position.highest_price = current_price_decimal

            if current_price_decimal < position.lowest_price:
                position.lowest_price = current_price_decimal

            # Calculate P/L
            position.profit_loss = position.current_value - position.order_amount
            if position.order_amount > 0:
                position.profit_loss_percent = (position.profit_loss / position.order_amount) * 100

            session.commit()

            return position.to_dict()

        except Exception as e:
            session.rollback()
            print(f"[DBPositionTracker] ERROR updating position for user {user_id}: {e}")
            return None
        finally:
            session.close()

    def close_position(self, user_id, coin_symbol, sell_price, reason='manual'):
        """
        Close a position.

        Args:
            user_id: User ID
            coin_symbol: Coin symbol
            sell_price: Sell price
            reason: Close reason

        Returns:
            float: Profit/loss amount or None
        """
        session = get_db_session()
        try:
            # Get open position
            position = session.query(SwingPosition).filter_by(
                user_id=user_id,
                coin_symbol=coin_symbol,
                status='open'
            ).first()

            if not position:
                print(f"[DBPositionTracker] No open position found for user {user_id} coin {coin_symbol}")
                return None

            # Calculate final values
            sell_price_decimal = Decimal(str(sell_price))
            sell_amount = sell_price_decimal * position.quantity
            profit_loss = sell_amount - position.order_amount
            profit_loss_percent = (profit_loss / position.order_amount) * 100 if position.order_amount > 0 else 0

            # Calculate holding time
            holding_time = datetime.utcnow() - position.buy_time
            holding_hours = Decimal(str(holding_time.total_seconds() / 3600))
            holding_days = int(holding_time.days)

            # Create history record
            history = SwingPositionHistory(
                user_id=user_id,
                position_id=position.position_id,
                coin_symbol=coin_symbol,
                buy_price=position.buy_price,
                sell_price=sell_price_decimal,
                quantity=position.quantity,
                buy_amount=position.order_amount,
                sell_amount=sell_amount,
                profit_loss=profit_loss,
                profit_loss_percent=profit_loss_percent,
                buy_time=position.buy_time,
                sell_time=datetime.utcnow(),
                holding_hours=holding_hours,
                holding_days=holding_days,
                close_reason=reason
            )

            session.add(history)

            # Mark position as closed
            position.status = 'closed'

            # Log the action
            log = SwingTradingLog(
                user_id=user_id,
                action='sell_executed',
                coin_symbol=coin_symbol,
                price=sell_price_decimal,
                amount=sell_amount,
                reason=reason,
                details={
                    'profit_loss': float(profit_loss),
                    'profit_loss_percent': float(profit_loss_percent),
                    'holding_hours': float(holding_hours)
                }
            )

            session.add(log)
            session.commit()

            profit_loss_float = float(profit_loss)
            print(f"[DBPositionTracker] User {user_id} closed position: {coin_symbol} P/L {profit_loss_float:,.0f} KRW ({float(profit_loss_percent):.2f}%)")

            return profit_loss_float

        except Exception as e:
            session.rollback()
            print(f"[DBPositionTracker] ERROR closing position for user {user_id}: {e}")
            return None
        finally:
            session.close()

    def check_exit_conditions(self, user_id, coin_symbol, current_price):
        """
        Check if position should be closed based on exit conditions.

        Args:
            user_id: User ID
            coin_symbol: Coin symbol
            current_price: Current market price

        Returns:
            tuple: (should_exit, reason) or (False, None)
        """
        session = get_db_session()
        try:
            # Get position
            position = session.query(SwingPosition).filter_by(
                user_id=user_id,
                coin_symbol=coin_symbol,
                status='open'
            ).first()

            if not position:
                return False, None

            # Get user config
            config = session.query(UserConfig).filter_by(user_id=user_id).first()
            if not config:
                return False, None

            # Calculate current P/L percent
            if position.order_amount == 0:
                return False, None

            current_value = Decimal(str(current_price)) * position.quantity
            profit_loss = current_value - position.order_amount
            pl_percent = float((profit_loss / position.order_amount) * 100)

            # Check emergency stop loss (3%)
            emergency_threshold = -float(config.emergency_stop_loss) * 100  # Convert to percentage
            if pl_percent <= emergency_threshold:
                return True, 'emergency_stop'

            # Check regular stop loss (3-5%)
            stop_loss_threshold = -float(config.stop_loss_min) * 100
            if pl_percent <= stop_loss_threshold:
                return True, 'stop_loss'

            # Check take profit (8-15%)
            take_profit_threshold = float(config.take_profit_min) * 100
            if pl_percent >= take_profit_threshold:
                return True, 'take_profit'

            # Check holding period (3 days)
            holding_time = datetime.utcnow() - position.buy_time
            if holding_time.days >= config.holding_period_days:
                if config.force_sell_after_period:
                    return True, 'holding_period'

            return False, None

        except Exception as e:
            print(f"[DBPositionTracker] ERROR checking exit conditions for user {user_id}: {e}")
            return False, None
        finally:
            session.close()

    def get_open_positions(self, user_id):
        """
        Get all open positions for a user.

        Args:
            user_id: User ID

        Returns:
            list: List of position dictionaries
        """
        session = get_db_session()
        try:
            positions = session.query(SwingPosition).filter_by(
                user_id=user_id,
                status='open'
            ).all()

            return [pos.to_dict() for pos in positions]

        except Exception as e:
            print(f"[DBPositionTracker] ERROR getting positions for user {user_id}: {e}")
            return []
        finally:
            session.close()

    def get_available_budget(self, user_id):
        """
        Calculate available budget for new positions.

        Args:
            user_id: User ID

        Returns:
            float: Available budget in KRW
        """
        session = get_db_session()
        try:
            # Get user config
            config = session.query(UserConfig).filter_by(user_id=user_id).first()
            if not config:
                return 0

            total_budget = config.total_budget_krw

            # Get total used budget
            positions = session.query(SwingPosition).filter_by(
                user_id=user_id,
                status='open'
            ).all()

            used_budget = sum(float(pos.order_amount) for pos in positions)
            available = total_budget - used_budget

            return max(0, available)

        except Exception as e:
            print(f"[DBPositionTracker] ERROR calculating budget for user {user_id}: {e}")
            return 0
        finally:
            session.close()

    def can_open_new_position(self, user_id, order_amount):
        """
        Check if user can open a new position.

        Args:
            user_id: User ID
            order_amount: Proposed order amount

        Returns:
            bool: True if can open position
        """
        session = get_db_session()
        try:
            # Get user config
            config = session.query(UserConfig).filter_by(user_id=user_id).first()
            if not config:
                return False

            # Check max concurrent positions
            open_positions_count = session.query(SwingPosition).filter_by(
                user_id=user_id,
                status='open'
            ).count()

            if open_positions_count >= config.max_concurrent_positions:
                print(f"[DBPositionTracker] User {user_id} reached max positions ({config.max_concurrent_positions})")
                return False

            # Check budget
            available = self.get_available_budget(user_id)
            if order_amount > available:
                print(f"[DBPositionTracker] User {user_id} insufficient budget: {available:,.0f} KRW < {order_amount:,.0f} KRW")
                return False

            return True

        except Exception as e:
            print(f"[DBPositionTracker] ERROR checking can open for user {user_id}: {e}")
            return False
        finally:
            session.close()

    def get_statistics(self, user_id):
        """
        Get trading statistics for a user.

        Args:
            user_id: User ID

        Returns:
            dict: Statistics summary
        """
        session = get_db_session()
        try:
            # Get closed positions
            history = session.query(SwingPositionHistory).filter_by(user_id=user_id).all()

            if not history:
                return {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0,
                    'total_profit': 0,
                    'avg_profit_per_trade': 0
                }

            total_trades = len(history)
            winning_trades = len([h for h in history if float(h.profit_loss) > 0])
            losing_trades = len([h for h in history if float(h.profit_loss) < 0])
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0

            total_profit = sum(float(h.profit_loss) for h in history)
            avg_profit = total_profit / total_trades if total_trades > 0 else 0

            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'total_profit': total_profit,
                'avg_profit_per_trade': avg_profit
            }

        except Exception as e:
            print(f"[DBPositionTracker] ERROR getting statistics for user {user_id}: {e}")
            return {}
        finally:
            session.close()
