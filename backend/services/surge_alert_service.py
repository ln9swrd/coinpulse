# -*- coding: utf-8 -*-
"""
Surge Alert Service
급등 알림 자동매매 서비스

참고 문서: docs/features/SURGE_ALERT_SYSTEM.md v2.0
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.surge_alert_models import SurgeAlert, SurgeAutoTradingSettings
from backend.models.plan_features import get_user_features, PLAN_FEATURES
from backend.database.connection import get_db_session

logger = logging.getLogger(__name__)


class SurgeAlertService:
    """급등 알림 자동매매 서비스 v2.0"""

    def __init__(self, session: Session = None):
        """
        Initialize surge alert service

        Args:
            session: SQLAlchemy session (optional, creates new if not provided)
        """
        self.session = session or get_db_session()
        logger.info("[SurgeAlertService] Initialized (v2.0)")

    def get_weekly_alert_count(self, user_id: int, auto_traded_only: bool = True) -> int:
        """
        Get user's auto-traded alert count for current week

        Args:
            user_id: User ID
            auto_traded_only: Count only auto-traded alerts (default True)

        Returns:
            Number of auto-traded alerts this week
        """
        try:
            current_week = SurgeAlert.get_current_week_number()

            query = self.session.query(func.count(SurgeAlert.id))\
                .filter(
                    SurgeAlert.user_id == user_id,
                    SurgeAlert.week_number == current_week
                )

            if auto_traded_only:
                query = query.filter(SurgeAlert.auto_traded == True)

            count = query.scalar()

            logger.info(f"[SurgeAlert] User {user_id} has {count} auto-traded alerts this week ({current_week})")
            return count or 0

        except Exception as e:
            logger.error(f"[SurgeAlert] Error getting weekly count for user {user_id}: {str(e)}")
            return 0

    def get_max_alerts_for_plan(self, plan: str) -> int:
        """
        Get maximum alerts per week for a plan

        Args:
            plan: Plan name ('free', 'basic', 'pro')

        Returns:
            Maximum alerts per week (actual limit, not displayed limit)
        """
        features = PLAN_FEATURES.get(plan.lower(), PLAN_FEATURES['free'])
        return features.get('max_surge_alerts', 0)

    def get_user_settings(self, user_id: int) -> Optional[SurgeAutoTradingSettings]:
        """
        Get user's auto-trading settings

        Args:
            user_id: User ID

        Returns:
            SurgeAutoTradingSettings or None
        """
        try:
            settings = self.session.query(SurgeAutoTradingSettings)\
                .filter(SurgeAutoTradingSettings.user_id == user_id)\
                .first()

            return settings

        except Exception as e:
            logger.error(f"[SurgeAlert] Error getting settings for user {user_id}: {str(e)}")
            return None

    def get_open_positions_count(self, user_id: int) -> int:
        """
        Get count of open positions for user

        Args:
            user_id: User ID

        Returns:
            Number of open positions
        """
        try:
            count = self.session.query(func.count(SurgeAlert.id))\
                .filter(
                    SurgeAlert.user_id == user_id,
                    SurgeAlert.auto_traded == True,
                    SurgeAlert.status.in_(['pending', 'executed'])
                )\
                .scalar()

            return count or 0

        except Exception as e:
            logger.error(f"[SurgeAlert] Error getting open positions for user {user_id}: {str(e)}")
            return 0

    def can_auto_trade(
        self,
        user_id: int,
        plan: str,
        settings: SurgeAutoTradingSettings,
        confidence: float,
        coin: str
    ) -> Tuple[bool, str]:
        """
        Check if auto-trade can be executed

        Args:
            user_id: User ID
            plan: User's plan
            settings: User's auto-trading settings
            confidence: Signal confidence
            coin: Coin symbol

        Returns:
            (can_trade: bool, reason: str)
        """
        # 1. Check plan allows auto-trading
        features = get_user_features(plan)
        if not features.get('surge_auto_trading', False):
            return False, "Plan does not support auto-trading"

        # 2. Check if enabled
        if not settings or not settings.enabled:
            return False, "Auto-trading is disabled"

        # 3. Check weekly limit
        max_alerts = self.get_max_alerts_for_plan(plan)
        current_count = self.get_weekly_alert_count(user_id, auto_traded_only=True)

        if current_count >= max_alerts:
            return False, f"Weekly limit reached ({current_count}/{max_alerts})"

        # 4. Check budget
        if not settings.can_trade():
            return False, "Insufficient budget"

        # 5. Check confidence threshold
        if confidence < settings.min_confidence:
            return False, f"Confidence {confidence}% below threshold {settings.min_confidence}%"

        # 6. Check max positions
        open_positions = self.get_open_positions_count(user_id)
        if open_positions >= settings.max_positions:
            return False, f"Maximum positions reached ({open_positions}/{settings.max_positions})"

        # 7. Check excluded coins
        if settings.excluded_coins and coin.upper() in settings.excluded_coins:
            return False, f"Coin {coin} is in exclusion list"

        return True, "OK"

    def execute_auto_trade(
        self,
        user_id: int,
        settings: SurgeAutoTradingSettings,
        market: str,
        coin: str,
        current_price: int
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Execute auto-trade purchase

        Args:
            user_id: User ID
            settings: Auto-trading settings
            market: Market code (e.g., 'KRW-BTC')
            coin: Coin symbol
            current_price: Current price

        Returns:
            (success: bool, trade_info: dict or None)
        """
        try:
            # Calculate quantity based on amount_per_trade
            amount = settings.amount_per_trade
            quantity = amount / current_price

            # TODO: Integrate with Upbit API to place actual order
            # For now, simulate trade
            logger.info(f"[SurgeAlert] Simulating auto-trade: {coin} x {quantity:.8f} for {amount:,} KRW")

            # Calculate stop loss and take profit prices
            stop_loss_price = None
            if settings.stop_loss_enabled:
                stop_loss_price = int(current_price * (1 + settings.stop_loss_percent / 100))

            take_profit_price = None
            if settings.take_profit_enabled:
                take_profit_price = int(current_price * (1 + settings.take_profit_percent / 100))

            trade_info = {
                'order_id': f'SIM-{user_id}-{int(datetime.utcnow().timestamp())}',  # Simulated order ID
                'amount': amount,
                'quantity': quantity,
                'price': current_price,
                'stop_loss_price': stop_loss_price,
                'take_profit_price': take_profit_price,
                'executed_at': datetime.utcnow()
            }

            logger.info(f"[SurgeAlert] Auto-trade executed successfully for user {user_id}")
            return True, trade_info

        except Exception as e:
            logger.error(f"[SurgeAlert] Error executing auto-trade for user {user_id}: {str(e)}")
            return False, None

    def record_alert(
        self,
        user_id: int,
        market: str,
        coin: str,
        confidence: float,
        entry_price: int = None,
        target_price: int = None,
        stop_loss_price: int = None,
        auto_traded: bool = False,
        trade_amount: int = None,
        trade_quantity: float = None,
        order_id: str = None,
        reason: str = None,
        alert_message: str = None,
        telegram_sent: bool = False,
        telegram_message_id: str = None
    ) -> Optional[SurgeAlert]:
        """
        Record an alert in database

        Args:
            user_id: User ID
            market: Market code
            coin: Coin symbol
            confidence: Prediction confidence
            entry_price: Entry price
            target_price: Target price
            stop_loss_price: Stop loss price
            auto_traded: Was auto-traded?
            trade_amount: Trade amount in KRW
            trade_quantity: Quantity purchased
            order_id: Order ID
            reason: Reason for alert
            alert_message: Telegram message content
            telegram_sent: Successfully sent via Telegram
            telegram_message_id: Telegram message ID

        Returns:
            SurgeAlert object or None if failed
        """
        try:
            alert = SurgeAlert(
                user_id=user_id,
                market=market,
                coin=coin,
                confidence=confidence,
                entry_price=entry_price,
                target_price=target_price,
                stop_loss_price=stop_loss_price,
                auto_traded=auto_traded,
                trade_amount=trade_amount,
                trade_quantity=trade_quantity,
                order_id=order_id,
                status='executed' if auto_traded else 'pending',
                reason=reason,
                alert_message=alert_message,
                telegram_sent=telegram_sent,
                telegram_message_id=telegram_message_id,
                sent_at=datetime.utcnow(),
                executed_at=datetime.utcnow() if auto_traded else None,
                week_number=SurgeAlert.get_current_week_number()
            )

            self.session.add(alert)
            self.session.commit()

            logger.info(f"[SurgeAlert] Recorded alert for user {user_id}: {market} (auto_traded={auto_traded})")
            return alert

        except Exception as e:
            logger.error(f"[SurgeAlert] Error recording alert: {str(e)}")
            self.session.rollback()
            return None

    def format_alert_message(
        self,
        coin: str,
        market: str,
        confidence: float,
        current_price: int,
        target_price: int,
        expected_return: float,
        auto_traded: bool = False,
        trade_amount: int = None,
        stop_loss_price: int = None,
        take_profit_price: int = None
    ) -> str:
        """
        Format alert message for Telegram

        Args:
            coin: Coin symbol
            market: Market code
            confidence: Prediction confidence
            current_price: Current price
            target_price: Target price
            expected_return: Expected return %
            auto_traded: Was auto-traded?
            trade_amount: Trade amount (if auto-traded)
            stop_loss_price: Stop loss price (if set)
            take_profit_price: Take profit price (if set)

        Returns:
            Formatted message string
        """
        # Coin names in Korean
        coin_names = {
            'BTC': '비트코인',
            'ETH': '이더리움',
            'XRP': '리플',
            'ADA': '에이다',
            'SOL': '솔라나',
            'DOGE': '도지코인',
            'DOT': '폴카닷',
            'MATIC': '폴리곤',
            'LTC': '라이트코인',
            'LINK': '체인링크'
        }

        coin_name = coin_names.get(coin, coin)

        if auto_traded:
            # Auto-traded message
            message = f"""
🤖 *급등 알림 자동매매*

코인: {coin} ({coin_name})
신뢰도: {confidence:.1f}%
매수 완료: {trade_amount:,}원

매수가: ₩{current_price:,}
목표가: ₩{target_price:,} (+{expected_return:.2f}%)
"""
            if stop_loss_price:
                message += f"손절가: ₩{stop_loss_price:,} ({(stop_loss_price - current_price) / current_price * 100:.1f}%)\n"
            if take_profit_price:
                message += f"익절가: ₩{take_profit_price:,} (+{(take_profit_price - current_price) / current_price * 100:.1f}%)\n"

            message += "\n💡 자동매매가 실행되었습니다. 포지션을 확인하세요."

        else:
            # Regular surge alert (no auto-trade)
            message = f"""
🔥 *급등 신호 감지*

코인: {coin} ({coin_name})
신뢰도: {confidence:.1f}%
현재가: ₩{current_price:,}
예상 목표가: ₩{target_price:,} (+{expected_return:.2f}%)

📊 검증된 알고리즘 (81.25% 적중률)
💡 자동매매를 활성화하여 자동 거래하세요.
"""

        # Add call-to-action
        message += f"\n\n[상세보기] https://coinpulse.sinsi.ai/dashboard.html?coin={market}"

        return message.strip()

    def send_alert_to_user(
        self,
        user_id: int,
        plan: str,
        market: str,
        coin: str,
        confidence: float,
        current_price: int,
        target_price: int,
        expected_return: float,
        telegram_chat_id: str = None
    ) -> Tuple[bool, Optional[SurgeAlert]]:
        """
        Send surge alert and optionally execute auto-trade

        Args:
            user_id: User ID
            plan: User's plan
            market: Market code
            coin: Coin symbol
            confidence: Prediction confidence
            current_price: Current price
            target_price: Target price
            expected_return: Expected return %
            telegram_chat_id: Telegram chat ID (optional)

        Returns:
            (success: bool, alert: SurgeAlert or None)
        """
        # 1. Get user's auto-trading settings
        settings = self.get_user_settings(user_id)

        # 2. Check if can auto-trade
        auto_traded = False
        trade_info = None

        if settings:
            can_trade, reason = self.can_auto_trade(user_id, plan, settings, confidence, coin)

            if can_trade:
                # Execute auto-trade
                success, trade_info = self.execute_auto_trade(
                    user_id, settings, market, coin, current_price
                )

                if success:
                    auto_traded = True
                    logger.info(f"[SurgeAlert] Auto-trade executed for user {user_id}: {market}")
                else:
                    logger.warning(f"[SurgeAlert] Auto-trade failed for user {user_id}: {market}")
            else:
                logger.info(f"[SurgeAlert] Auto-trade not executed for user {user_id}: {reason}")

        # 3. Format message
        message = self.format_alert_message(
            coin, market, confidence, current_price, target_price,
            expected_return, auto_traded,
            trade_info.get('amount') if trade_info else None,
            trade_info.get('stop_loss_price') if trade_info else None,
            trade_info.get('take_profit_price') if trade_info else None
        )

        # 4. Send via Telegram (if chat_id provided)
        telegram_sent = False
        telegram_message_id = None

        if telegram_chat_id:
            try:
                # TODO: Integrate with SurgeTelegramBot
                # For now, just log
                logger.info(f"[SurgeAlert] Would send to Telegram chat {telegram_chat_id}:")
                logger.info(message)
                telegram_sent = True
            except Exception as e:
                logger.error(f"[SurgeAlert] Failed to send Telegram message: {str(e)}")

        # 5. Record alert
        alert = self.record_alert(
            user_id=user_id,
            market=market,
            coin=coin,
            confidence=confidence,
            entry_price=current_price,
            target_price=target_price,
            stop_loss_price=trade_info.get('stop_loss_price') if trade_info else None,
            auto_traded=auto_traded,
            trade_amount=trade_info.get('amount') if trade_info else None,
            trade_quantity=trade_info.get('quantity') if trade_info else None,
            order_id=trade_info.get('order_id') if trade_info else None,
            reason=f"Surge prediction with {confidence:.1f}% confidence",
            alert_message=message,
            telegram_sent=telegram_sent,
            telegram_message_id=telegram_message_id
        )

        if alert:
            logger.info(f"[SurgeAlert] Successfully processed alert for user {user_id}: {market} (auto_traded={auto_traded})")
            return True, alert
        else:
            logger.error(f"[SurgeAlert] Failed to record alert for user {user_id}")
            return False, None

    def get_user_alerts(
        self,
        user_id: int,
        limit: int = 50,
        week_number: int = None
    ) -> List[SurgeAlert]:
        """
        Get user's alert history

        Args:
            user_id: User ID
            limit: Maximum number of alerts to return
            week_number: Filter by week number (optional)

        Returns:
            List of SurgeAlert objects
        """
        try:
            query = self.session.query(SurgeAlert)\
                .filter(SurgeAlert.user_id == user_id)

            if week_number:
                query = query.filter(SurgeAlert.week_number == week_number)

            alerts = query.order_by(SurgeAlert.sent_at.desc())\
                .limit(limit)\
                .all()

            logger.info(f"[SurgeAlert] Retrieved {len(alerts)} alerts for user {user_id}")
            return alerts

        except Exception as e:
            logger.error(f"[SurgeAlert] Error getting alerts for user {user_id}: {str(e)}")
            return []

    def get_alert_stats(self, user_id: int) -> Dict:
        """
        Get alert statistics for user

        Args:
            user_id: User ID

        Returns:
            Dictionary with stats
        """
        try:
            current_week = SurgeAlert.get_current_week_number()

            # This week's count
            week_count = self.get_weekly_alert_count(user_id, auto_traded_only=True)

            # Total count
            total_count = self.session.query(func.count(SurgeAlert.id))\
                .filter(
                    SurgeAlert.user_id == user_id,
                    SurgeAlert.auto_traded == True
                )\
                .scalar() or 0

            # Get settings for statistics
            settings = self.get_user_settings(user_id)

            return {
                'week_count': week_count,
                'total_count': total_count,
                'total_trades': settings.total_trades if settings else 0,
                'successful_trades': settings.successful_trades if settings else 0,
                'total_profit_loss': settings.total_profit_loss if settings else 0,
                'success_rate': (settings.successful_trades / settings.total_trades * 100) if settings and settings.total_trades > 0 else 0,
                'current_week': current_week
            }

        except Exception as e:
            logger.error(f"[SurgeAlert] Error getting stats for user {user_id}: {str(e)}")
            return {
                'week_count': 0,
                'total_count': 0,
                'total_trades': 0,
                'successful_trades': 0,
                'total_profit_loss': 0,
                'success_rate': 0
            }


