# -*- coding: utf-8 -*-
"""
Signal Distribution Service
중앙 시그널을 사용자에게 분배하고 사용량 추적
"""

from datetime import datetime, timedelta
from sqlalchemy import func
from backend.database.connection import get_db_session
from backend.models.trading_signal import TradingSignal, UserSignalHistory, ExecutionStatus, SignalStatus
from backend.models.plan_limits import PlanLimits
from backend.models.subscription_models import Subscription, SubscriptionStatus
from backend.database.models import User


class SignalDistributor:
    """
    시그널 분배 및 사용량 관리 서비스

    핵심 기능:
    1. 새로운 시그널을 요금제별 제한에 맞춰 분배
    2. 월간 사용량 추적
    3. 보너스 알림 표시
    4. 우선순위 관리 (Enterprise > Pro > Basic > Free)
    5. Telegram 알림 전송 (optional)
    """

    def __init__(self, telegram_bot=None):
        self.session = None
        self.telegram_bot = telegram_bot

    def get_monthly_usage(self, user_id):
        """
        사용자의 이번 달 시그널 수신 횟수 조회

        Args:
            user_id (int): 사용자 ID

        Returns:
            int: 이번 달 받은 시그널 수
        """
        session = get_db_session()
        try:
            # 이번 달 시작일
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)

            # 이번 달 받은 시그널 개수
            count = session.query(UserSignalHistory).filter(
                UserSignalHistory.user_id == user_id,
                UserSignalHistory.received_at >= month_start
            ).count()

            return count

        finally:
            session.close()

    def can_receive_signal(self, user_id, user_plan):
        """
        사용자가 시그널을 받을 수 있는지 확인

        Args:
            user_id (int): 사용자 ID
            user_plan (str): 플랜 ('free', 'basic', 'pro', 'enterprise')

        Returns:
            tuple: (bool: 받을 수 있는지, str: 이유, bool: 보너스 여부)
        """
        current_usage = self.get_monthly_usage(user_id)
        can_receive, message = PlanLimits.check_can_receive_signal(user_plan, current_usage)
        is_bonus = PlanLimits.is_bonus_signal(user_plan, current_usage)

        return can_receive, message, is_bonus

    def get_eligible_users(self, signal_id):
        """
        시그널을 받을 수 있는 사용자 목록 조회

        Args:
            signal_id (int): 시그널 ID

        Returns:
            list: [(user_id, email, plan, is_bonus), ...]
        """
        session = get_db_session()
        try:
            # 활성 구독자 조회 (User와 조인하여 email 가져오기)
            active_subscriptions = session.query(Subscription, User).join(
                User, Subscription.user_id == User.id
            ).filter(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.current_period_end > datetime.utcnow()
            ).all()

            eligible_users = []

            for sub, user in active_subscriptions:
                user_id = sub.user_id
                plan = sub.plan.value

                # 제한 확인
                can_receive, message, is_bonus = self.can_receive_signal(user_id, plan)

                if can_receive:
                    eligible_users.append({
                        'user_id': user_id,
                        'email': user.email,
                        'plan': plan,
                        'is_bonus': is_bonus,
                        'priority': self._get_priority(plan)
                    })

            # 우선순위로 정렬 (Enterprise > Pro > Basic > Free)
            eligible_users.sort(key=lambda x: x['priority'], reverse=True)

            return eligible_users

        finally:
            session.close()

    def _get_priority(self, plan):
        """
        플랜별 우선순위 반환

        Args:
            plan (str): 플랜 이름

        Returns:
            int: 우선순위 (높을수록 우선)
        """
        priority_map = {
            'enterprise': 100,
            'pro': 50,
            'basic': 20,
            'free': 10
        }
        return priority_map.get(plan, 0)

    def distribute_signal(self, signal_id):
        """
        시그널을 적격 사용자에게 분배

        Args:
            signal_id (int): 분배할 시그널 ID

        Returns:
            dict: {
                'distributed_count': int,
                'users': [{'user_id': int, 'email': str, 'is_bonus': bool}],
                'errors': []
            }
        """
        session = get_db_session()

        try:
            # 시그널 조회
            signal = session.query(TradingSignal).filter(
                TradingSignal.id == signal_id
            ).first()

            if not signal:
                return {
                    'distributed_count': 0,
                    'users': [],
                    'errors': [f"Signal {signal_id} not found"]
                }

            # 만료된 시그널 체크
            if signal.is_expired():
                signal.status = SignalStatus.EXPIRED
                session.commit()
                return {
                    'distributed_count': 0,
                    'users': [],
                    'errors': [f"Signal {signal_id} has expired"]
                }

            # 적격 사용자 조회
            eligible_users = self.get_eligible_users(signal_id)

            distributed_users = []
            errors = []

            for user_info in eligible_users:
                try:
                    # UserSignalHistory 생성
                    history = UserSignalHistory(
                        user_id=user_info['user_id'],
                        signal_id=signal_id,
                        received_at=datetime.utcnow(),
                        is_bonus=user_info['is_bonus'],
                        execution_status=ExecutionStatus.NOT_EXECUTED
                    )
                    session.add(history)

                    distributed_users.append({
                        'user_id': user_info['user_id'],
                        'email': user_info['email'],
                        'plan': user_info['plan'],
                        'is_bonus': user_info['is_bonus']
                    })

                except Exception as e:
                    errors.append(f"User {user_info['user_id']}: {str(e)}")

            # 시그널 통계 업데이트
            signal.distributed_to = len(distributed_users)
            signal.status = SignalStatus.ACTIVE

            session.commit()

            print(f"[SignalDistributor] Signal {signal_id} distributed to {len(distributed_users)} users")
            for user in distributed_users[:5]:  # 처음 5명만 로그
                bonus_label = " (BONUS)" if user['is_bonus'] else ""
                print(f"  - {user['email']} ({user['plan']}){bonus_label}")

            if len(distributed_users) > 5:
                print(f"  ... and {len(distributed_users) - 5} more")

            # Send Telegram notifications (if telegram_bot is available)
            if self.telegram_bot and distributed_users:
                self._send_telegram_notifications(signal, distributed_users)

            return {
                'distributed_count': len(distributed_users),
                'users': distributed_users,
                'errors': errors
            }

        except Exception as e:
            session.rollback()
            return {
                'distributed_count': 0,
                'users': [],
                'errors': [f"Distribution error: {str(e)}"]
            }

        finally:
            session.close()

    def mark_signal_executed(self, user_id, signal_id, order_id, execution_price):
        """
        사용자가 시그널을 실행했을 때 기록

        Args:
            user_id (int): 사용자 ID
            signal_id (int): 시그널 ID
            order_id (str): Upbit 주문 ID
            execution_price (int): 실제 체결 가격

        Returns:
            bool: 성공 여부
        """
        session = get_db_session()

        try:
            # UserSignalHistory 업데이트
            history = session.query(UserSignalHistory).filter(
                UserSignalHistory.user_id == user_id,
                UserSignalHistory.signal_id == signal_id
            ).first()

            if not history:
                print(f"[SignalDistributor] History not found for user {user_id}, signal {signal_id}")
                return False

            history.execution_status = ExecutionStatus.EXECUTED
            history.executed_at = datetime.utcnow()
            history.order_id = order_id
            history.execution_price = execution_price

            # TradingSignal executed_count 증가
            signal = session.query(TradingSignal).filter(
                TradingSignal.id == signal_id
            ).first()

            if signal:
                signal.executed_count += 1

            session.commit()

            print(f"[SignalDistributor] Signal {signal_id} executed by user {user_id}")
            print(f"  Order ID: {order_id}")
            print(f"  Execution price: ₩{execution_price:,}")

            return True

        except Exception as e:
            session.rollback()
            print(f"[SignalDistributor] Error marking execution: {e}")
            return False

        finally:
            session.close()

    def get_user_signal_history(self, user_id, limit=50):
        """
        사용자의 시그널 수신 이력 조회

        Args:
            user_id (int): 사용자 ID
            limit (int): 최대 조회 개수

        Returns:
            list: [{'signal': {...}, 'history': {...}}, ...]
        """
        session = get_db_session()

        try:
            histories = session.query(UserSignalHistory).filter(
                UserSignalHistory.user_id == user_id
            ).order_by(UserSignalHistory.received_at.desc()).limit(limit).all()

            result = []

            for history in histories:
                signal = session.query(TradingSignal).filter(
                    TradingSignal.id == history.signal_id
                ).first()

                if signal:
                    result.append({
                        'signal': signal.to_dict(),
                        'history': history.to_dict()
                    })

            return result

        finally:
            session.close()

    def get_usage_stats(self, user_id, plan):
        """
        사용자의 이번 달 사용량 통계

        Args:
            user_id (int): 사용자 ID
            plan (str): 플랜 이름

        Returns:
            dict: PlanLimits.get_usage_stats() 결과
        """
        current_usage = self.get_monthly_usage(user_id)
        return PlanLimits.get_usage_stats(plan, current_usage)

    def _send_telegram_notifications(self, signal, distributed_users):
        """
        Send Telegram notifications to users

        Args:
            signal: TradingSignal object
            distributed_users: List of user dicts with telegram_chat_id
        """
        try:
            import asyncio
            from backend.models.user import User

            print(f"[SignalDistributor] Sending Telegram notifications to {len(distributed_users)} users...")

            session = get_db_session()

            notification_count = 0
            for user_info in distributed_users:
                try:
                    # Get user's telegram_chat_id from database
                    user = session.query(User).filter(User.id == user_info['user_id']).first()

                    if not user or not hasattr(user, 'telegram_chat_id') or not user.telegram_chat_id:
                        continue

                    # Prepare signal data for telegram notification
                    signal_data = {
                        'telegram_chat_id': user.telegram_chat_id,
                        'signal_id': signal.signal_id,
                        'market': signal.market,
                        'confidence': signal.confidence,
                        'entry_price': signal.entry_price,
                        'target_price': signal.target_price,
                        'stop_loss': signal.stop_loss,
                        'reason': signal.reason,
                        'is_bonus': user_info.get('is_bonus', False)
                    }

                    # Send notification (async)
                    asyncio.create_task(self.telegram_bot.send_signal_notification(signal_data))
                    notification_count += 1

                except Exception as e:
                    print(f"[SignalDistributor] Failed to send Telegram notification to user {user_info['user_id']}: {e}")

            session.close()

            if notification_count > 0:
                print(f"[SignalDistributor] Telegram notifications queued for {notification_count} users")

        except Exception as e:
            print(f"[SignalDistributor] Error sending Telegram notifications: {e}")


