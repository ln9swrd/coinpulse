# -*- coding: utf-8 -*-
"""
Signal Generation Scheduler
Periodically analyzes surge candidates and generates trading signals
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import time

from backend.common import UpbitAPI
from backend.services.surge_predictor import SurgePredictor
from backend.services.market_filter_service import MarketFilter
from backend.services.signal_generation_service import signal_generator


class SignalScheduler:
    """
    Background scheduler for automatic signal generation

    Tasks:
    1. Surge Analysis + Signal Generation (every 15 minutes)
    2. Signal Expiry Cleanup (every 30 minutes)
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.upbit_api = UpbitAPI(None, None)  # Public API only
        self.market_filter = MarketFilter()

        # Config from backtest
        SURGE_CONFIG = {
            "surge_prediction": {
                "volume_increase_threshold": 1.5,
                "rsi_oversold_level": 35,
                "rsi_buy_zone_max": 50,
                "support_level_proximity": 0.02,
                "uptrend_confirmation_days": 3,
                "min_surge_probability_score": 60
            }
        }
        self.predictor = SurgePredictor(SURGE_CONFIG)

        self.is_running = False

    def analyze_and_generate_signals(self):
        """
        Main task: Analyze top coins and generate signals

        Process:
        1. Get top 50 coins by volume
        2. Analyze each coin for surge potential
        3. Generate signals for high-confidence predictions (score >= 80)
        4. Distribute to eligible users
        """
        try:
            print("\n" + "=" * 80)
            print(f"[Scheduler] Starting surge analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)

            # Get monitored markets (top 50 by volume)
            monitored_markets = self._get_monitored_markets()
            print(f"[Scheduler] Monitoring {len(monitored_markets)} markets")

            # Analyze all markets
            candidates = []
            for market in monitored_markets:
                try:
                    # Get candle data (30 days) - PUBLIC API
                    candle_data = self.upbit_api.get_candles_days(market=market, count=30)
                    if not candle_data or len(candle_data) < 20:
                        continue

                    # Get current price
                    current_price = float(candle_data[0].get('trade_price', 0))
                    if current_price == 0:
                        continue

                    # Analyze coin
                    analysis = self.predictor.analyze_coin(market, candle_data, current_price)

                    # Only include high-confidence candidates (score >= 80)
                    if analysis['score'] >= 80:
                        candidates.append({
                            'market': market,
                            'score': analysis['score'],
                            'current_price': current_price,
                            'signals': analysis['signals'],
                            'recommendation': analysis['recommendation']
                        })

                    # Rate limit (0.1s between requests)
                    time.sleep(0.1)

                except Exception as e:
                    print(f"[Scheduler] Error analyzing {market}: {e}")
                    continue

            print(f"[Scheduler] Found {len(candidates)} high-confidence candidates")

            # Generate signals for high-confidence candidates
            if candidates:
                result = signal_generator.batch_generate_from_candidates(candidates)
                print(f"\n[Scheduler] Signal generation complete:")
                print(f"  - Signals generated: {result['generated']}")
                print(f"  - Users notified: {result['distributed_total']}")
                if result['errors']:
                    print(f"  - Errors: {len(result['errors'])}")
            else:
                print("[Scheduler] No high-confidence candidates found")

            print("=" * 80)
            print(f"[Scheduler] Analysis complete - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80 + "\n")

        except Exception as e:
            print(f"[Scheduler] Error in analyze_and_generate_signals: {e}")

    def cleanup_expired_signals(self):
        """
        Cleanup task: Expire old signals

        Runs every 30 minutes to update status of expired signals
        """
        try:
            print(f"\n[Scheduler] Cleaning up expired signals - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            expired_count = signal_generator.expire_old_signals()

            if expired_count > 0:
                print(f"[Scheduler] Expired {expired_count} old signals")
            else:
                print("[Scheduler] No expired signals found")

        except Exception as e:
            print(f"[Scheduler] Error in cleanup_expired_signals: {e}")

    def _get_monitored_markets(self):
        """
        Get list of markets to monitor (top 50 by volume, excluding caution)

        Returns:
            list: Market codes
        """
        try:
            markets = self.market_filter.get_top_coins_by_volume(count=50, exclude_caution=True)
            return markets if markets else []
        except Exception as e:
            print(f"[Scheduler] Error getting monitored markets: {e}")
            # Fallback to popular coins
            return [
                'KRW-XRP', 'KRW-ADA', 'KRW-DOGE', 'KRW-AVAX', 'KRW-SHIB',
                'KRW-DOT', 'KRW-MATIC', 'KRW-SOL', 'KRW-LINK', 'KRW-BCH',
                'KRW-NEAR', 'KRW-XLM', 'KRW-ALGO', 'KRW-ATOM', 'KRW-ETC',
                'KRW-VET', 'KRW-ICP', 'KRW-FIL', 'KRW-HBAR', 'KRW-APT',
                'KRW-SAND', 'KRW-MANA', 'KRW-AXS', 'KRW-AAVE', 'KRW-EOS',
                'KRW-THETA', 'KRW-XTZ', 'KRW-EGLD', 'KRW-BSV', 'KRW-ZIL'
            ]

    def start(self):
        """
        Start the scheduler

        Schedules:
        - Signal generation: Every 15 minutes
        - Signal cleanup: Every 30 minutes
        """
        if self.is_running:
            print("[Scheduler] Already running")
            return

        print("\n" + "=" * 80)
        print("Signal Scheduler Starting")
        print("=" * 80)

        # Schedule signal generation (every 15 minutes)
        self.scheduler.add_job(
            func=self.analyze_and_generate_signals,
            trigger=IntervalTrigger(minutes=15),
            id='signal_generation',
            name='Surge Analysis + Signal Generation',
            replace_existing=True
        )
        print("[Scheduler] Job scheduled: Signal generation (every 15 minutes)")

        # Schedule signal cleanup (every 30 minutes)
        self.scheduler.add_job(
            func=self.cleanup_expired_signals,
            trigger=IntervalTrigger(minutes=30),
            id='signal_cleanup',
            name='Signal Expiry Cleanup',
            replace_existing=True
        )
        print("[Scheduler] Job scheduled: Signal cleanup (every 30 minutes)")

        # Start scheduler
        self.scheduler.start()
        self.is_running = True

        print("[Scheduler] Started successfully")
        print("=" * 80 + "\n")

        # Run immediately on startup
        print("[Scheduler] Running initial analysis...")
        self.analyze_and_generate_signals()

    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return

        print("\n[Scheduler] Stopping...")
        self.scheduler.shutdown()
        self.is_running = False
        print("[Scheduler] Stopped")

    def get_jobs(self):
        """Get list of scheduled jobs"""
        if not self.is_running:
            return []

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None
            })
        return jobs


# Global instance
signal_scheduler = SignalScheduler()


# Test function
if __name__ == "__main__":
    print("=" * 80)
    print("Signal Scheduler Test")
    print("=" * 80)

    scheduler = SignalScheduler()

    print("\n[Test] Starting scheduler...")
    scheduler.start()

    print("\n[Test] Scheduled jobs:")
    jobs = scheduler.get_jobs()
    for job in jobs:
        print(f"  - {job['name']} ({job['id']})")
        print(f"    Next run: {job['next_run_time']}")

    print("\n[Test] Scheduler is running. Press Ctrl+C to stop...")

    try:
        # Keep running
        import time
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n[Test] Stopping scheduler...")
        scheduler.stop()
        print("[Test] Stopped")
