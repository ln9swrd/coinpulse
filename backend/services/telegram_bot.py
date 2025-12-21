"""
텔레그램 알림 봇

급등 예측 후보 발견 시 실시간 알림을 텔레그램으로 전송
"""
import os
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import logging

try:
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("[TelegramBot] python-telegram-bot not installed. Run: pip install python-telegram-bot")

# Logging setup
logging.basicConfig(
    format='[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SurgeTelegramBot:
    """급등 예측 텔레그램 봇"""

    def __init__(self, token: str = None):
        """
        Initialize Telegram bot

        Args:
            token: Telegram bot token (from @BotFather)
        """
        if not TELEGRAM_AVAILABLE:
            raise ImportError("python-telegram-bot is required. Install with: pip install python-telegram-bot")

        self.token = token or os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")

        self.base_url = os.getenv('BASE_URL', 'https://coinpulse.sinsi.ai')
        self.app = None
        self.bot = None
        self.subscribers = set()  # Set of chat_ids to send notifications
        self.min_score = 60  # Minimum score to send alert

        logger.info("[TelegramBot] Initialized")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /start command - Welcome message
        """
        chat_id = update.effective_chat.id
        self.subscribers.add(chat_id)

        welcome_message = """
🚀 *CoinPulse 급등 예측 알림 봇*

검증된 알고리즘 (81.25% 적중률)으로
실시간 급등 후보를 *무료*로 알려드립니다!

📊 *백테스트 검증 결과*
• 적중률: 81.25% ✅
• 평균 수익률: +19.12% 📈
• 총 거래: 16건 (13승 3패)
• 보유 기간: 3일
• 검증 기간: 2024.11-12월

🔔 *알림 작동 방식*
• 5분마다 30개 인기 코인 자동 분석
• 60점 이상 급등 후보 발견 시 즉시 알림
• 중복 알림 방지 (같은 코인 하루 1회)

📢 *명령어*
/start - 알림 시작
/stop - 알림 중지
/link - CoinPulse 계정 연동
/status - 현재 급등 후보 확인
/stats - 백테스트 통계
/help - 도움말

🌐 *웹사이트*
https://coinpulse.sinsi.ai
(PC/모바일에서 실시간 차트 & 자동매매)

💬 *친구에게 공유하기*
수익 기회를 친구와 함께!
이 봇 링크를 공유하세요:
https://t.me/coinpulse_surge_sinsi_bot

⚠️ *주의사항*
이 알림은 투자 권유가 아닙니다.
모든 투자 책임은 본인에게 있습니다.
        """

        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown'
        )

        logger.info(f"[TelegramBot] New subscriber: {chat_id}")

    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /stop command - Unsubscribe
        """
        chat_id = update.effective_chat.id
        self.subscribers.discard(chat_id)

        await update.message.reply_text(
            "알림이 중지되었습니다.\n"
            "/start 명령어로 다시 시작할 수 있습니다."
        )

        logger.info(f"[TelegramBot] Unsubscribed: {chat_id}")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /status command - Current surge candidates
        """
        # This would call the surge prediction API
        # For now, return placeholder
        await update.message.reply_text(
            f"🔍 현재 급등 후보를 조회 중...\n"
            f"웹 UI에서 확인: {self.base_url}/surge_monitoring.html"
        )

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /stats command - Backtest statistics
        """
        stats_message = """
📊 *백테스트 검증 결과*
기간: 2024-11-13 ~ 2024-12-07 (4주)

✅ *승률*: 81.25% (13승 3패)
📈 *평균 수익률*: +19.12%
💰 *평균 수익* (승리): +24.19%
📉 *평균 손실* (실패): -2.84%
🎯 *Risk/Reward*: 8.5:1

🏆 *최고 수익*
KRW-XLM: +110.51% (2024-11-20)

📌 *보유 전략*
• 보유 기간: 3일
• 최소 점수: 60점
• 5가지 지표 분석

상세 결과: {self.base_url}/surge_monitoring.html
        """

        await update.message.reply_text(
            stats_message,
            parse_mode='Markdown'
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /help command - Help message
        """
        help_message = """
📚 *CoinPulse 급등 예측 봇 사용법*

*명령어 목록*
/start - 알림 시작
/stop - 알림 중지
/link - CoinPulse 계정 연동
/status - 현재 급등 후보 확인
/stats - 백테스트 통계
/help - 이 도움말

*알림 기준*
• 점수 60점 이상
• 5가지 기술적 지표 분석
  - 거래량 (Volume)
  - RSI
  - 지지선 (Support)
  - 추세 (Trend)
  - 모멘텀 (Momentum)

*투자 시 유의사항*
1. 과거 성과 ≠ 미래 보장
2. 투자 권유 아님
3. 투자 책임은 본인에게
4. 손절 기준 명시 권장 (-5%)
5. 분산 투자 권장

문의: https://github.com/your-repo/coinpulse
        """

        await update.message.reply_text(
            help_message,
            parse_mode='Markdown'
        )

    async def link_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /link command - Link Telegram account to CoinPulse user account

        Usage: /link <6-digit-code>
        """
        chat_id = update.effective_chat.id
        telegram_username = update.effective_user.username

        # Check if code is provided
        if not context.args or len(context.args) == 0:
            await update.message.reply_text(
                "🔗 *Telegram 계정 연동*\n\n"
                "CoinPulse 계정과 Telegram을 연동하여 트레이딩 시그널 알림을 받으세요!\n\n"
                "*사용법:*\n"
                "1. CoinPulse 웹사이트에서 로그인\n"
                "2. 설정 페이지에서 연동 코드 생성\n"
                "3. `/link <코드>` 명령어로 연동\n\n"
                "*예시:*\n"
                "`/link 123456`\n\n"
                "🌐 *웹사이트*\n"
                f"{self.base_url}/settings.html",
                parse_mode='Markdown'
            )
            return

        # Get the code
        code = context.args[0]

        # Validate code format (6 digits)
        if not code.isdigit() or len(code) != 6:
            await update.message.reply_text(
                "❌ *잘못된 코드 형식*\n\n"
                "연동 코드는 6자리 숫자여야 합니다.\n"
                "예: `/link 123456`",
                parse_mode='Markdown'
            )
            return

        # Call the verification API
        try:
            import requests

            verify_url = f"{self.base_url}/api/telegram/link/verify"
            payload = {
                'code': code,
                'telegram_chat_id': str(chat_id),
                'telegram_username': telegram_username
            }

            response = requests.post(verify_url, json=payload, timeout=10)
            data = response.json()

            if response.status_code == 200 and data.get('success'):
                user_info = data.get('user', {})
                await update.message.reply_text(
                    "✅ *연동 성공!*\n\n"
                    f"계정: {user_info.get('email', 'Unknown')}\n"
                    f"Telegram: @{telegram_username}\n\n"
                    "이제 트레이딩 시그널 알림을 받으실 수 있습니다! 🎉\n\n"
                    "🔔 *알림 설정*\n"
                    f"{self.base_url}/settings.html",
                    parse_mode='Markdown'
                )
                logger.info(f"[TelegramBot] Account linked: chat_id={chat_id}, user={user_info.get('email')}")
            else:
                error_message = data.get('error', 'Unknown error')
                await update.message.reply_text(
                    f"❌ *연동 실패*\n\n"
                    f"{error_message}\n\n"
                    "다시 시도해주세요.",
                    parse_mode='Markdown'
                )
                logger.warning(f"[TelegramBot] Link failed: {error_message}")

        except Exception as e:
            await update.message.reply_text(
                "❌ *오류 발생*\n\n"
                "서버 연결에 실패했습니다.\n"
                "잠시 후 다시 시도해주세요.",
                parse_mode='Markdown'
            )
            logger.error(f"[TelegramBot] Link error: {e}")

    async def send_signal_notification(self, signal_data: Dict):
        """
        Send trading signal notification to a specific user

        Args:
            signal_data: Signal data
                {
                    "telegram_chat_id": 123456,
                    "signal_id": "SIGNAL-20251221-001",
                    "market": "KRW-XRP",
                    "confidence": 85,
                    "entry_price": 650,
                    "target_price": 682,
                    "stop_loss": 637,
                    "reason": "...",
                    "is_bonus": False
                }
        """
        if not self.bot:
            logger.warning("[TelegramBot] Bot not initialized, skipping signal notification")
            return

        chat_id = signal_data.get('telegram_chat_id')
        if not chat_id:
            logger.warning("[TelegramBot] No telegram_chat_id provided")
            return

        # Format signal message
        market = signal_data['market']
        confidence = signal_data['confidence']
        entry_price = signal_data['entry_price']
        target_price = signal_data['target_price']
        stop_loss = signal_data['stop_loss']
        reason = signal_data.get('reason', 'High-confidence surge prediction')
        is_bonus = signal_data.get('is_bonus', False)

        # Calculate expected return
        expected_return = ((target_price - entry_price) / entry_price) * 100

        # Emoji based on confidence
        confidence_emoji = "🔥" if confidence >= 85 else "⚡"
        bonus_text = "🎁 *BONUS SIGNAL*\n\n" if is_bonus else ""

        signal_message = f"""
{bonus_text}{confidence_emoji} *Trading Signal Alert*

*Market*: {market}
*Confidence*: {confidence}%

*Entry Price*: KRW {entry_price:,}
*Target Price*: KRW {target_price:,}
*Stop Loss*: KRW {stop_loss:,}

*Expected Return*: +{expected_return:.2f}%

*Reason*: {reason}

*Valid Until*: 4 hours from now

🌐 *View Chart*
https://coinpulse.sinsi.ai/trading_chart.html?market={market}

⚠️ This is not investment advice.
All trading decisions and risks are your own.
        """

        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=signal_message,
                parse_mode='Markdown'
            )
            logger.info(f"[TelegramBot] Signal notification sent to {chat_id}: {market} ({confidence}%)")
        except Exception as e:
            logger.error(f"[TelegramBot] Failed to send signal notification to {chat_id}: {e}")

    async def send_surge_alert(self, candidate: Dict):
        """
        Send surge alert to all subscribers

        Args:
            candidate: Surge candidate data
                {
                    "market": "KRW-XLM",
                    "score": 80,
                    "current_price": 176.5,
                    "signals": {...},
                    "recommendation": "strong_buy"
                }
        """
        if not self.bot:
            logger.warning("[TelegramBot] Bot not initialized, skipping alert")
            return

        # Format alert message
        market = candidate['market']
        score = candidate['score']
        price = candidate['current_price']
        signals = candidate['signals']

        # Emoji based on score
        score_emoji = "🔥" if score >= 70 else "⚡"

        alert_message = f"""
{score_emoji} *급등 예측 알림*

*코인*: {market}
*점수*: {score}점
*현재가*: {price:,.0f} KRW
*추천*: {candidate['recommendation']}

📊 *시그널 분석*
• 거래량: {signals['volume']['description']} ({signals['volume']['score']}점)
• RSI: {signals['rsi']['description']} ({signals['rsi']['score']}점)
• 지지선: {signals['support']['description']} ({signals['support']['score']}점)
• 추세: {signals['trend']['description']} ({signals['trend']['score']}점)
• 모멘텀: {signals['momentum']['description']} ({signals['momentum']['score']}점)

⏰ 발견 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🌐 *차트 보기*
https://coinpulse.sinsi.ai/trading_chart.html?market={market}

💬 *친구에게도 알려주세요!*
https://t.me/coinpulse_surge_sinsi_bot

⚠️ 이 알림은 투자 권유가 아닙니다.
투자 책임은 본인에게 있습니다.
        """

        # Send to all subscribers
        for chat_id in list(self.subscribers):
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=alert_message,
                    parse_mode='Markdown'
                )
                logger.info(f"[TelegramBot] Alert sent to {chat_id}: {market} ({score}점)")
            except Exception as e:
                logger.error(f"[TelegramBot] Failed to send to {chat_id}: {e}")
                # Remove invalid chat_id
                self.subscribers.discard(chat_id)

    async def send_execution_notification(self, data: Dict):
        """
        Send signal execution notification to user

        Args:
            data: Execution data
                {
                    "telegram_chat_id": 123456,
                    "type": "execution",
                    "market": "KRW-XRP",
                    "execution_price": 650,
                    "signal_id": "SIGNAL-20251221-001",
                    "executed_at": "2025-12-21T..."
                }
        """
        if not self.bot:
            logger.warning("[TelegramBot] Bot not initialized, skipping execution notification")
            return

        chat_id = data.get('telegram_chat_id')
        if not chat_id:
            return

        market = data.get('market', 'Unknown')
        execution_price = data.get('execution_price', 0)
        signal_id = data.get('signal_id', 'Unknown')
        executed_at = data.get('executed_at', '')

        message = f"""
✅ *시그널 실행 완료*

*코인*: {market}
*실행 가격*: KRW {execution_price:,}
*시그널 ID*: {signal_id}
*실행 시각*: {executed_at[:19]}

📊 포지션이 열렸습니다.
목표가나 손절가에 도달하면 알림을 받으실 수 있습니다.

🌐 *내 시그널 보기*
{self.base_url}/my_signals.html
        """

        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"[TelegramBot] Execution notification sent to {chat_id}: {market}")
        except Exception as e:
            logger.error(f"[TelegramBot] Failed to send execution notification: {e}")

    async def send_close_notification(self, data: Dict):
        """
        Send position close notification to user

        Args:
            data: Close data
                {
                    "telegram_chat_id": 123456,
                    "type": "position_closed",
                    "market": "KRW-XRP",
                    "execution_price": 650,
                    "close_price": 682,
                    "profit_loss": 492,
                    "profit_loss_ratio": 4.92,
                    "close_reason": "target_reached"
                }
        """
        if not self.bot:
            logger.warning("[TelegramBot] Bot not initialized, skipping close notification")
            return

        chat_id = data.get('telegram_chat_id')
        if not chat_id:
            return

        market = data.get('market', 'Unknown')
        execution_price = data.get('execution_price', 0)
        close_price = data.get('close_price', 0)
        profit_loss = data.get('profit_loss', 0)
        profit_loss_ratio = data.get('profit_loss_ratio', 0)
        close_reason = data.get('close_reason', 'manual')

        # Emoji based on profit/loss
        if profit_loss >= 0:
            emoji = "🎉" if profit_loss_ratio >= 5 else "✅"
            status = "수익 실현"
        else:
            emoji = "⚠️"
            status = "손실 확정"

        reason_text = {
            'target_reached': '목표가 도달',
            'stop_loss': '손절가 도달',
            'manual': '수동 청산'
        }.get(close_reason, close_reason)

        message = f"""
{emoji} *포지션 청산 완료*

*코인*: {market}
*실행 가격*: KRW {execution_price:,}
*청산 가격*: KRW {close_price:,}

*손익*: {profit_loss:+,.0f} KRW ({profit_loss_ratio:+.2f}%)
*청산 사유*: {reason_text}

{status}되었습니다.

🌐 *거래 내역 보기*
{self.base_url}/my_signals.html
        """

        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"[TelegramBot] Close notification sent to {chat_id}: {market} ({profit_loss_ratio:+.2f}%)")
        except Exception as e:
            logger.error(f"[TelegramBot] Failed to send close notification: {e}")

    async def initialize(self):
        """Initialize bot application"""
        self.app = Application.builder().token(self.token).build()
        self.bot = self.app.bot

        # Register command handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("stop", self.stop_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("link", self.link_command))

        logger.info("[TelegramBot] Bot initialized with command handlers")

    async def start_polling(self):
        """Start bot polling (blocking)"""
        if not self.app:
            await self.initialize()

        logger.info("[TelegramBot] Starting polling...")
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("[TelegramBot] Stopping...")
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()

    def run(self):
        """Run bot (blocking)"""
        asyncio.run(self.start_polling())


# Standalone bot runner
if __name__ == "__main__":
    import sys

    print("\n" + "="*60)
    print("CoinPulse 텔레그램 알림 봇")
    print("="*60 + "\n")

    # Check token
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")
        print("\n설정 방법:")
        print("1. @BotFather에게서 봇 토큰 받기")
        print("2. .env 파일에 추가:")
        print("   TELEGRAM_BOT_TOKEN=your_bot_token_here")
        print("3. 또는 환경 변수 설정:")
        print("   set TELEGRAM_BOT_TOKEN=your_bot_token_here")
        print("\n자세한 내용: https://core.telegram.org/bots#creating-a-new-bot")
        sys.exit(1)

    # Check library
    if not TELEGRAM_AVAILABLE:
        print("[ERROR] python-telegram-bot 라이브러리가 설치되지 않았습니다.")
        print("\n설치 방법:")
        print("   pip install python-telegram-bot")
        sys.exit(1)

    # Start bot
    print("[INFO] 텔레그램 봇을 시작합니다...")
    print(f"[INFO] 구독자에게 /start 명령어를 보내도록 안내하세요.")
    print("="*60 + "\n")

    bot = SurgeTelegramBot(token)
    bot.run()
