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
from backend.database.connection import get_db_session
from backend.models.surge_candidates_cache_models import SurgeCandidatesCache
from backend.services.websocket_service import get_websocket_service
from backend.services.dynamic_market_selector import get_market_selector

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

        # Initialize Dynamic Market Selector (50 coins, updated daily)
        self.market_selector = get_market_selector(target_count=50)
        self.monitor_coins = self.market_selector.get_markets(force_update=True, update_interval_hours=24)

        # Track alerted candidates (to avoid duplicate alerts)
        self.alerted_candidates: Set[str] = set()  # Set of market names
        self.min_score = 70  # Raised from 60 to improve signal quality

        logger.info(f"[SurgeAlertScheduler] Initialized (interval: {check_interval}s, coins: {len(self.monitor_coins)})")
        logger.info(f"[SurgeAlertScheduler] Dynamic market selection enabled (auto-update every 24h)")

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
                    candidates.append({
                        'market': market,
                        'coin': coin,
                        'score': analysis['score'],
                        'current_price': int(current_price),
                        'signals': analysis['signals'],
                        'recommendation': analysis['recommendation'],
                        'analysis': analysis  # Store full analysis for cache
                    })

                # Rate limit
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"[SurgeAlertScheduler] Error analyzing {market}: {e}")
                continue

        return candidates

    def is_already_alerted_recently(self, market: str, hours: int = 24) -> bool:
        """
        Check if market was already alerted within recent hours in database

        This prevents duplicate alerts for the same coin within a short time period.
        Default: 24 hours (prevents multiple alerts per day for same coin)

        Args:
            market: Market symbol (e.g., 'KRW-BTC')
            hours: Number of hours to check (default: 24)

        Returns:
            True if already alerted within recent hours, False otherwise
        """
        try:
            with get_db_session() as session:
                cutoff_time = datetime.now() - timedelta(hours=hours)

                result = session.execute(
                    text("""
                        SELECT COUNT(*) FROM surge_alerts
                        WHERE market = :market
                        AND sent_at >= :cutoff_time
                    """),
                    {'market': market, 'cutoff_time': cutoff_time}
                )
                count = result.scalar()

                if count > 0:
                    logger.debug(f"[SurgeAlertScheduler] {market} already alerted within {hours} hours")

                return count > 0

        except Exception as e:
            logger.error(f"[SurgeAlertScheduler] Error checking recent alerts: {e}")
            return False  # Default to False to allow saving

    def save_to_database(self, candidate: Dict):
        """
        Save surge alert to database with entry/target/stop-loss prices

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

                # Calculate prices
                current_price = int(candidate.get('current_price', 0))
                entry_price = current_price  # Entry price = current price at prediction time
                target_price = int(candidate.get('target_price', current_price * 1.05))  # Default: +5%
                stop_loss_price = int(current_price * 0.95)  # Default: -5% stop loss
                expected_return = candidate.get('expected_return', 0.05)

                # Prepare alert data
                query = text("""
                    INSERT INTO surge_alerts (
                        user_id, market, coin, confidence, signal_type,
                        current_price, entry_price, target_price, stop_loss_price,
                        expected_return, reason, alert_message, telegram_sent,
                        sent_at, week_number, auto_traded, status
                    ) VALUES (
                        :user_id, :market, :coin, :confidence, :signal_type,
                        :current_price, :entry_price, :target_price, :stop_loss_price,
                        :expected_return, :reason, :alert_message, :telegram_sent,
                        :sent_at, :week_number, :auto_traded, :status
                    )
                """)

                # Use system user_id = 1 (or admin) for surge alerts
                params = {
                    'user_id': 1,  # System user
                    'market': candidate['market'],
                    'coin': coin,
                    'confidence': candidate['score'] / 100.0,  # Convert score to 0-1 range
                    'signal_type': 'surge',
                    'current_price': current_price,
                    'entry_price': entry_price,
                    'target_price': target_price,
                    'stop_loss_price': stop_loss_price,
                    'expected_return': expected_return,
                    'reason': candidate.get('reason', ''),
                    'alert_message': f"급등 예측: {candidate['market']} (신뢰도: {candidate['score']}점)",
                    'telegram_sent': True,
                    'sent_at': now,
                    'week_number': week_number,
                    'auto_traded': False,
                    'status': 'pending'  # Initial status
                }

                session.execute(query, params)
                session.commit()

                logger.info(f"[SurgeAlertScheduler] Saved to DB: {candidate['market']} "
                           f"(Entry: {entry_price:,}원, Target: {target_price:,}원, Stop: {stop_loss_price:,}원)")

        except Exception as e:
            logger.error(f"[SurgeAlertScheduler] Failed to save to DB: {e}")

    async def close_pending_signals(self):
        """
        Check pending signals and close them based on user settings:
        - Take profit:達成時即時賣出
        - Stop loss: 達成時即時賣出
        - Peak tracking: 피크에서 일정 비율 하락 시 매도
        - Time expiry: 48시간 경과 시 강제 종료

        Uses user's auto-trading settings for dynamic thresholds.
        """
        try:
            with get_db_session() as session:
                # Get all pending signals with user settings
                query = text("""
                    SELECT
                        sa.id, sa.user_id, sa.market, sa.coin,
                        sa.entry_price, sa.peak_price, sa.sent_at,
                        ats.take_profit_percent, ats.stop_loss_percent
                    FROM surge_alerts sa
                    LEFT JOIN surge_auto_trading_settings ats ON sa.user_id = ats.user_id
                    WHERE sa.status = 'pending'
                """)
                result = session.execute(query)
                pending_signals = [dict(row._mapping) for row in result]

                if not pending_signals:
                    return

                logger.info(f"[SurgeAlertScheduler] Checking {len(pending_signals)} pending signals for closure")

                # Batch fetch current prices (avoid rate limit)
                unique_markets = list(set([s['market'] for s in pending_signals]))
                all_prices = {}

                # Upbit allows up to 100 markets per request
                for i in range(0, len(unique_markets), 100):
                    batch_markets = unique_markets[i:i+100]
                    try:
                        ticker_data = self.upbit_api.get_ticker(batch_markets)
                        for ticker in ticker_data:
                            all_prices[ticker['market']] = int(ticker.get('trade_price', 0))
                    except Exception as e:
                        logger.warning(f"[SurgeAlertScheduler] Failed to fetch batch prices: {e}")

                logger.info(f"[SurgeAlertScheduler] Fetched prices for {len(all_prices)} markets in {(len(unique_markets) + 99) // 100} batch(es)")

                closed_count = 0
                for signal in pending_signals:
                    signal_id = signal['id']
                    market = signal['market']
                    entry_price = signal['entry_price']
                    peak_price = signal.get('peak_price') or entry_price
                    entry_time = signal['sent_at']

                    # User settings (default if not set)
                    take_profit_pct = signal.get('take_profit_percent') or 10.0  # Default: +10%
                    stop_loss_pct = signal.get('stop_loss_percent') or -5.0      # Default: -5%

                    # Calculate elapsed time
                    hours_elapsed = (datetime.now() - entry_time).total_seconds() / 3600

                    # Get current price from batch cache
                    current_price = all_prices.get(market)
                    if not current_price or current_price == 0:
                        logger.warning(f"[SurgeAlertScheduler] No price data for {market}, skipping")
                        continue

                    # Update peak price if current is higher
                    if current_price > peak_price:
                        peak_price = current_price

                    # Calculate profit percentage
                    profit_pct = ((current_price - entry_price) / entry_price) * 100
                    peak_profit_pct = ((peak_price - entry_price) / entry_price) * 100

                    # Determine if should close (user-settings based)
                    should_close = False
                    close_reason = None

                    # 1. Take profit reached - INSTANT SELL
                    if profit_pct >= take_profit_pct:
                        should_close = True
                        close_reason = f'Take profit (+{profit_pct:.1f}% >= +{take_profit_pct:.1f}%)'

                    # 2. Stop loss reached - INSTANT SELL
                    elif profit_pct <= stop_loss_pct:
                        should_close = True
                        close_reason = f'Stop loss ({profit_pct:.1f}% <= {stop_loss_pct:.1f}%)'

                    # 3. Peak tracking - protect profits
                    elif peak_price > entry_price:
                        # If peak reached take_profit target, allow 8% drop from peak
                        if peak_profit_pct >= take_profit_pct:
                            if current_price < peak_price * 0.92:  # 8% drop from peak
                                should_close = True
                                close_reason = f'Peak profit secured (+{peak_profit_pct:.1f}% peak, now +{profit_pct:.1f}%)'
                        # If peak not reached target yet, allow 5% drop from peak
                        else:
                            if current_price < peak_price * 0.95:  # 5% drop from peak
                                should_close = True
                                close_reason = f'Drop from peak (+{peak_profit_pct:.1f}% → +{profit_pct:.1f}%)'

                    # 4. Time expiry - force close after 48 hours
                    elif hours_elapsed >= 48:
                        should_close = True
                        close_reason = f'Expired (48h, {profit_pct:+.1f}%)'

                    if should_close:
                        # Calculate profit
                        profit_pct = ((current_price - entry_price) / entry_price) * 100
                        status = 'win' if profit_pct > 0 else 'lose'

                        # Update signal
                        update_query = text("""
                            UPDATE surge_alerts
                            SET peak_price = :peak_price,
                                exit_price = :exit_price,
                                close_reason = :close_reason,
                                status = :status,
                                closed_at = NOW()
                            WHERE id = :signal_id
                        """)

                        session.execute(update_query, {
                            'signal_id': signal_id,
                            'peak_price': peak_price,
                            'exit_price': current_price,
                            'close_reason': close_reason,
                            'status': status
                        })
                        session.commit()

                        closed_count += 1
                        logger.info(
                            f"[SurgeAlertScheduler] Closed {market} as '{status}': "
                            f"Entry={entry_price:,} → Peak={peak_price:,} → Exit={current_price:,} "
                            f"({profit_pct:+.1f}%) | {close_reason}"
                        )
                    else:
                        # Just update peak price if higher
                        if current_price > peak_price:
                            update_query = text("""
                                UPDATE surge_alerts
                                SET peak_price = :peak_price
                                WHERE id = :signal_id
                            """)
                            session.execute(update_query, {
                                'signal_id': signal_id,
                                'peak_price': peak_price
                            })
                            session.commit()

                if closed_count > 0:
                    logger.info(f"[SurgeAlertScheduler] Auto-closed {closed_count} signals")

        except Exception as e:
            logger.error(f"[SurgeAlertScheduler] Error in close_pending_signals: {e}")

    def update_candidates_cache(self, candidates: List[Dict]):
        """
        Update surge candidates cache table

        NEW LOGIC (2025-12-26):
        - Keep ALL candidates with active surge_alerts (even if score < 60)
        - Only delete candidates that are closed/expired in surge_alerts
        - This ensures "단타 감지" and "단타신호 이력" show same active signals

        Args:
            candidates: List of analyzed candidates (score >= 60)
        """
        try:
            with get_db_session() as session:
                # Get active markets from surge_alerts (status = pending or active)
                active_alerts_query = text("""
                    SELECT DISTINCT market
                    FROM surge_alerts
                    WHERE status IN ('pending', 'active')
                      AND market IS NOT NULL
                """)
                result = session.execute(active_alerts_query)
                active_markets = {row[0] for row in result.fetchall()}

                logger.info(f"[SurgeAlertScheduler] Found {len(active_markets)} active signals in DB")

                # Get current high-score markets (>= 60)
                current_markets = {c['market'] for c in candidates}

                # Combined: keep active alerts + new high-score candidates
                keep_markets = active_markets | current_markets

                # Delete ONLY candidates that are NOT in keep_markets
                deleted = session.query(SurgeCandidatesCache).filter(
                    ~SurgeCandidatesCache.market.in_(keep_markets)
                ).delete(synchronize_session=False)

                if deleted > 0:
                    logger.info(f"[SurgeAlertScheduler] Removed {deleted} closed/expired candidates from cache")

                # Upsert new high-score candidates (>= 60)
                for candidate in candidates:
                    market = candidate['market']
                    coin = candidate.get('coin', market.replace('KRW-', ''))

                    # Check if exists
                    existing = session.query(SurgeCandidatesCache).filter_by(market=market).first()

                    if existing:
                        # Update
                        existing.coin = coin
                        existing.score = candidate['score']
                        existing.current_price = candidate['current_price']
                        existing.recommendation = candidate['recommendation']
                        existing.signals = candidate.get('signals', {})
                        existing.analysis_result = candidate.get('analysis', {})
                        existing.analyzed_at = datetime.now()
                        existing.updated_at = datetime.now()
                    else:
                        # Insert
                        cache_record = SurgeCandidatesCache(
                            market=market,
                            coin=coin,
                            score=candidate['score'],
                            current_price=candidate['current_price'],
                            recommendation=candidate['recommendation'],
                            signals=candidate.get('signals', {}),
                            analysis_result=candidate.get('analysis', {}),
                            analyzed_at=datetime.now()
                        )
                        session.add(cache_record)

                # Keep existing cache for active alerts (even if score < 60 now)
                # Just update their analyzed_at to show they were checked
                for market in active_markets - current_markets:
                    existing = session.query(SurgeCandidatesCache).filter_by(market=market).first()
                    if existing:
                        existing.updated_at = datetime.now()
                        logger.debug(f"[SurgeAlertScheduler] Kept {market} in cache (active alert, score < 60)")

                session.commit()
                logger.info(f"[SurgeAlertScheduler] Cache updated: {len(candidates)} high-score + {len(active_markets - current_markets)} active (low-score)")

        except Exception as e:
            logger.error(f"[SurgeAlertScheduler] Failed to update cache: {e}")

    async def check_and_alert(self):
        """
        Check for new surge candidates and send alerts
        """
        logger.info("[SurgeAlertScheduler] Checking for surge candidates...")

        try:
            # Check and close pending signals (auto-close system)
            await self.close_pending_signals()

            # Update market list if needed (every 24 hours)
            updated_markets = self.market_selector.get_markets(force_update=False, update_interval_hours=24)
            if updated_markets != self.monitor_coins:
                logger.info(f"[SurgeAlertScheduler] Market list updated: {len(updated_markets)} coins")
                self.monitor_coins = updated_markets

            # Get current candidates
            candidates = self.get_surge_candidates()

            # Update cache (always, even if empty) for /api/surge-candidates
            self.update_candidates_cache(candidates if candidates else [])

            if not candidates:
                logger.info("[SurgeAlertScheduler] No candidates found")
                return

            logger.info(f"[SurgeAlertScheduler] Found {len(candidates)} candidates")

            # Send alerts for new candidates
            new_alerts = 0
            new_db_records = 0
            for candidate in candidates:
                market = candidate['market']

                # Check if already sent telegram alert (in-memory check for telegram spam prevention)
                telegram_already_sent = market in self.alerted_candidates

                # Check if already alerted within recent hours (24 hours by default)
                # This prevents duplicate alerts for the same coin within a day
                db_already_alerted = self.is_already_alerted_recently(market, hours=24)

                # Send telegram alert only if not already sent (in-memory check)
                if not telegram_already_sent:
                    await self.telegram_bot.send_surge_alert(candidate)
                    self.alerted_candidates.add(market)
                    new_alerts += 1
                    logger.info(f"[SurgeAlertScheduler] Telegram alert sent: {market} ({candidate['score']}점)")

                    # Also send WebSocket notification (broadcast to all users)
                    try:
                        ws_service = get_websocket_service()
                        ws_service.broadcast_surge_alert(candidate)
                        logger.info(f"[SurgeAlertScheduler] WebSocket alert broadcast: {market}")
                    except Exception as ws_error:
                        logger.warning(f"[SurgeAlertScheduler] WebSocket not available: {ws_error}")

                # Save to database only if not already alerted within recent 24 hours
                if not db_already_alerted:
                    self.save_to_database(candidate)
                    new_db_records += 1
                    logger.info(f"[SurgeAlertScheduler] Saved to DB: {market}")
                else:
                    logger.debug(f"[SurgeAlertScheduler] {market} already alerted within 24h, skipping save")

            if new_alerts > 0:
                logger.info(f"[SurgeAlertScheduler] Sent {new_alerts} new telegram alerts")
            if new_db_records > 0:
                logger.info(f"[SurgeAlertScheduler] Saved {new_db_records} new DB records")

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
