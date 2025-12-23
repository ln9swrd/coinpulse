# -*- coding: utf-8 -*-
"""
Surge Auto-Trading Background Worker
급등 예측 자동 매매 백그라운드 작업자

사용자별 자동 매매 설정을 확인하고 급등 신호 발생 시 자동 매수 실행
"""

import time
import logging
import threading
from datetime import datetime
from typing import List, Dict, Set
from sqlalchemy import and_

from backend.database.connection import get_db_session
from backend.database.models import User
from backend.models.surge_alert_models import SurgeAutoTradingSettings, SurgeAlert
from backend.services.surge_alert_service import get_surge_alert_service
from backend.common import UpbitAPI, load_api_keys
from backend.services.surge_predictor import SurgePredictor

logger = logging.getLogger(__name__)


class SurgeAutoTradingWorker:
    """
    급등 예측 자동 매매 백그라운드 작업자

    주기적으로:
    1. 급등 후보 코인 탐지
    2. 자동 매매가 활성화된 사용자 조회
    3. 조건을 만족하는 사용자에게 자동 매수 실행
    """

    def __init__(self, check_interval: int = 300):
        """
        Initialize worker

        Args:
            check_interval: Check interval in seconds (default: 300 = 5 minutes)
        """
        self.check_interval = check_interval
        self.running = False
        self.thread = None

        # Initialize Upbit API
        access_key, secret_key = load_api_keys()
        self.upbit_api = UpbitAPI(access_key, secret_key)

        # Initialize SurgePredictor
        self.config = {
            "surge_prediction": {
                "volume_increase_threshold": 1.5,
                "rsi_oversold_level": 35,
                "rsi_buy_zone_max": 50,
                "support_level_proximity": 0.02,
                "uptrend_confirmation_days": 3,
                "min_surge_probability_score": 60
            }
        }
        self.predictor = SurgePredictor(self.config)

        # Popular coins to monitor (reduced to top performers)
        self.monitor_coins = [
            'KRW-XRP', 'KRW-ADA', 'KRW-DOGE', 'KRW-SOL', 'KRW-MATIC',
            'KRW-DOT', 'KRW-LINK', 'KRW-AVAX', 'KRW-NEAR', 'KRW-ATOM',
            'KRW-ALGO', 'KRW-XLM', 'KRW-FIL', 'KRW-APT', 'KRW-SAND'
        ]

        # Track alerted markets to avoid duplicate alerts within same cycle
        self.alerted_in_cycle: Set[str] = set()

        # Minimum score for auto-trading
        self.min_score = 75  # Higher threshold for auto-trading (vs 60 for manual alerts)

        logger.info(f"[AutoTradingWorker] Initialized (interval: {check_interval}s, coins: {len(self.monitor_coins)})")

    def get_surge_candidates(self) -> List[Dict]:
        """
        Get current surge candidates

        Returns:
            List of surge candidates with score >= min_score
        """
        candidates = []

        for market in self.monitor_coins:
            try:
                # Get candle data
                candle_data = self.upbit_api.get_candles_days(market=market, count=30)
                if not candle_data or len(candle_data) < 20:
                    continue

                # Get current price
                current_price = float(candle_data[0].get('trade_price', 0))
                if current_price == 0:
                    continue

                # Analyze
                analysis = self.predictor.analyze_coin(market, candle_data, current_price)

                # Add to candidates if score >= min_score
                if analysis['score'] >= self.min_score:
                    coin = market.replace('KRW-', '')

                    # Calculate target price based on expected return
                    expected_return = analysis.get('expected_return', 10.0)
                    target_price = int(current_price * (1 + expected_return / 100))

                    candidates.append({
                        'market': market,
                        'coin': coin,
                        'score': analysis['score'],
                        'current_price': int(current_price),
                        'target_price': target_price,
                        'expected_return': expected_return,
                        'signals': analysis['signals'],
                        'recommendation': analysis['recommendation']
                    })

                # Rate limit (10 requests per second max)
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"[AutoTradingWorker] Error analyzing {market}: {e}")
                continue

        return candidates

    def get_active_users(self) -> List[tuple]:
        """
        Get users with auto-trading enabled

        Returns:
            List of (user, settings) tuples
        """
        session = get_db_session()

        try:
            # Query users with auto-trading enabled and valid plan
            results = session.query(User, SurgeAutoTradingSettings)\
                .join(SurgeAutoTradingSettings, User.id == SurgeAutoTradingSettings.user_id)\
                .filter(
                    and_(
                        SurgeAutoTradingSettings.enabled == True,
                        User.plan.in_(['basic', 'pro', 'enterprise'])  # Exclude free plan
                    )
                )\
                .all()

            logger.info(f"[AutoTradingWorker] Found {len(results)} active users")
            return results

        except Exception as e:
            logger.error(f"[AutoTradingWorker] Error querying active users: {e}")
            return []

        finally:
            session.close()

    def process_candidates(self):
        """
        Process surge candidates and execute auto-trades for eligible users
        """
        logger.info("[AutoTradingWorker] Processing surge candidates...")

        try:
            # 1. Get surge candidates
            candidates = self.get_surge_candidates()

            if not candidates:
                logger.info("[AutoTradingWorker] No candidates found")
                return

            logger.info(f"[AutoTradingWorker] Found {len(candidates)} candidates: {[c['market'] for c in candidates]}")

            # 2. Get active users
            active_users = self.get_active_users()

            if not active_users:
                logger.info("[AutoTradingWorker] No active users")
                return

            # 3. Get surge alert service
            surge_service = get_surge_alert_service()

            # 4. Process each candidate for each user
            total_alerts = 0
            total_trades = 0

            for candidate in candidates:
                market = candidate['market']

                # Skip if already alerted in this cycle
                if market in self.alerted_in_cycle:
                    logger.debug(f"[AutoTradingWorker] {market} already processed in this cycle")
                    continue

                for user, settings in active_users:
                    try:
                        # Send alert and potentially execute trade
                        success, alert = surge_service.send_alert_to_user(
                            user_id=user.id,
                            plan=user.plan or 'free',
                            market=market,
                            coin=candidate['coin'],
                            confidence=candidate['score'],
                            current_price=candidate['current_price'],
                            target_price=candidate['target_price'],
                            expected_return=candidate['expected_return'],
                            telegram_chat_id=user.telegram_chat_id if hasattr(user, 'telegram_chat_id') else None
                        )

                        if success:
                            total_alerts += 1
                            if alert and alert.auto_traded:
                                total_trades += 1
                                logger.info(f"[AutoTradingWorker] ✅ Auto-trade executed: User {user.id} bought {market}")
                            else:
                                logger.info(f"[AutoTradingWorker] 📧 Alert sent: User {user.id} notified about {market}")

                    except Exception as e:
                        logger.error(f"[AutoTradingWorker] Error processing user {user.id} for {market}: {e}")
                        continue

                # Mark as alerted in this cycle
                self.alerted_in_cycle.add(market)

            logger.info(f"[AutoTradingWorker] ✅ Cycle complete: {total_alerts} alerts sent, {total_trades} auto-trades executed")

        except Exception as e:
            logger.error(f"[AutoTradingWorker] Error in process_candidates: {e}")

    def run_worker_loop(self):
        """
        Main worker loop (runs in background thread)
        """
        logger.info(f"[AutoTradingWorker] Starting worker loop (interval: {self.check_interval}s)")

        while self.running:
            try:
                # Process candidates
                self.process_candidates()

                # Clear alerted candidates after each cycle
                self.alerted_in_cycle.clear()

                # Wait for next cycle
                logger.info(f"[AutoTradingWorker] Next check in {self.check_interval}s...")
                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"[AutoTradingWorker] Error in worker loop: {e}")
                # Wait and retry
                time.sleep(60)

    def start(self):
        """
        Start worker in background thread
        """
        if self.running:
            logger.warning("[AutoTradingWorker] Worker already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self.run_worker_loop, daemon=True)
        self.thread.start()

        logger.info("[AutoTradingWorker] ✅ Worker started")

    def stop(self):
        """
        Stop worker
        """
        if not self.running:
            logger.warning("[AutoTradingWorker] Worker not running")
            return

        self.running = False

        if self.thread:
            self.thread.join(timeout=10)

        logger.info("[AutoTradingWorker] ✅ Worker stopped")

    def is_running(self) -> bool:
        """
        Check if worker is running

        Returns:
            True if running
        """
        return self.running


# Singleton instance
_worker_instance = None


def get_auto_trading_worker(check_interval: int = 300) -> SurgeAutoTradingWorker:
    """
    Get or create auto-trading worker instance

    Args:
        check_interval: Check interval in seconds

    Returns:
        SurgeAutoTradingWorker instance
    """
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = SurgeAutoTradingWorker(check_interval)
    return _worker_instance


if __name__ == "__main__":
    print("Surge Auto-Trading Worker")
    print("=" * 60)

    # Initialize worker
    worker = get_auto_trading_worker(check_interval=60)  # 1 minute for testing

    # Start worker
    worker.start()

    print("\n✅ Worker started")
    print(f"• Monitoring {len(worker.monitor_coins)} coins")
    print(f"• Check interval: {worker.check_interval}s")
    print(f"• Minimum score: {worker.min_score}")
    print("\nPress Ctrl+C to stop\n")

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping worker...")
        worker.stop()
        print("✅ Worker stopped")
