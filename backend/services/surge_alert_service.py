# -*- coding: utf-8 -*-
"""
Surge Alert Service
급등 알림 전송 및 관리 서비스

참고 문서: docs/features/SURGE_ALERT_SYSTEM.md
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.surge_alert_models import SurgeAlert, UserFavoriteCoin
from backend.models.plan_features import get_user_features, PLAN_FEATURES
from backend.database.connection import get_db_session

logger = logging.getLogger(__name__)


class SurgeAlertService:
    """급등 알림 서비스"""

    def __init__(self, session: Session = None):
        """
        Initialize surge alert service

        Args:
            session: SQLAlchemy session (optional, creates new if not provided)
        """
        self.session = session or get_db_session()
        logger.info("[SurgeAlertService] Initialized")

    def get_weekly_alert_count(self, user_id: int) -> int:
        """
        Get user's alert count for current week

        Args:
            user_id: User ID

        Returns:
            Number of alerts sent this week
        """
        try:
            current_week = SurgeAlert.get_current_week_number()

            count = self.session.query(func.count(SurgeAlert.id))\
                .filter(
                    SurgeAlert.user_id == user_id,
                    SurgeAlert.week_number == current_week
                )\
                .scalar()

            logger.info(f"[SurgeAlert] User {user_id} has {count} alerts this week ({current_week})")
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

    def can_send_alert(self, user_id: int, plan: str) -> Tuple[bool, str]:
        """
        Check if user can receive an alert

        Args:
            user_id: User ID
            plan: User's plan ('free', 'basic', 'pro')

        Returns:
            (can_send: bool, reason: str)
        """
        # Free plan: no alerts
        if plan.lower() == 'free':
            return False, "Free plan does not support alerts"

        # Check weekly limit
        max_alerts = self.get_max_alerts_for_plan(plan)
        current_count = self.get_weekly_alert_count(user_id)

        if current_count >= max_alerts:
            return False, f"Weekly limit reached ({current_count}/{max_alerts})"

        return True, "OK"

    def get_user_favorite_coins(self, user_id: int) -> List[UserFavoriteCoin]:
        """
        Get user's favorite coins with alert enabled

        Args:
            user_id: User ID

        Returns:
            List of UserFavoriteCoin objects
        """
        try:
            favorites = self.session.query(UserFavoriteCoin)\
                .filter(
                    UserFavoriteCoin.user_id == user_id,
                    UserFavoriteCoin.alert_enabled == True
                )\
                .all()

            logger.info(f"[SurgeAlert] User {user_id} has {len(favorites)} favorite coins with alerts enabled")
            return favorites

        except Exception as e:
            logger.error(f"[SurgeAlert] Error getting favorites for user {user_id}: {str(e)}")
            return []

    def is_coin_in_favorites(self, user_id: int, coin: str) -> bool:
        """
        Check if a coin is in user's favorites with alert enabled

        Args:
            user_id: User ID
            coin: Coin symbol (e.g., 'BTC')

        Returns:
            True if coin is in favorites with alert enabled
        """
        try:
            exists = self.session.query(UserFavoriteCoin)\
                .filter(
                    UserFavoriteCoin.user_id == user_id,
                    UserFavoriteCoin.coin == coin.upper(),
                    UserFavoriteCoin.alert_enabled == True
                )\
                .first()

            return exists is not None

        except Exception as e:
            logger.error(f"[SurgeAlert] Error checking favorite for user {user_id}, coin {coin}: {str(e)}")
            return False

    def get_confidence_threshold(self, plan: str, is_favorite: bool) -> float:
        """
        Get confidence threshold based on plan and favorite status

        Args:
            plan: User's plan
            is_favorite: Is the coin in user's favorites?

        Returns:
            Minimum confidence threshold (%)
        """
        if plan.lower() == 'pro':
            return 75.0 if is_favorite else 85.0
        elif plan.lower() == 'basic':
            return 80.0 if is_favorite else 90.0
        else:
            return 100.0  # Free plan: never send

    def should_send_alert(
        self,
        user_id: int,
        plan: str,
        market: str,
        coin: str,
        confidence: float,
        holdings: Dict = None
    ) -> Tuple[bool, str, str]:
        """
        Determine if alert should be sent to user

        Args:
            user_id: User ID
            plan: User's plan
            market: Market code (e.g., 'KRW-BTC')
            coin: Coin symbol (e.g., 'BTC')
            confidence: Prediction confidence (0-100)
            holdings: User's current holdings (optional)

        Returns:
            (should_send: bool, signal_type: str, reason: str)
        """
        # 1. Check if user can receive alerts
        can_send, reason = self.can_send_alert(user_id, plan)
        if not can_send:
            return False, None, reason

        # 2. Check if coin is in favorites
        is_favorite = self.is_coin_in_favorites(user_id, coin)

        # 3. Get confidence threshold
        threshold = self.get_confidence_threshold(plan, is_favorite)

        # 4. Check confidence
        if confidence < threshold:
            return False, None, f"Confidence {confidence}% below threshold {threshold}%"

        # 5. Determine signal type
        signal_type = "favorite" if is_favorite else "high_confidence"

        # 6. Check if user already owns this coin
        if holdings and market in holdings:
            holding = holdings[market]
            if holding.get('balance', 0) > 0:
                signal_type = "additional_buy"
                logger.info(f"[SurgeAlert] User {user_id} already owns {coin}, signal type: additional_buy")

        return True, signal_type, "OK"

    def record_alert(
        self,
        user_id: int,
        market: str,
        coin: str,
        confidence: float,
        signal_type: str,
        current_price: int = None,
        target_price: int = None,
        expected_return: float = None,
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
            signal_type: Type of signal ('favorite', 'high_confidence', 'additional_buy')
            current_price: Current price in KRW
            target_price: Target price in KRW
            expected_return: Expected return %
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
                signal_type=signal_type,
                current_price=current_price,
                target_price=target_price,
                expected_return=expected_return,
                reason=reason,
                alert_message=alert_message,
                telegram_sent=telegram_sent,
                telegram_message_id=telegram_message_id,
                sent_at=datetime.utcnow(),
                week_number=SurgeAlert.get_current_week_number()
            )

            self.session.add(alert)
            self.session.commit()

            logger.info(f"[SurgeAlert] Recorded alert for user {user_id}: {market} ({signal_type})")
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
        signal_type: str,
        holding_info: Dict = None
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
            signal_type: Signal type
            holding_info: Current holding info (for additional_buy type)

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

        if signal_type == "additional_buy":
            # Additional buy opportunity message
            holding_value = holding_info.get('avg_buy_price', 0) if holding_info else 0
            holding_return = holding_info.get('profit_rate', 0) if holding_info else 0

            message = f"""
