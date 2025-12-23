"""
급등 예측 알림 스케줄러

주기적으로 급등 후보를 확인하고 텔레그램으로 알림 전송
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Set, Dict, List
import logging
import os
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables
load_dotenv()

from backend.common import UpbitAPI, load_api_keys
from backend.services.surge_predictor import SurgePredictor
from backend.services.telegram_bot import SurgeTelegramBot, TELEGRAM_AVAILABLE
from backend.models.database import get_db_session

# Logging setup
logging.basicConfig(
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SurgeAlertScheduler:
    """급등 예측 알림 스케줄러"""

    def __init__(self, telegram_bot: SurgeTelegramBot, check_interval: int = 300):
        """
        Initialize scheduler

        Args:
            telegram_bot: Telegram bot instance
            check_interval: Check interval in seconds (default: 300 = 5 minutes)
        """
        self.telegram_bot = telegram_bot
        self.check_interval = check_interval

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

        # Popular coins to monitor
        self.monitor_coins = [
            'KRW-XRP', 'KRW-ADA', 'KRW-DOGE', 'KRW-AVAX', 'KRW-SHIB',
            'KRW-DOT', 'KRW-MATIC', 'KRW-SOL', 'KRW-LINK', 'KRW-BCH',
            'KRW-NEAR', 'KRW-XLM', 'KRW-ALGO', 'KRW-ATOM', 'KRW-ETC',
            'KRW-VET', 'KRW-ICP', 'KRW-FIL', 'KRW-HBAR', 'KRW-APT',
            'KRW-SAND', 'KRW-MANA', 'KRW-AXS', 'KRW-AAVE', 'KRW-EOS',
            'KRW-THETA', 'KRW-XTZ', 'KRW-EGLD', 'KRW-BSV', 'KRW-ZIL'
        ]

        # Track alerted candidates (to avoid duplicate alerts)
        self.alerted_candidates: Set[str] = set()  # Set of market names
        self.min_score = 60

        logger.info(f"[SurgeAlertScheduler] Initialized (interval: {check_interval}s, coins: {len(self.monitor_coins)})")

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
                    candidates.append({
                        'market': market,
                        'score': analysis['score'],
                        'current_price': current_price,
                        'signals': analysis['signals'],
                        'recommendation': analysis['recommendation']
                    })

                # Rate limit
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"[SurgeAlertScheduler] Error analyzing {market}: {e}")
                continue

        return candidates

    def save_to_database(self, candidate: Dict):
        """
        Save surge alert to database

        Args:
            candidate: Surge candidate data
        """
        try:
            with get_db_session() as session:
                # Calculate week number (ISO week)
                now = datetime.now()
                week_number = now.isocalendar()[1]

                # Extract coin from market (e.g., "KRW-BTC" -> "BTC")
                coin = candidate['market'].split('-')[1] if '-' in candidate['market'] else candidate['market']

                # Prepare alert data
                query = text("""
                    INSERT INTO surge_alerts (
                        user_id, market, coin, confidence, signal_type,
                        current_price, target_price, expected_return, reason,
                        alert_message, telegram_sent, sent_at, week_number, auto_traded
                    ) VALUES (
                        :user_id, :market, :coin, :confidence, :signal_type,
                        :current_price, :target_price, :expected_return, :reason,
                        :alert_message, :telegram_sent, :sent_at, :week_number, :auto_traded
                    )
                """)

                # Use system user_id = 1 (or admin) for surge alerts
                params = {
                    'user_id': 1,  # System user
                    'market': candidate['market'],
                    'coin': coin,
                    'confidence': candidate['score'] / 100.0,  # Convert score to 0-1 range
                    'signal_type': 'surge',
                    'current_price': int(candidate.get('current_price', 0)),
                    'target_price': int(candidate.get('target_price', 0)),
                    'expected_return': candidate.get('expected_return', 0.0),
                    'reason': candidate.get('reason', ''),
                    'alert_message': f"급등 예측: {candidate['market']} (신뢰도: {candidate['score']}점)",
                    'telegram_sent': True,
                    'sent_at': now,
                    'week_number': week_number,
                    'auto_traded': False
                }

                session.execute(query, params)
                session.commit()

                logger.info(f"[SurgeAlertScheduler] Saved to DB: {candidate['market']}")

        except Exception as e:
            logger.error(f"[SurgeAlertScheduler] Failed to save to DB: {e}")

    async def check_and_alert(self):
        """
        Check for new surge candidates and send alerts
        """
        logger.info("[SurgeAlertScheduler] Checking for surge candidates...")

        try:
            # Get current candidates
            candidates = self.get_surge_candidates()

            if not candidates:
                logger.info("[SurgeAlertScheduler] No candidates found")
                return

            logger.info(f"[SurgeAlertScheduler] Found {len(candidates)} candidates")

            # Send alerts for new candidates
            new_alerts = 0
            for candidate in candidates:
                market = candidate['market']

                # Skip if already alerted
                if market in self.alerted_candidates:
                    logger.debug(f"[SurgeAlertScheduler] {market} already alerted, skipping")
                    continue

                # Send alert
                await self.telegram_bot.send_surge_alert(candidate)

                # Save to database
                self.save_to_database(candidate)

                # Mark as alerted
                self.alerted_candidates.add(market)
                new_alerts += 1

                logger.info(f"[SurgeAlertScheduler] New alert sent: {market} ({candidate['score']}점)")

            if new_alerts > 0:
                logger.info(f"[SurgeAlertScheduler] Sent {new_alerts} new alerts")

            # Clean up old alerts (remove if not in current candidates)
            current_markets = {c['market'] for c in candidates}
            removed = self.alerted_candidates - current_markets
            if removed:
                self.alerted_candidates -= removed
                logger.info(f"[SurgeAlertScheduler] Cleared {len(removed)} old alerts: {removed}")

        except Exception as e:
            logger.error(f"[SurgeAlertScheduler] Error in check_and_alert: {e}")

    async def run(self):
        """
        Run scheduler loop (blocking)
        """
        logger.info(f"[SurgeAlertScheduler] Starting scheduler loop (interval: {self.check_interval}s)")

        # Initial check
        await self.check_and_alert()

        # Periodic check
        while True:
            try:
                await asyncio.sleep(self.check_interval)
                await self.check_and_alert()

            except KeyboardInterrupt:
                logger.info("[SurgeAlertScheduler] Stopped by user")
                break
            except Exception as e:
                logger.error(f"[SurgeAlertScheduler] Error in run loop: {e}")
                # Wait and retry
                await asyncio.sleep(60)


async def main():
    """Main entry point"""
    import os

    print("\n" + "="*60)
    print("CoinPulse 급등 예측 알림 시스템")
    print("="*60 + "\n")

    # Check Telegram token
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
        print("\n설정 방법:")
        print("1. @BotFather에게서 봇 토큰 받기")
        print("2. .env 파일에 추가:")
        print("   TELEGRAM_BOT_TOKEN=your_bot_token_here")
        return

    # Check library
    if not TELEGRAM_AVAILABLE:
        print("[ERROR] python-telegram-bot 라이브러리가 설치되지 않았습니다.")
        print("\n설치 방법:")
        print("   pip install python-telegram-bot")
        return

    # Initialize bot
    print("[INFO] 텔레그램 봇 초기화 중...")
    telegram_bot = SurgeTelegramBot(token)
    await telegram_bot.initialize()

    # Initialize scheduler
    print("[INFO] 급등 예측 스케줄러 초기화 중...")
    scheduler = SurgeAlertScheduler(telegram_bot, check_interval=300)  # 5 minutes

    print("\n" + "="*60)
    print("시스템 시작!")
    print("="*60)
    print(f"• 모니터링 코인: {len(scheduler.monitor_coins)}개")
    print(f"• 체크 주기: {scheduler.check_interval}초 (5분)")
    print(f"• 최소 점수: {scheduler.min_score}점")
    print("\n텔레그램 봇 명령어:")
    print("  /start - 알림 시작")
    print("  /stop - 알림 중지")
    print("  /status - 현재 급등 후보")
    print("  /stats - 백테스트 통계")
    print("  /help - 도움말")
    print("="*60 + "\n")

    # Start bot polling and scheduler concurrently
    try:
        await asyncio.gather(
            telegram_bot.start_polling(),
            scheduler.run()
        )
    except KeyboardInterrupt:
        print("\n[INFO] 시스템을 종료합니다...")


if __name__ == "__main__":
    asyncio.run(main())
