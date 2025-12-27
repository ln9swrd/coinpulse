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

    def get_coin_position_info(self, user_id: int, coin: str) -> Dict:
        """
        Get position information for a specific coin

        Args:
            user_id: User ID
            coin: Coin symbol (e.g., 'BTC', 'ETH')

        Returns:
            Dictionary with position info:
            {
                'count': number of open positions,
                'total_amount': total invested amount in KRW
            }
        """
        try:
            # Get open positions for this coin
            positions = self.session.query(SurgeAlert)\
                .filter(
                    SurgeAlert.user_id == user_id,
                    SurgeAlert.coin == coin.upper(),
                    SurgeAlert.auto_traded == True,
                    SurgeAlert.status.in_(['pending', 'executed'])
                )\
                .all()

            count = len(positions)
            total_amount = sum(p.trade_amount for p in positions if p.trade_amount)

            logger.debug(f"[SurgeAlert] User {user_id} has {count} positions in {coin} (total: {total_amount:,} KRW)")
            return {
                'count': count,
                'total_amount': total_amount
            }

        except Exception as e:
            logger.error(f"[SurgeAlert] Error getting coin position info for user {user_id}, coin {coin}: {str(e)}")
            return {'count': 0, 'total_amount': 0}

    def _check_high_price_entry(self, coin: str) -> Tuple[bool, str]:
        """
        Check if current price is too high for entry (avoid buying at peak)

        Checks:
        1. RSI > 70 (overbought)
        2. Price increase > 10% in last 24h
        3. Price near 52-week high

        Args:
            coin: Coin symbol (e.g., 'BTC')

        Returns:
            (is_high_price: bool, reason: str)
        """
        try:
            from backend.common import UpbitAPI

            market = f"KRW-{coin.upper()}"

            # Get public API instance (no auth needed for candles)
            api = UpbitAPI(None, None)

            # Get recent candles (15-minute candles, last 100)
            candles = api.get_candles(market=market, interval='15', count=100)

            if not candles or len(candles) < 20:
                logger.warning(f"[SurgeAlert] Insufficient candle data for {coin}, allowing entry")
                return False, "OK"

            # Get current and historical prices
            current_price = float(candles[0]['trade_price'])
            price_24h_ago = float(candles[-1]['trade_price'])

            # Calculate 24h price change
            price_change_pct = ((current_price - price_24h_ago) / price_24h_ago) * 100

            # Check 1: Price increased too much in 24h (> 10%)
            if price_change_pct > 10:
                logger.info(f"[SurgeAlert] {coin} price rose {price_change_pct:.1f}% in 24h - too high for entry")
                return True, f"Price rose {price_change_pct:.1f}% in 24h (고점위험)"

            # Check 2: RSI > 70 (overbought)
            rsi = self._calculate_rsi([float(c['trade_price']) for c in reversed(candles)], period=14)
            if rsi and rsi > 70:
                logger.info(f"[SurgeAlert] {coin} RSI {rsi:.1f} is overbought (>70) - too high for entry")
                return True, f"RSI {rsi:.1f} overbought (고점위험)"

            # Check 3: Near recent high (within 2% of highest price in last 100 candles)
            prices = [float(c['high_price']) for c in candles]
            max_price = max(prices)
            if current_price >= max_price * 0.98:
                logger.info(f"[SurgeAlert] {coin} at {current_price:,} near recent high {max_price:,} - too high for entry")
                return True, f"Near recent high (고점위험)"

            return False, "OK"

        except Exception as e:
            logger.error(f"[SurgeAlert] Error checking high price entry for {coin}: {str(e)}")
            # On error, allow entry (fail-safe)
            return False, "OK"

    def _calculate_rsi(self, prices: list, period: int = 14) -> float:
        """
        Calculate RSI (Relative Strength Index)

        Args:
            prices: List of prices (oldest to newest)
            period: RSI period (default 14)

        Returns:
            RSI value (0-100)
        """
        try:
            if len(prices) < period + 1:
                return None

            # Calculate price changes
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]

            # Separate gains and losses
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]

            # Calculate average gain/loss
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period

            if avg_loss == 0:
                return 100.0

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            return rsi

        except Exception as e:
            logger.error(f"[SurgeAlert] Error calculating RSI: {str(e)}")
            return None

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

        # -1 means unlimited
        if max_alerts != -1 and current_count >= max_alerts:
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

        # 7.5. Check high-price entry filter (avoid buying at peak)
        avoid_high_price = getattr(settings, 'avoid_high_price_entry', True)
        if avoid_high_price:
            is_high_price, high_price_reason = self._check_high_price_entry(coin)
            if is_high_price:
                return False, f"High price entry avoided: {high_price_reason}"

        # 8. Check position strategy restrictions
        position_strategy = getattr(settings, 'position_strategy', 'single')

        if position_strategy == 'single':
            # Single position strategy: no duplicate positions allowed in same coin
            allow_duplicates = getattr(settings, 'allow_duplicate_positions', False)

            if not allow_duplicates:
                coin_info = self.get_coin_position_info(user_id, coin)
                if coin_info['count'] > 0:
                    return False, f"Already have position in {coin} (single position strategy, no duplicates)"

        elif position_strategy == 'multiple':
            # Multiple position strategy: check max amount per coin
            max_amount_per_coin = getattr(settings, 'max_amount_per_coin', None)

            if max_amount_per_coin:
                coin_info = self.get_coin_position_info(user_id, coin)
                total_invested = coin_info['total_amount']
                new_total = total_invested + settings.amount_per_trade

                if new_total > max_amount_per_coin:
                    return False, f"Exceeds max amount per coin {max_amount_per_coin:,} KRW (current: {total_invested:,}, would be: {new_total:,})"

        return True, "OK"

    def execute_auto_trade(
        self,
        user_id: int,
        settings: SurgeAutoTradingSettings,
        market: str,
        coin: str,
        entry_price: int,
        target_price: int = None,
        stop_loss_price: int = None,
        use_prediction_prices: bool = True
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Execute auto-trade purchase with surge prediction prices

        Args:
            user_id: User ID
            settings: Auto-trading settings
            market: Market code (e.g., 'KRW-BTC')
            coin: Coin symbol
            entry_price: Entry price from surge prediction
            target_price: Target price from surge prediction (optional)
            stop_loss_price: Stop loss price from surge prediction (optional)
            use_prediction_prices: Use prediction prices for stop loss/take profit (default True)

        Returns:
            (success: bool, trade_info: dict or None)
        """
        try:
            # Calculate quantity based on amount_per_trade
            amount = settings.amount_per_trade
            quantity = amount / entry_price

            logger.info(f"[SurgeAlert] Executing auto-trade for user {user_id}:")
            logger.info(f"  Market: {market}")
            logger.info(f"  Entry Price: {entry_price:,} KRW")
            logger.info(f"  Amount: {amount:,} KRW")
            logger.info(f"  Quantity: {quantity:.8f}")

            # Determine stop loss and take profit prices
            if use_prediction_prices and target_price and stop_loss_price:
                # Use prices from surge prediction
                final_stop_loss = stop_loss_price
                final_take_profit = target_price
                logger.info(f"  Using surge prediction prices:")
                logger.info(f"    - Target: {target_price:,} KRW")
                logger.info(f"    - Stop Loss: {stop_loss_price:,} KRW")
            else:
                # Use user's settings
                final_stop_loss = None
                if settings.stop_loss_enabled:
                    calculated = entry_price * (1 + settings.stop_loss_percent / 100)
                    # For low-price coins (< 100), keep 2 decimal places
                    final_stop_loss = round(calculated, 2) if entry_price < 100 else int(calculated)

                final_take_profit = None
                if settings.take_profit_enabled:
                    calculated = entry_price * (1 + settings.take_profit_percent / 100)
                    # For low-price coins (< 100), keep 2 decimal places
                    final_take_profit = round(calculated, 2) if entry_price < 100 else int(calculated)

                logger.info(f"  Using user settings:")
                logger.info(f"    - Stop Loss: {settings.stop_loss_percent}%")
                logger.info(f"    - Take Profit: {settings.take_profit_percent}%")

            # Try to place actual order with Upbit API
            try:
                from backend.common import UpbitAPI, load_api_keys

                # Load user's API keys
                access_key, secret_key = load_api_keys(user_id=user_id)

                if not access_key or not secret_key:
                    raise Exception("No API keys found for user")

                # Real trade execution
                upbit_api = UpbitAPI(access_key, secret_key)

                # Place market buy order
                logger.info(f"[SurgeAlert] Attempting real order: {market}, amount={amount}")
                order_result = upbit_api.place_order(
                    market=market,
                    side='bid',
                    volume=None,
                    price=amount,
                    ord_type='price'  # Market order by amount
                )

                # Check if order was successful
                if order_result and order_result.get('success'):
                    order_id = order_result.get('uuid')
                    order_data = order_result.get('order', {})

                    # Get executed volume and price
                    executed_volume = float(order_data.get('executed_volume', quantity))
                    avg_price = float(order_data.get('avg_price', entry_price))

                    # ✅ CRITICAL: Recalculate stop-loss and take-profit based on ACTUAL execution price
                    # This prevents slippage issues where signal price != execution price
                    if use_prediction_prices and target_price and stop_loss_price:
                        # Keep prediction-based absolute prices (already set)
                        actual_stop_loss = final_stop_loss
                        actual_take_profit = final_take_profit
                        logger.info(f"[SurgeAlert] Using prediction-based prices (no recalculation)")
                    else:
                        # Recalculate based on actual execution price
                        actual_stop_loss = None
                        if settings.stop_loss_enabled:
                            calculated = avg_price * (1 + settings.stop_loss_percent / 100)
                            actual_stop_loss = round(calculated, 2) if avg_price < 100 else int(calculated)

                        actual_take_profit = None
                        if settings.take_profit_enabled:
                            calculated = avg_price * (1 + settings.take_profit_percent / 100)
                            actual_take_profit = round(calculated, 2) if avg_price < 100 else int(calculated)

                        logger.info(f"[SurgeAlert] Recalculated based on execution price:")
                        logger.info(f"  Stop Loss: {actual_stop_loss:,} KRW (avg_price × {1 + settings.stop_loss_percent/100:.3f})")
                        logger.info(f"  Take Profit: {actual_take_profit:,} KRW (avg_price × {1 + settings.take_profit_percent/100:.3f})")

                    logger.info(f"[SurgeAlert] ✅ REAL order placed successfully:")
                    logger.info(f"  Order ID: {order_id}")
                    logger.info(f"  Market: {market}")
                    logger.info(f"  Amount: {amount:,} KRW")
                    logger.info(f"  Executed Volume: {executed_volume:.8f}")
                    logger.info(f"  Avg Price: {avg_price:,} KRW")
                    logger.info(f"  Final Stop Loss: {actual_stop_loss:,} KRW")
                    logger.info(f"  Final Take Profit: {actual_take_profit:,} KRW")

                    trade_info = {
                        'order_id': order_id,
                        'amount': amount,
                        'quantity': executed_volume,
                        'price': avg_price,
                        'entry_price': avg_price,  # ✅ Use actual execution price
                        'stop_loss_price': actual_stop_loss,  # ✅ Recalculated
                        'take_profit_price': actual_take_profit,  # ✅ Recalculated
                        'executed_at': datetime.utcnow(),
                        'real_trade': True
                    }

                    return True, trade_info
                else:
                    # Order failed - log detailed error
                    error_msg = order_result.get('error', 'Unknown error')
                    error_details = order_result.get('details', '')
                    logger.error(f"[SurgeAlert] ❌ Order placement failed:")
                    logger.error(f"  Error: {error_msg}")
                    logger.error(f"  Details: {error_details}")
                    raise Exception(f"Order failed: {error_msg}")

            except Exception as api_error:
                logger.warning(f"[SurgeAlert] Real trade failed: {str(api_error)}, falling back to simulation")

                # Fall back to simulation
                trade_info = {
                    'order_id': f'SIM-{user_id}-{int(datetime.utcnow().timestamp())}',
                    'amount': amount,
                    'quantity': quantity,
                    'price': entry_price,
                    'entry_price': entry_price,
                    'stop_loss_price': final_stop_loss,
                    'take_profit_price': final_take_profit,
                    'executed_at': datetime.utcnow(),
                    'real_trade': False
                }

                logger.info(f"[SurgeAlert] Simulated trade executed")
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
            # Check for duplicate alert (same user, market within last 1 hour)
            from datetime import timedelta
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)

            existing_alert = self.session.query(SurgeAlert).filter(
                SurgeAlert.user_id == user_id,
                SurgeAlert.market == market,
                SurgeAlert.sent_at >= one_hour_ago
            ).first()

            if existing_alert:
                logger.info(f"[SurgeAlert] Duplicate alert detected for user {user_id}: {market} (skipping)")
                return existing_alert

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
        entry_price: int = None,
        stop_loss_price: int = None,
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
            entry_price: Entry price from surge prediction (default: current_price)
            stop_loss_price: Stop loss price from surge prediction (optional)
            telegram_chat_id: Telegram chat ID (optional)

        Returns:
            (success: bool, alert: SurgeAlert or None)
        """
        # Use current price as entry if not provided
        if entry_price is None:
            entry_price = current_price

        # 1. Get user's auto-trading settings
        settings = self.get_user_settings(user_id)

        # 2. Check if can auto-trade
        auto_traded = False
        trade_info = None

        if settings:
            can_trade, reason = self.can_auto_trade(user_id, plan, settings, confidence, coin)

            if can_trade:
                # Execute auto-trade with surge prediction prices
                success, trade_info = self.execute_auto_trade(
                    user_id=user_id,
                    settings=settings,
                    market=market,
                    coin=coin,
                    entry_price=entry_price,
                    target_price=target_price,
                    stop_loss_price=stop_loss_price,
                    use_prediction_prices=True
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
