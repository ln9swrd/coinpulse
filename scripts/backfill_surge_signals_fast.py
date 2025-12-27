# -*- coding: utf-8 -*-
"""
Fast Backfill Surge Signals

Faster version that:
- Samples every 3 days instead of daily (3x faster)
- Checks 48h outcomes instead of 72h (1.5x faster)
- Combined: 4.5x faster (~40min instead of 3h)
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


class FastSurgeBackfiller:
    """Fast backfill with sampling"""

    def __init__(self, start_date: datetime):
        self.start_date = start_date
        self.end_date = datetime.now()
        self.upbit_api_base = "https://api.upbit.com/v1"
        self.market_selector = DynamicMarketSelector()

        # Initialize SurgePredictor
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
        self.sample_interval_days = 3  # Sample every 3 days
        self.outcome_hours = 48  # Check 48h outcomes instead of 72h

        print(f"[INFO] Backfill period: {start_date.date()} to {self.end_date.date()}")
        print(f"[INFO] Sampling: every {self.sample_interval_days} days")
        print(f"[INFO] Outcome window: {self.outcome_hours} hours")
        total_samples = (self.end_date - start_date).days // self.sample_interval_days
        print(f"[INFO] Total samples: {total_samples} days")

    def get_markets_for_date(self, date: datetime) -> List[str]:
        """Get list of markets to check"""
        markets = self.market_selector.get_markets(force_update=False)
        return markets[:50]  # Top 50

    def fetch_candles(self, market: str, date: datetime, count: int = 200) -> Optional[List[Dict]]:
        """Fetch candles"""
        try:
            to_datetime = date.strftime('%Y-%m-%d %H:%M:%S')
            response = requests.get(
                f"{self.upbit_api_base}/candles/minutes/1",
                params={'market': market, 'to': to_datetime, 'count': count},
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            return None

        except Exception as e:
            return None

    def find_peak_and_outcome(self, market: str, entry_date: datetime, entry_price: int) -> Dict:
        """Find peak and outcome for next 48 hours (faster than 72h)"""
        all_candles = []

        # 48h = 2880 minutes, need 15 chunks of 200
        for chunk in range(15):
            candles = self.fetch_candles(
                market,
                entry_date + timedelta(minutes=(chunk + 1) * 200),
                count=200
            )

            if candles:
                all_candles.extend(candles)

            time.sleep(0.25)  # Slightly faster rate limit

        if not all_candles:
            return {
                'peak_price': entry_price,
                'exit_price': entry_price,
                'closed_at': entry_date + timedelta(hours=self.outcome_hours),
                'close_reason': 'No data available'
            }

        # Find peak
        peak_price = entry_price
        for candle in all_candles:
            high = int(candle.get('high_price', 0))
            if high > peak_price:
                peak_price = high

        # Final price
        final_price = int(all_candles[0].get('trade_price', entry_price))

        # Determine close reason
        if peak_price > entry_price and final_price < peak_price * 0.97:
            reason = 'Drop from peak (>3%)'
        elif final_price < entry_price * 0.98:
            reason = 'Below entry price'
        else:
            reason = f'Expired ({self.outcome_hours}h)'

        return {
            'peak_price': peak_price,
            'exit_price': final_price,
            'closed_at': entry_date + timedelta(hours=self.outcome_hours),
            'close_reason': reason
        }

    def detect_surge(self, market: str, candles: List[Dict], check_date: datetime) -> Optional[Dict]:
        """Detect surge"""
        if not candles or len(candles) < 50:
            return None

        try:
            current_price = float(candles[0].get('trade_price', 0))
            if current_price == 0:
                return None

            analysis = self.surge_predictor.analyze_coin(market, candles, current_price)
            if not analysis or analysis.get('score', 0) < 60:
                return None

            score = analysis.get('score', 0)
            target_price = int(analysis.get('target_price', current_price * 1.05))
            entry_price = int(current_price)
            coin = market.split('-')[1]

            print(f"    [SIGNAL] {coin} (score={score})")
            outcome = self.find_peak_and_outcome(market, check_date, entry_price)

            return {
                'market': market,
                'coin': coin,
                'score': score,
                'entry_price': entry_price,
                'target_price': target_price,
                'detected_at': check_date,
                **outcome
            }

        except Exception as e:
            return None

    def insert_signal(self, signal: Dict):
        """Insert signal (system-wide, user_id=1, signal_type='surge')"""
        # Calculate week number from detected_at date
        detected_at = signal['detected_at']
        week_number = detected_at.isocalendar()[1]  # ISO week number

        with get_db_session() as session:
            query = text("""
                INSERT INTO surge_alerts (
                    user_id, market, coin, signal_type, status, confidence, entry_price, target_price,
                    peak_price, exit_price, close_reason, sent_at, closed_at, week_number
                )
                VALUES (
                    1, :market, :coin, 'surge', 'closed', :score, :entry_price, :target_price,
                    :peak_price, :exit_price, :close_reason, :detected_at, :closed_at, :week_number
                )
            """)

            session.execute(query, {**signal, 'week_number': week_number})
            session.commit()

    def backfill(self):
        """Run fast backfill"""
        print()
        print("=" * 80)
        print("Starting Fast Backfill")
        print("=" * 80)
        print()

        print("[INFO] Fetching markets...")
        markets = self.get_markets_for_date(self.start_date)
        print(f"[OK] {len(markets)} markets")
        print()

        current_date = self.start_date
        total_signals = 0
        dates_processed = 0

        while current_date <= self.end_date:
            print(f"[INFO] {current_date.date()}...")
            date_signals = 0

            for market in markets:
                candles = self.fetch_candles(market, current_date)
                if candles:
                    signal = self.detect_surge(market, candles, current_date)
                    if signal:
                        self.insert_signal(signal)
                        date_signals += 1
                        total_signals += 1

                        profit_pct = ((signal['exit_price'] - signal['entry_price']) / signal['entry_price']) * 100
                        peak_pct = ((signal['peak_price'] - signal['entry_price']) / signal['entry_price']) * 100
                        print(f"      Entry={signal['entry_price']:,}, "
                              f"Peak=+{peak_pct:.1f}%, Exit={profit_pct:+.1f}%")

                time.sleep(0.4)  # Rate limit

            dates_processed += 1
            print(f"[OK] {date_signals} signals")
            print()

            # Jump to next sample date
            current_date += timedelta(days=self.sample_interval_days)

        print("=" * 80)
        print("Backfill Complete")
        print("=" * 80)
        print(f"[SUMMARY] Processed {dates_processed} sample dates")
        print(f"[SUMMARY] Total signals: {total_signals}")
        print()


def main():
    print()
    print("=" * 80)
    print("CoinPulse Fast Surge Signal Backfill")
    print("=" * 80)
    print()

    start_date = datetime(2025, 10, 1, 0, 0, 0)
    backfiller = FastSurgeBackfiller(start_date)
    backfiller.backfill()


if __name__ == "__main__":
    print(f"[START] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    main()
    print()
    print(f"[DONE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
