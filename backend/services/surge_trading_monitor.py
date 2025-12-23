"""
급등 예측 실시간 자동매매 모니터링 시스템

급등 신호 발생 시:
1. 즉시 매수 주문 실행
2. 실시간 가격 모니터링 시작
3. 목표가 도달 → 즉시 매도 (익절)
4. 손절가 도달 → 즉시 매도 (손절)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
import time
from datetime import datetime
from typing import Dict, List
from sqlalchemy import text

from backend.common import UpbitAPI, load_api_keys
from backend.database.connection import get_db_session
from backend.services.auto_trading_service import AutoTradingService

# Telegram notification support
try:
    import asyncio
    from backend.services.telegram_bot import SurgeTelegramBot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

logging.basicConfig(
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SurgeTradingMonitor:
    """
    급등 예측 실시간 자동매매 모니터링

    핵심 기능:
    - 급등 신호 발생 시 즉시 매수
    - 실시간 가격 모니터링 (5초 주기)
    - 목표가 도달 시 자동 익절
    - 손절가 도달 시 자동 손절
    """

    def __init__(self, user_id: int, check_interval: int = 5):
        """
        Initialize surge trading monitor

        Args:
            user_id: User ID for trading
            check_interval: Price check interval in seconds (default: 5)
        """
        self.user_id = user_id
        self.check_interval = check_interval

        # Initialize Upbit API
        access_key, secret_key = load_api_keys()
        self.upbit_api = UpbitAPI(access_key, secret_key)

        # Initialize auto trading service
        self.trading_service = AutoTradingService(user_id)

        # Initialize telegram bot (optional)
        self.telegram_enabled = False
        self.telegram_bot = None
        try:
            if TELEGRAM_AVAILABLE:
                token = os.getenv('TELEGRAM_BOT_TOKEN')
                if token:
                    self.telegram_bot = SurgeTelegramBot(token)
                    self.telegram_enabled = True
                    logger.info("[SurgeTradingMonitor] Telegram bot enabled")
        except Exception as e:
            logger.warning(f"[SurgeTradingMonitor] Telegram bot initialization failed: {e}")

        logger.info(f"[SurgeTradingMonitor] Initialized for user {user_id} (interval: {check_interval}s)")

    def _send_telegram_notification(self, message: str, user_telegram_id: int = None):
        """
        Send telegram notification (sync wrapper for async bot)

        Args:
            message: Message text to send
            user_telegram_id: User's telegram chat ID
        """
        if not self.telegram_enabled or not self.telegram_bot:
            return

        try:
            # Get user's telegram chat ID from database if not provided
            if not user_telegram_id:
                with get_db_session() as session:
                    query = text("SELECT telegram_chat_id FROM users WHERE id = :user_id")
                    result = session.execute(query, {'user_id': self.user_id}).scalar()
                    user_telegram_id = result

            if not user_telegram_id:
                return

            # Run async telegram send in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self.telegram_bot.bot.send_message(
                    chat_id=user_telegram_id,
                    text=message,
                    parse_mode='Markdown'
                )
            )
            loop.close()

        except Exception as e:
            logger.error(f"[SurgeTradingMonitor] Failed to send telegram notification: {e}")

    def _send_buy_notification(self, market: str, entry_price: float, target_price: float, stop_loss_price: float, confidence: float):
        """Send telegram notification for buy execution"""
        message = f"""
🚀 *급등 예측 매수 실행*

*코인*: {market}
*진입가*: {entry_price:,.0f}원
*목표가*: {target_price:,.0f}원 (+{((target_price - entry_price) / entry_price * 100):.1f}%)
*손절가*: {stop_loss_price:,.0f}원 ({((stop_loss_price - entry_price) / entry_price * 100):.1f}%)
*신뢰도*: {confidence * 100:.0f}%

📊 실시간 모니터링을 시작합니다.
        """
        self._send_telegram_notification(message)

    def _send_sell_notification(self, market: str, entry_price: float, sell_price: float, profit_pct: float, status: str):
        """Send telegram notification for sell execution"""
        if status == 'win':
            emoji = "✅"
            title = "익절 성공"
        elif status == 'lose':
            emoji = "⚠️"
            title = "손절 실행"
        else:
            emoji = "⚪"
            title = "포지션 청산"

        message = f"""
{emoji} *{title}*

*코인*: {market}
*매수가*: {entry_price:,.0f}원
*매도가*: {sell_price:,.0f}원
*수익률*: {profit_pct:+.2f}%
*손익*: {int((sell_price - entry_price)):+,}원

