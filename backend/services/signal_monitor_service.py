# -*- coding: utf-8 -*-
"""
Surge Signal Monitor Service

Real-time monitoring service for active surge signals:
- Tracks peak prices for active signals
- Detects momentum loss
- Auto-closes signals based on criteria:
  1. Peak price drop > 3%
  2. No upward movement for 24h
  3. Time expired (72h)
  4. Low progress towards target

Runs every 5 minutes to ensure timely closures.
"""

import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from sqlalchemy import text

from backend.database.connection import get_db_session

# Logging setup
logging.basicConfig(
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SignalMonitorService:
    """Monitor active surge signals and auto-close when momentum is lost"""

    def __init__(self, check_interval: int = 300):
        """
        Initialize signal monitor

        Args:
            check_interval: Check interval in seconds (default: 300 = 5 minutes)
        """
        self.check_interval = check_interval
        self.upbit_api_base = "https://api.upbit.com/v1"

        # Auto-close criteria
        self.max_age_hours = 72  # Close signals older than 72 hours
        self.peak_drop_threshold = 0.03  # 3% drop from peak triggers close
        self.stagnant_hours = 24  # No movement for 24 hours
        self.min_progress_pct = 10  # Minimum 10% progress towards target

        logger.info(f"[SignalMonitor] Initialized (interval: {check_interval}s)")
        logger.info(f"[SignalMonitor] Criteria: max_age={self.max_age_hours}h, "
                   f"peak_drop={self.peak_drop_threshold*100}%, "
                   f"stagnant={self.stagnant_hours}h")

    def get_current_price(self, market: str) -> Optional[int]:
        """
        Get current price from Upbit API

        Args:
            market: Market symbol (e.g., 'KRW-BTC')

        Returns:
            Current price in KRW, or None if failed
        """
        try:
            response = requests.get(
                f"{self.upbit_api_base}/ticker",
                params={'markets': market},
                timeout=5
            )

            if response.status_code == 200:
                ticker_data = response.json()
                if ticker_data and len(ticker_data) > 0:
                    return int(ticker_data[0]['trade_price'])

        except Exception as e:
            logger.error(f"[SignalMonitor] Failed to get price for {market}: {e}")

        return None

    def get_active_signals(self) -> List[Dict]:
        """
        Get all active (non-closed) surge signals

        Returns:
            List of active signal dicts
        """
        with get_db_session() as session:
            query = text("""
                SELECT id, market, coin, status, entry_price, target_price,
                       peak_price, sent_at, last_checked_at,
                       EXTRACT(EPOCH FROM (NOW() - sent_at))/3600 as hours_since_sent,
                       EXTRACT(EPOCH FROM (NOW() - COALESCE(last_checked_at, sent_at)))/3600 as hours_since_check
                FROM surge_alerts
                WHERE status IN ('pending', 'active')
                  AND sent_at IS NOT NULL
                ORDER BY sent_at DESC
            """)

            result = session.execute(query)
            signals = result.fetchall()

            return [
                {
                    'id': s[0],
                    'market': s[1],
                    'coin': s[2],
                    'status': s[3],
                    'entry_price': s[4],
                    'target_price': s[5],
                    'peak_price': s[6],
                    'sent_at': s[7],
                    'last_checked_at': s[8],
                    'hours_since_sent': float(s[9]) if s[9] else 0,
                    'hours_since_check': float(s[10]) if s[10] else 0
                }
                for s in signals
            ]

    def should_close_signal(self, signal: Dict, current_price: int) -> tuple[bool, str]:
        """
        Determine if signal should be closed

        Args:
            signal: Signal dict
            current_price: Current market price

        Returns:
            (should_close: bool, reason: str)
        """
        entry_price = signal.get('entry_price')
        peak_price = signal.get('peak_price') or entry_price
        target_price = signal.get('target_price')
        hours_since_sent = signal.get('hours_since_sent', 0)

        # Criterion 1: Time expired (72 hours)
        if hours_since_sent >= self.max_age_hours:
            return True, f"Expired ({hours_since_sent:.0f}h > {self.max_age_hours}h)"

        # Criterion 2: Significant drop from peak
        if peak_price and current_price < peak_price:
            drop_pct = (peak_price - current_price) / peak_price
            if drop_pct >= self.peak_drop_threshold:
                return True, f"Drop from peak ({drop_pct*100:.1f}% > {self.peak_drop_threshold*100}%)"

        # Criterion 3: Negative momentum (price below entry)
        if entry_price and current_price < entry_price * 0.98:  # -2% from entry
            return True, f"Below entry price ({current_price} < {entry_price*0.98:.0f})"

        # Criterion 4: Stagnant (no significant movement)
        if entry_price:
            change_pct = ((current_price - entry_price) / entry_price) * 100
            if abs(change_pct) < 1.0 and hours_since_sent >= self.stagnant_hours:
                return True, f"Stagnant ({change_pct:.2f}% in {hours_since_sent:.0f}h)"

        # Criterion 5: Low progress towards target
        if target_price and entry_price and target_price > entry_price:
            progress = ((current_price - entry_price) / (target_price - entry_price)) * 100
            if progress < self.min_progress_pct and hours_since_sent >= 48:  # After 48h
                return True, f"Low progress ({progress:.1f}% < {self.min_progress_pct}%)"

        return False, "Active"

    def update_signal_peak(self, signal_id: int, peak_price: int):
        """
        Update signal's peak price

        Args:
            signal_id: Signal ID
            peak_price: New peak price
        """
        with get_db_session() as session:
            query = text("""
                UPDATE surge_alerts
                SET peak_price = :peak_price,
                    last_checked_at = NOW()
                WHERE id = :signal_id
            """)

            session.execute(query, {
                'signal_id': signal_id,
                'peak_price': peak_price
            })
            session.commit()

    def close_signal(self, signal_id: int, exit_price: int, reason: str):
        """
        Close a signal

        Args:
            signal_id: Signal ID
            exit_price: Exit price
            reason: Closure reason
        """
        with get_db_session() as session:
            query = text("""
                UPDATE surge_alerts
                SET status = 'closed',
                    exit_price = :exit_price,
                    closed_at = NOW(),
                    close_reason = :reason
                WHERE id = :signal_id
            """)

            session.execute(query, {
                'signal_id': signal_id,
                'exit_price': exit_price,
                'reason': reason
            })
            session.commit()

    def monitor_signals(self):
        """
        Monitor all active signals and update/close as needed
        """
        logger.info("[SignalMonitor] Checking active signals...")

        signals = self.get_active_signals()

        if not signals:
            logger.info("[SignalMonitor] No active signals to monitor")
            return

        logger.info(f"[SignalMonitor] Monitoring {len(signals)} active signals")

        updated_count = 0
        closed_count = 0

        for signal in signals:
            signal_id = signal['id']
            market = signal['market']
            coin = signal['coin']
            entry_price = signal.get('entry_price')
            peak_price = signal.get('peak_price') or entry_price
            hours_since_sent = signal.get('hours_since_sent', 0)

            # Get current price
            current_price = self.get_current_price(market)

            if not current_price:
                logger.warning(f"[SignalMonitor] {coin} (ID: {signal_id}): Failed to get price")
                continue

            logger.info(f"[SignalMonitor] {coin} (ID: {signal_id}): "
                       f"Entry={entry_price:,} Peak={peak_price:,} Current={current_price:,}")

            # Update peak if new high
            if peak_price is None or current_price > peak_price:
                self.update_signal_peak(signal_id, current_price)
                logger.info(f"[SignalMonitor] {coin} NEW PEAK: {peak_price:,} -> {current_price:,} "
                           f"(+{((current_price - peak_price) / peak_price * 100) if peak_price else 0:.2f}%)")
                updated_count += 1
                peak_price = current_price  # Update local copy

            # Check if should close
            should_close, reason = self.should_close_signal(signal, current_price)

            if should_close:
                self.close_signal(signal_id, current_price, reason)
                logger.info(f"[SignalMonitor] {coin} CLOSED: {reason} "
                           f"(Entry={entry_price:,} Peak={peak_price:,} Exit={current_price:,})")
                closed_count += 1
            else:
                # Update last_checked_at
                with get_db_session() as session:
                    session.execute(
                        text("UPDATE surge_alerts SET last_checked_at = NOW() WHERE id = :sid"),
                        {'sid': signal_id}
                    )
                    session.commit()

            # Rate limit
            time.sleep(0.1)

        logger.info(f"[SignalMonitor] Complete: {updated_count} peaks updated, {closed_count} signals closed")

    def run(self):
        """
        Run monitoring loop
        """
        logger.info(f"[SignalMonitor] Starting monitoring loop (interval: {self.check_interval}s)")

        while True:
            try:
                self.monitor_signals()

                # Wait for next check
                logger.info(f"[SignalMonitor] Next check in {self.check_interval}s...")
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("[SignalMonitor] Stopped by user")
                break
            except Exception as e:
                logger.error(f"[SignalMonitor] Error in monitoring loop: {e}", exc_info=True)
                # Wait and retry
                time.sleep(60)


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("CoinPulse 급등 신호 모니터링 서비스")
    print("="*60 + "\n")

    # Initialize service
    monitor = SignalMonitorService(check_interval=300)  # 5 minutes

    print("[INFO] 시스템 시작!")
    print(f"[INFO] 체크 주기: {monitor.check_interval}초 (5분)")
    print(f"[INFO] 최대 신호 수명: {monitor.max_age_hours}시간")
    print(f"[INFO] 최고가 하락 임계값: {monitor.peak_drop_threshold*100}%")
    print("="*60 + "\n")

    # Run service
    monitor.run()


if __name__ == "__main__":
    main()