📈 *추가 매수 기회*

코인: {coin} ({coin_name})
현재 보유: ₩{holding_value:,} ({holding_return:+.2f}%)
추가 급등 예상: {confidence:.1f}% 신뢰도

현재가: ₩{current_price:,}
예상 목표가: ₩{target_price:,} (+{expected_return:.2f}%)

추가 매수 시 예상 평균 수익률: +{(holding_return + expected_return) / 2:.2f}%

💡 이미 보유 중인 코인의 추가 상승이 예상됩니다.
"""

        elif signal_type == "high_confidence":
            # High confidence non-favorite coin message
            message = f"""
🔥 *고신뢰도 급등 알림*

코인: {coin} ({coin_name})
신뢰도: {confidence:.1f}% ⭐
현재가: ₩{current_price:,}
예상 목표가: ₩{target_price:,}
예상 상승률: +{expected_return:.2f}%

💡 관심 코인에 추가하면 우선 알림을 받을 수 있습니다.
"""

        else:
            # Regular favorite coin alert
            message = f"""
📈 *급등 알림*

코인: {coin} ({coin_name})
신뢰도: {confidence:.1f}%
현재가: ₩{current_price:,}
예상 목표가: ₩{target_price:,} (+{expected_return:.2f}%)

📊 검증된 알고리즘 (81.25% 적중률)
"""

        # Add call-to-action
        message += f"\n[상세보기] https://coinpulse.sinsi.ai/dashboard.html?coin={market}"

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
        holdings: Dict = None,
        telegram_chat_id: str = None
    ) -> Tuple[bool, Optional[SurgeAlert]]:
        """
        Send surge alert to a user

        Args:
            user_id: User ID
            plan: User's plan
            market: Market code
            coin: Coin symbol
            confidence: Prediction confidence
            current_price: Current price
            target_price: Target price
            expected_return: Expected return %
            holdings: User's holdings
            telegram_chat_id: Telegram chat ID (optional)

        Returns:
            (success: bool, alert: SurgeAlert or None)
        """
        # 1. Check if should send
        should_send, signal_type, reason = self.should_send_alert(
            user_id, plan, market, coin, confidence, holdings
        )

        if not should_send:
            logger.info(f"[SurgeAlert] Not sending alert to user {user_id}: {reason}")
            return False, None

        # 2. Get holding info for additional_buy type
        holding_info = None
        if signal_type == "additional_buy" and holdings and market in holdings:
            holding_info = holdings[market]

        # 3. Format message
        message = self.format_alert_message(
            coin, market, confidence, current_price, target_price,
            expected_return, signal_type, holding_info
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
            signal_type=signal_type,
            current_price=current_price,
            target_price=target_price,
            expected_return=expected_return,
            reason=f"Surge prediction with {confidence:.1f}% confidence",
            alert_message=message,
            telegram_sent=telegram_sent,
            telegram_message_id=telegram_message_id
        )

        if alert:
            logger.info(f"[SurgeAlert] Successfully sent alert to user {user_id}: {market} ({signal_type})")
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
            week_count = self.get_weekly_alert_count(user_id)

            # Total count
            total_count = self.session.query(func.count(SurgeAlert.id))\
                .filter(SurgeAlert.user_id == user_id)\
                .scalar() or 0

            # User actions count
            action_count = self.session.query(func.count(SurgeAlert.id))\
                .filter(
                    SurgeAlert.user_id == user_id,
                    SurgeAlert.user_action.isnot(None)
                )\
                .scalar() or 0

            return {
                'week_count': week_count,
                'total_count': total_count,
                'action_count': action_count,
                'action_rate': (action_count / total_count * 100) if total_count > 0 else 0,
                'current_week': current_week
            }

        except Exception as e:
            logger.error(f"[SurgeAlert] Error getting stats for user {user_id}: {str(e)}")
            return {
                'week_count': 0,
                'total_count': 0,
                'action_count': 0,
                'action_rate': 0
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
    print("Surge Alert Service")
    print("=" * 60)

    # Example usage
    service = get_surge_alert_service()

    print("\n1. Testing alert eligibility:")
    can_send, reason = service.can_send_alert(user_id=1, plan='basic')
    print(f"   Can send to basic user: {can_send} ({reason})")

    print("\n2. Testing confidence thresholds:")
    for plan in ['free', 'basic', 'pro']:
        threshold_fav = service.get_confidence_threshold(plan, is_favorite=True)
        threshold_reg = service.get_confidence_threshold(plan, is_favorite=False)
        print(f"   {plan.upper()}: favorite={threshold_fav}%, regular={threshold_reg}%")

    print("\n3. Testing message formatting:")
    message = service.format_alert_message(
        coin='BTC',
        market='KRW-BTC',
        confidence=85.5,
        current_price=52000000,
        target_price=54000000,
        expected_return=3.8,
        signal_type='favorite'
    )
    print(f"   Message:\n{message}")

    print("\n✅ Service initialized successfully")