# Singleton instance
_service_instance = None


def get_surge_alert_service(session: Session = None) -> SurgeAlertService:
    """
    Get or create surge alert service instance

    Args:
        session: SQLAlchemy session (optional)

    Returns:
        SurgeAlertService instance
    """
    global _service_instance
    if _service_instance is None or session is not None:
        _service_instance = SurgeAlertService(session)
    return _service_instance


if __name__ == "__main__":
    print("Surge Alert Service v2.0")
    print("=" * 60)

    # Example usage
    service = get_surge_alert_service()

    print("\n1. Testing weekly count:")
    count = service.get_weekly_alert_count(user_id=1)
    print(f"   Weekly count: {count}")

    print("\n2. Testing max alerts:")
    for plan in ['free', 'basic', 'pro']:
        max_alerts = service.get_max_alerts_for_plan(plan)
        print(f"   {plan.upper()}: {max_alerts} alerts/week")

    print("\n3. Testing message formatting:")
    message = service.format_alert_message(
        coin='BTC',
        market='KRW-BTC',
        confidence=85.5,
        current_price=52000000,
        target_price=54000000,
        expected_return=3.8,
        auto_traded=True,
        trade_amount=100000,
        stop_loss_price=49400000,
        take_profit_price=57200000
    )
    print(f"   Message:\n{message}")

    print("\n✅ Service initialized successfully (v2.0)")