# 전역 인스턴스
signal_distributor = SignalDistributor()


# Test function
if __name__ == "__main__":
    print("=" * 60)
    print("Signal Distribution Service Test")
    print("=" * 60)

    distributor = SignalDistributor()

    # Test 1: 사용량 조회
    print("\n[Test 1] Monthly usage check:")
    test_user_id = 1
    usage = distributor.get_monthly_usage(test_user_id)
    print(f"  User {test_user_id}: {usage}회 사용")

    # Test 2: 수신 가능 여부
    print("\n[Test 2] Can receive signal:")
    for plan in ['free', 'basic', 'pro', 'enterprise']:
        can_receive, message, is_bonus = distributor.can_receive_signal(test_user_id, plan)
        print(f"  {plan.upper()}: {can_receive} ({message}) - Bonus: {is_bonus}")

    # Test 3: 사용량 통계
    print("\n[Test 3] Usage stats:")
    stats = distributor.get_usage_stats(test_user_id, 'basic')
    print(f"  Plan: {stats['plan']}")
    print(f"  Promised: {stats['promised']}회")
    print(f"  Actual limit: {stats['actual']}회")
    print(f"  Used: {stats['used']}회")
    print(f"  Remaining: {stats['remaining']}회")
    print(f"  Bonus received: {stats['bonus_received']}회")
    print(f"  Usage: {stats['usage_percentage']}%")