{'🎉 목표 달성!' if status == 'win' else ''}
        """
        self._send_telegram_notification(message)

    def get_active_surge_positions(self) -> List[Dict]:
        """
        Get active surge trading positions

        Returns:
            List of active positions from surge signals
        """
        try:
            with get_db_session() as session:
                query = text("""
                    SELECT
                        sa.id as alert_id,
                        sa.market,
                        sa.coin,
                        sa.entry_price,
                        sa.target_price,
                        sa.stop_loss_price,
                        sa.confidence,
                        sa.sent_at,
                        sp.position_id,
                        sp.quantity as amount,
                        sp.buy_price as actual_entry_price,
                        sp.status as position_status
                    FROM surge_alerts sa
                    JOIN swing_positions sp ON sa.id = sp.surge_alert_id
                    WHERE sa.user_id = :user_id
                      AND sa.status = 'pending'
                      AND sp.status = 'active'
                      AND sp.position_type = 'surge'
                      AND sa.auto_traded = true
                    ORDER BY sa.sent_at DESC
                """)

                result = session.execute(query, {'user_id': self.user_id})
                positions = [dict(row._mapping) for row in result]

                return positions

        except Exception as e:
            logger.error(f"[SurgeTradingMonitor] Error getting active positions: {e}")
            return []

    def check_position_and_execute(self, position: Dict) -> bool:
        """
        Check position price and execute take-profit or stop-loss

        Args:
            position: Position data with entry/target/stop prices

        Returns:
            True if position was closed (sold), False if still open
        """
        try:
            market = position['market']
            position_id = position['position_id']
            alert_id = position['alert_id']

            entry_price = position['actual_entry_price']
            target_price = position['target_price']
            stop_loss_price = position['stop_loss_price']

            # Get current price
            current_price = self.upbit_api.get_current_price(market)
            if not current_price:
                logger.warning(f"[SurgeTradingMonitor] Could not get price for {market}")
                return False

            # Calculate profit/loss percentage
            profit_pct = ((current_price - entry_price) / entry_price) * 100

            # Check for take-profit (target reached)
            if current_price >= target_price:
                logger.info(
                    f"[SurgeTradingMonitor] TARGET HIT! {market} "
                    f"Entry: {entry_price:,} -> Current: {current_price:,} "
                    f"(+{profit_pct:.2f}%) - SELLING NOW"
                )

                # Execute sell order
                sell_result = self.trading_service.execute_sell_order(
                    market=market,
                    amount=position['amount'],
                    reason='take_profit'
                )

                if sell_result['success']:
                    # Get actual executed price from sell order
                    actual_sell_price = sell_result.get('executed_price', current_price)

                    # Calculate ACTUAL profit/loss based on executed prices
                    actual_profit_loss = actual_sell_price - entry_price
                    actual_profit_pct = (actual_profit_loss / entry_price) * 100

                    # Determine status based on ACTUAL profit/loss
                    if actual_profit_pct > 0:
                        status = 'win'
                        logger.info(f"[SurgeTradingMonitor] WIN: {market} (+{actual_profit_pct:.2f}%)")
                    elif actual_profit_pct < 0:
                        status = 'lose'
                        logger.warning(f"[SurgeTradingMonitor] LOSE: {market} ({actual_profit_pct:.2f}%)")
                    else:
                        status = 'neutral'
                        logger.info(f"[SurgeTradingMonitor] NEUTRAL: {market} (0.0%)")

                    # Update surge_alert with actual profit/loss
                    self._update_surge_alert_status(
                        alert_id=alert_id,
                        status=status,
                        profit_loss_pct=actual_profit_pct,
                        closed_at=datetime.now()
                    )

                    logger.info(
                        f"[SurgeTradingMonitor] Sell executed: {market} "
                        f"(Buy: {entry_price:,} -> Sell: {actual_sell_price:,}, "
                        f"P/L: {actual_profit_pct:+.2f}%)"
                    )

                    # Send telegram notification
                    self._send_sell_notification(market, entry_price, actual_sell_price, actual_profit_pct, status)

                    return True
                else:
                    logger.error(f"[SurgeTradingMonitor] Sell order failed: {sell_result.get('error')}")
                    return False

            # Check for stop-loss (stop hit)
            elif current_price <= stop_loss_price:
                logger.warning(
                    f"[SurgeTradingMonitor] STOP-LOSS HIT! {market} "
                    f"Entry: {entry_price:,} -> Current: {current_price:,} "
                    f"({profit_pct:.2f}%) - SELLING NOW"
                )

                # Execute sell order
                sell_result = self.trading_service.execute_sell_order(
                    market=market,
                    amount=position['amount'],
                    reason='stop_loss'
                )

                if sell_result['success']:
                    # Get actual executed price from sell order
                    actual_sell_price = sell_result.get('executed_price', current_price)

                    # Calculate ACTUAL profit/loss based on executed prices
                    actual_profit_loss = actual_sell_price - entry_price
                    actual_profit_pct = (actual_profit_loss / entry_price) * 100

                    # Determine status based on ACTUAL profit/loss
                    if actual_profit_pct > 0:
                        status = 'win'
                        logger.info(f"[SurgeTradingMonitor] WIN: {market} (+{actual_profit_pct:.2f}%)")
                    elif actual_profit_pct < 0:
                        status = 'lose'
                        logger.warning(f"[SurgeTradingMonitor] LOSE: {market} ({actual_profit_pct:.2f}%)")
                    else:
                        status = 'neutral'
                        logger.info(f"[SurgeTradingMonitor] NEUTRAL: {market} (0.0%)")

                    # Update surge_alert with actual profit/loss
                    self._update_surge_alert_status(
                        alert_id=alert_id,
                        status=status,
                        profit_loss_pct=actual_profit_pct,
                        closed_at=datetime.now()
                    )

                    logger.info(
                        f"[SurgeTradingMonitor] Sell executed: {market} "
                        f"(Buy: {entry_price:,} -> Sell: {actual_sell_price:,}, "
                        f"P/L: {actual_profit_pct:+.2f}%)"
                    )

                    # Send telegram notification
                    self._send_sell_notification(market, entry_price, actual_sell_price, actual_profit_pct, status)

                    return True
                else:
                    logger.error(f"[SurgeTradingMonitor] Sell order failed: {sell_result.get('error')}")
                    return False

            else:
                # Price is between stop-loss and target - keep monitoring
                logger.debug(
                    f"[SurgeTradingMonitor] Monitoring {market}: "
                    f"{current_price:,} ({profit_pct:+.2f}%) "
                    f"[Stop: {stop_loss_price:,}, Target: {target_price:,}]"
                )
                return False

        except Exception as e:
            logger.error(f"[SurgeTradingMonitor] Error checking position {position.get('position_id')}: {e}")
            return False

    def _update_surge_alert_status(self, alert_id: int, status: str, profit_loss_pct: float, closed_at: datetime):
        """
        Update surge_alert status after position is closed

        Args:
            alert_id: Surge alert ID
            status: New status ('win' or 'lose')
            profit_loss_pct: Profit/loss percentage
            closed_at: Timestamp when position was closed
        """
        try:
            with get_db_session() as session:
                update_query = text("""
                    UPDATE surge_alerts
                    SET
                        status = :status,
                        profit_loss_percent = :profit_loss_pct,
                        closed_at = :closed_at
                    WHERE id = :alert_id
                """)

                session.execute(update_query, {
                    'alert_id': alert_id,
                    'status': status,
                    'profit_loss_pct': profit_loss_pct,
                    'closed_at': closed_at
                })
                session.commit()

                logger.info(f"[SurgeTradingMonitor] Updated surge_alert {alert_id} to '{status}'")

        except Exception as e:
            logger.error(f"[SurgeTradingMonitor] Failed to update surge_alert {alert_id}: {e}")

    def run_monitor_cycle(self) -> Dict[str, int]:
        """
        Run one monitoring cycle

        Returns:
            Statistics: {total, checked, closed}
        """
        logger.info("[SurgeTradingMonitor] Starting monitor cycle...")

        # Get active positions
        positions = self.get_active_surge_positions()

        if not positions:
            logger.info("[SurgeTradingMonitor] No active surge positions to monitor")
            return {'total': 0, 'checked': 0, 'closed': 0}

        logger.info(f"[SurgeTradingMonitor] Monitoring {len(positions)} active positions")

        # Check each position
        stats = {'total': len(positions), 'checked': 0, 'closed': 0}

        for position in positions:
            try:
                closed = self.check_position_and_execute(position)
                stats['checked'] += 1

                if closed:
                    stats['closed'] += 1

                # Rate limit to avoid API throttling
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"[SurgeTradingMonitor] Error processing position {position['position_id']}: {e}")
                continue

        logger.info(
            f"[SurgeTradingMonitor] Cycle complete - "
            f"Total: {stats['total']}, Checked: {stats['checked']}, Closed: {stats['closed']}"
        )

        return stats

    def run_monitor_loop(self):
        """
        Run continuous monitoring loop

        Checks active positions every N seconds (default: 5s)
        """
        logger.info(f"[SurgeTradingMonitor] Starting monitor loop (interval: {self.check_interval}s)...")

        while True:
            try:
                # Run one cycle
                self.run_monitor_cycle()

                # Wait before next cycle
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("[SurgeTradingMonitor] Stopped by user")
                break
            except Exception as e:
                logger.error(f"[SurgeTradingMonitor] Error in monitor loop: {e}")
                # Wait 30 seconds before retry on error
                time.sleep(30)


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("CoinPulse 급등 예측 실시간 자동매매 모니터링")
    print("="*60 + "\n")
    print("기능:")
    print("  - 급등 신호 발생 시 즉시 매수")
    print("  - 실시간 가격 모니터링 (5초 주기)")
    print("  - 목표가 도달 → 자동 익절")
    print("  - 손절가 도달 → 자동 손절")
    print("\n" + "="*60 + "\n")

    # Get user ID (default: 1 for testing)
    user_id = int(input("Enter user ID (default: 1): ") or "1")

    # Initialize monitor
    monitor = SurgeTradingMonitor(user_id=user_id, check_interval=5)

    # Run initial cycle
    print("\n[INFO] Running initial monitor cycle...")
    stats = monitor.run_monitor_cycle()
    print(f"[INFO] Initial cycle complete: {stats}")

    # Ask if user wants to run continuous loop
    print("\n실시간 모니터링을 시작하시겠습니까? (5초마다 자동 체크)")
    print("Enter 'y' to start, or any other key to exit:")
    choice = input().strip().lower()

    if choice == 'y':
        monitor.run_monitor_loop()
    else:
        print("[INFO] Exiting...")


if __name__ == "__main__":
    main()
