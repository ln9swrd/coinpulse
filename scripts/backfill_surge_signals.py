# -*- coding: utf-8 -*-
"""
Backfill Surge Signals

Regenerates surge signals from October 1, 2025 to present by:
1. Fetching historical candle data for each date
2. Running surge detection algorithm
3. Inserting detected signals with proper timestamps

This simulates what would have been detected if the system was running since Oct 1.
"""

import os
import sys
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from backend.database.connection import get_db_session
from backend.services.dynamic_market_selector import DynamicMarketSelector
from backend.services.surge_predictor import SurgePredictor


class SurgeBackfiller:
    """Backfill historical surge signals"""

    def __init__(self, start_date: datetime):
        self.start_date = start_date
        self.end_date = datetime.now()
        self.upbit_api_base = "https://api.upbit.com/v1"
        self.market_selector = DynamicMarketSelector()

        # Initialize SurgePredictor with config (same as surge_alert_scheduler)
        config = {
            "surge_prediction": {
                "volume_increase_threshold": 1.5,
                "rsi_oversold_level": 35,
                "rsi_buy_zone_max": 50,
                "support_level_proximity": 0.02,
                "uptrend_confirmation_days": 3,
                "min_surge_probability_score": 60
            }
        }
        self.surge_predictor = SurgePredictor(config)

        print(f"[INFO] Backfill period: {start_date.date()} to {self.end_date.date()}")
        print(f"[INFO] Total days: {(self.end_date - start_date).days}")

    def get_markets_for_date(self, date: datetime) -> List[str]:
        """Get list of markets to check for a given date"""
        # Use dynamic market selector
        markets = self.market_selector.get_markets(force_update=False)

        # For historical data, we use current markets
        # (ideally we'd fetch historical market list, but that's complex)
        return markets[:50]  # Top 50

    def fetch_candles(self, market: str, date: datetime, count: int = 200) -> Optional[List[Dict]]:
        """Fetch historical candle data for a specific date"""
        try:
            # Fetch minute candles for the date
            to_datetime = date.strftime('%Y-%m-%d %H:%M:%S')

            response = requests.get(
                f"{self.upbit_api_base}/candles/minutes/1",
                params={
                    'market': market,
                    'to': to_datetime,
                    'count': count
                },
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"[ERROR] {market}: API returned {response.status_code}")
                return None

        except Exception as e:
            print(f"[ERROR] {market}: Failed to fetch candles - {e}")
            return None

    def find_peak_and_outcome(self, market: str, entry_date: datetime, entry_price: int) -> Dict:
        """
        Find peak price and determine outcome for the next 72 hours

        Returns dict with peak_price, exit_price, closed_at, close_reason
        """
        # Fetch candles for next 72 hours (4320 minutes)
        # Split into multiple requests (max 200 per request)
        all_candles = []

        for chunk in range(22):  # 4320 / 200 = 21.6, round up to 22
            from_datetime = (entry_date + timedelta(minutes=chunk * 200)).strftime('%Y-%m-%d %H:%M:%S')

            candles = self.fetch_candles(market, entry_date + timedelta(minutes=(chunk + 1) * 200), count=200)

            if candles:
                all_candles.extend(candles)

            time.sleep(0.3)  # Rate limit

        if not all_candles:
            # No data, assume failed
            return {
                'peak_price': entry_price,
                'exit_price': entry_price,
                'closed_at': entry_date + timedelta(hours=72),
                'close_reason': 'No data available'
            }

        # Find peak price
        peak_price = entry_price
        peak_time = entry_date

        for candle in all_candles:
            high = int(candle.get('high_price', 0))
            if high > peak_price:
                peak_price = high
                candle_time_str = candle.get('candle_date_time_kst', '')
                peak_time = datetime.strptime(candle_time_str, '%Y-%m-%dT%H:%M:%S')

        # Determine close reason and exit price
        final_candle = all_candles[0]  # Most recent (Upbit returns newest first)
        final_price = int(final_candle.get('trade_price', entry_price))

        # Check if dropped from peak by >3%
        if peak_price > entry_price and final_price < peak_price * 0.97:
            return {
                'peak_price': peak_price,
                'exit_price': final_price,
                'closed_at': entry_date + timedelta(hours=72),
                'close_reason': 'Drop from peak (>3%)'
            }

        # Check if below entry by >2%
        elif final_price < entry_price * 0.98:
            return {
                'peak_price': peak_price,
                'exit_price': final_price,
                'closed_at': entry_date + timedelta(hours=72),
                'close_reason': 'Below entry price'
            }

        # Otherwise, expired after 72h
        else:
            return {
                'peak_price': peak_price,
                'exit_price': final_price,
                'closed_at': entry_date + timedelta(hours=72),
                'close_reason': 'Expired (72h)'
            }

    def detect_surge(self, market: str, candles: List[Dict], check_date: datetime) -> Optional[Dict]:
        """
        Run surge detection on historical candle data

        Returns surge signal dict if detected, None otherwise
        """
        if not candles or len(candles) < 50:
            return None

        try:
            # Get current price
            current_price = float(candles[0].get('trade_price', 0))
            if current_price == 0:
                return None

            # Run surge analysis
            analysis = self.surge_predictor.analyze_coin(market, candles, current_price)

            if not analysis:
                return None

            score = analysis.get('score', 0)

            # Only create signals for high-confidence predictions (score >= 60)
            if score < 60:
                return None

            # Get target price from analysis
            target_price = int(analysis.get('target_price', current_price * 1.05))
            entry_price = int(current_price)

            # Extract coin name from market (e.g., "KRW-BTC" -> "BTC")
            coin = market.split('-')[1]

            # Find peak and outcome for next 72 hours
            print(f"    [INFO] Finding outcome for {coin}...")
            outcome = self.find_peak_and_outcome(market, check_date, entry_price)

            return {
                'market': market,
                'coin': coin,
                'score': score,
                'entry_price': entry_price,
                'target_price': target_price,
                'detected_at': check_date,
                **outcome  # Add peak_price, exit_price, closed_at, close_reason
            }

        except Exception as e:
            print(f"[ERROR] {market}: Surge detection failed - {e}")
            return None

    def insert_signal(self, signal: Dict):
        """Insert detected signal into database (already closed with outcome)"""
        with get_db_session() as session:
            query = text("""
                INSERT INTO surge_alerts (
                    market, coin, status, score, entry_price, target_price,
                    peak_price, exit_price, close_reason,
                    detected_at, sent_at, closed_at, created_at, updated_at
                )
                VALUES (
                    :market, :coin, 'closed', :score, :entry_price, :target_price,
                    :peak_price, :exit_price, :close_reason,
                    :detected_at, :detected_at, :closed_at, :detected_at, :detected_at
                )
            """)

            session.execute(query, {
                'market': signal['market'],
                'coin': signal['coin'],
                'score': signal['score'],
                'entry_price': signal['entry_price'],
                'target_price': signal['target_price'],
                'peak_price': signal['peak_price'],
                'exit_price': signal['exit_price'],
                'close_reason': signal['close_reason'],
                'detected_at': signal['detected_at'],
                'closed_at': signal['closed_at']
            })

            session.commit()

    def backfill(self):
        """Run backfill process"""
        print()
        print("=" * 80)
        print("Starting Backfill Process")
        print("=" * 80)
        print()

        # Get markets
        print("[INFO] Fetching market list...")
        markets = self.get_markets_for_date(self.start_date)
        print(f"[OK] Found {len(markets)} markets to check")
        print()

        # Loop through dates (check once per day at 00:00)
        current_date = self.start_date
        total_signals = 0
        dates_processed = 0

        while current_date <= self.end_date:
            print(f"[INFO] Processing {current_date.date()}...")
            date_signals = 0

            # Check each market for this date
            for market in markets:
                # Fetch candles for this date
                candles = self.fetch_candles(market, current_date)

                if not candles:
                    continue

                # Detect surge
                signal = self.detect_surge(market, candles, current_date)

                if signal:
                    # Insert signal
                    self.insert_signal(signal)
                    date_signals += 1
                    total_signals += 1

                    # Calculate profit/loss
                    profit_pct = ((signal['exit_price'] - signal['entry_price']) / signal['entry_price']) * 100
                    peak_pct = ((signal['peak_price'] - signal['entry_price']) / signal['entry_price']) * 100

                    print(f"  [SIGNAL] {signal['coin']}: "
                          f"Score={signal['score']}, "
                          f"Entry={signal['entry_price']:,}, "
                          f"Peak={signal['peak_price']:,} (+{peak_pct:.1f}%), "
                          f"Exit={signal['exit_price']:,} ({profit_pct:+.1f}%), "
                          f"Reason: {signal['close_reason']}")

                # Rate limit (to avoid 429 errors, use 0.5s delay = 2 requests/sec)
                time.sleep(0.5)

            dates_processed += 1
            print(f"[OK] {current_date.date()}: {date_signals} signals detected")
            print()

            # Move to next day
            current_date += timedelta(days=1)

        print("=" * 80)
        print("Backfill Complete")
        print("=" * 80)
        print(f"[SUMMARY] Processed {dates_processed} days")
        print(f"[SUMMARY] Total signals detected: {total_signals}")
        print()


def main():
    """Main entry point"""
    print()
    print("=" * 80)
    print("CoinPulse Surge Signal Backfill")
    print("=" * 80)
    print()

    # Start date: October 1, 2025
    start_date = datetime(2025, 10, 1, 0, 0, 0)

    # Create backfiller
    backfiller = SurgeBackfiller(start_date)

    # Run backfill
    backfiller.backfill()


if __name__ == "__main__":
    print(f"[START] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    main()

    print()
    print(f"[DONE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
