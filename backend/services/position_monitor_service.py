# -*- coding: utf-8 -*-
"""
Position Monitor Service
포지션 모니터링 및 자동 손절/익절 서비스

급등 예측으로 매수한 포지션을 모니터링하여:
- 목표가 도달 시 자동 익절
- 손절가 도달 시 자동 손절
- 실시간 수익률 추적
"""

import time
import logging
import threading
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import and_

from backend.database.connection import get_db_session
from backend.models.surge_alert_models import SurgeAlert
from backend.common import UpbitAPI, load_api_keys

logger = logging.getLogger(__name__)


class PositionMonitorService:
    """
    포지션 모니터링 서비스

    실시간으로 오픈 포지션의 가격을 체크하여
    목표가/손절가 도달 시 자동으로 청산
    """

    def __init__(self, check_interval: int = 10):
        """
        Initialize position monitor

        Args:
            check_interval: Check interval in seconds (default: 10)
        """
        self.check_interval = check_interval
        self.running = False
        self.thread = None

        logger.info(f"[PositionMonitor] Initialized (interval: {check_interval}s)")

    def get_open_positions(self) -> List[SurgeAlert]:
        """
        Get all open positions that need monitoring

        Returns:
            List of SurgeAlert objects with open positions
        """
        session = get_db_session()

        try:
            positions = session.query(SurgeAlert)\
                .filter(
                    and_(
                        SurgeAlert.auto_traded == True,
                        SurgeAlert.status.in_(['executed', 'pending']),
                        SurgeAlert.order_id != None
                    )
                )\
                .all()

            logger.info(f"[PositionMonitor] Found {len(positions)} open positions to monitor")
            return positions

        except Exception as e:
            logger.error(f"[PositionMonitor] Error getting open positions: {e}")
            return []

        finally:
            session.close()

    def check_position(
        self,
        position: SurgeAlert,
        current_price: float
    ) -> Optional[str]:
        """
        Check if position should be closed

        Args:
            position: SurgeAlert object
            current_price: Current market price

        Returns:
            Action to take: 'take_profit', 'stop_loss', or None
        """
        # Check take profit
        if position.target_price and current_price >= position.target_price:
            profit_pct = ((current_price - position.entry_price) / position.entry_price) * 100
            logger.info(f"[PositionMonitor] Take profit triggered for {position.market}")
            logger.info(f"  Entry: {position.entry_price:,} -> Current: {current_price:,} (+{profit_pct:.2f}%)")
            return 'take_profit'

        # Check stop loss
        if position.stop_loss_price and current_price <= position.stop_loss_price:
            loss_pct = ((current_price - position.entry_price) / position.entry_price) * 100
            logger.info(f"[PositionMonitor] Stop loss triggered for {position.market}")
            logger.info(f"  Entry: {position.entry_price:,} -> Current: {current_price:,} ({loss_pct:.2f}%)")
            return 'stop_loss'

        return None

    def execute_close_position(
        self,
        position: SurgeAlert,
        current_price: float,
        reason: str
    ) -> bool:
        """
        Execute position close (sell order)

        Args:
            position: SurgeAlert object
            current_price: Current market price
            reason: Reason for closing ('take_profit' or 'stop_loss')

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"[PositionMonitor] Closing position for user {position.user_id}:")
            logger.info(f"  Market: {position.market}")
            logger.info(f"  Reason: {reason}")
            logger.info(f"  Quantity: {position.trade_quantity}")
            logger.info(f"  Current Price: {current_price:,}")

            # Load user's API keys
            access_key, secret_key = load_api_keys(user_id=position.user_id)

            if not access_key or not secret_key:
                logger.error(f"[PositionMonitor] No API keys for user {position.user_id}")
                return False

            # Execute sell order
            upbit_api = UpbitAPI(access_key, secret_key)

            order_result = upbit_api.place_order(
                market=position.market,
                side='ask',  # Sell
                volume=position.trade_quantity,
                price=None,
                ord_type='market'  # Market order
            )

            if order_result and 'uuid' in order_result:
                # Calculate profit/loss
                sell_amount = current_price * position.trade_quantity
                buy_amount = position.trade_amount
                profit_loss = int(sell_amount - buy_amount)
                profit_loss_percent = ((current_price - position.entry_price) / position.entry_price) * 100

                logger.info(f"[PositionMonitor] Position closed successfully:")
                logger.info(f"  Order ID: {order_result['uuid']}")
                logger.info(f"  P/L: {profit_loss:,} KRW ({profit_loss_percent:.2f}%)")

                # Update position in database
                session = get_db_session()
                try:
                    position.status = 'completed' if reason == 'take_profit' else 'stopped'
                    position.profit_loss = profit_loss
                    position.profit_loss_percent = profit_loss_percent
                    position.closed_at = datetime.utcnow()

                    session.commit()
                    logger.info(f"[PositionMonitor] Position updated in database")

                except Exception as db_error:
                    logger.error(f"[PositionMonitor] Database update failed: {db_error}")
                    session.rollback()

                finally:
                    session.close()

                return True
            else:
                logger.error(f"[PositionMonitor] Sell order failed: {order_result}")
                return False

        except Exception as e:
            logger.error(f"[PositionMonitor] Error closing position: {e}")
            return False

    def monitor_positions(self):
        """
        Main monitoring loop

        Check all open positions and execute closes as needed
        """
        try:
            positions = self.get_open_positions()

            if not positions:
                return

            # Get current prices for all markets
            markets = list(set([p.market for p in positions]))

            # Get ticker data
            from backend.common import UpbitAPI
            public_api = UpbitAPI(None, None)  # Public API

            tickers = public_api.get_ticker(markets=','.join(markets))

            if not tickers:
                logger.warning("[PositionMonitor] Failed to get ticker data")
                return

            # Create price map
            price_map = {
                ticker['market']: float(ticker['trade_price'])
                for ticker in tickers
            }

            # Check each position
            for position in positions:
                current_price = price_map.get(position.market)

                if not current_price:
                    logger.warning(f"[PositionMonitor] No price data for {position.market}")
                    continue

                # Check if action needed
                action = self.check_position(position, current_price)

                if action:
                    # Execute close
                    success = self.execute_close_position(position, current_price, action)

                    if success:
                        logger.info(f"[PositionMonitor] ✅ Position closed: {position.market} ({action})")
                    else:
                        logger.error(f"[PositionMonitor] ❌ Failed to close: {position.market}")

        except Exception as e:
            logger.error(f"[PositionMonitor] Error in monitor loop: {e}")

    def run_monitor_loop(self):
        """
        Background monitoring loop
        """
        logger.info(f"[PositionMonitor] Starting monitor loop (interval: {self.check_interval}s)")

        while self.running:
            try:
                self.monitor_positions()

                # Wait for next cycle
                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"[PositionMonitor] Error in loop: {e}")
                time.sleep(60)  # Wait and retry

    def start(self):
        """
        Start position monitor in background thread
        """
        if self.running:
            logger.warning("[PositionMonitor] Monitor already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self.run_monitor_loop, daemon=True)
        self.thread.start()

        logger.info("[PositionMonitor] ✅ Monitor started")

    def stop(self):
        """
        Stop position monitor
        """
        if not self.running:
            logger.warning("[PositionMonitor] Monitor not running")
            return

        self.running = False

        if self.thread:
            self.thread.join(timeout=10)

        logger.info("[PositionMonitor] ✅ Monitor stopped")

    def is_running(self) -> bool:
        """
        Check if monitor is running

        Returns:
            True if running
        """
        return self.running


# Singleton instance
_monitor_instance = None


def get_position_monitor(check_interval: int = 10) -> PositionMonitorService:
    """
    Get or create position monitor instance

    Args:
        check_interval: Check interval in seconds

    Returns:
        PositionMonitorService instance
    """
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PositionMonitorService(check_interval)
    return _monitor_instance


if __name__ == "__main__":
    print("Position Monitor Service")
    print("=" * 60)

    # Initialize monitor
    monitor = get_position_monitor(check_interval=5)

    # Start monitor
    monitor.start()

    print("\n✅ Monitor started")
    print(f"• Check interval: {monitor.check_interval}s")
    print("\nPress Ctrl+C to stop\n")

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping monitor...")
        monitor.stop()
        print("✅ Monitor stopped")
