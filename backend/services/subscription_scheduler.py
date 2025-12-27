"""
Subscription Scheduler Service

Automatic subscription renewal scheduler.
Runs daily to check expiring subscriptions and process payments.
"""

import schedule
import time
import threading
from datetime import datetime, timedelta
from backend.database.connection import get_db_session
from backend.database.models import User, BillingKey
from backend.models.subscription_models import Subscription
from backend.routes.payments import get_auth_header
import requests
import os

# Toss Payments configuration
TOSS_API_URL = 'https://api.tosspayments.com/v1/billing'


class SubscriptionScheduler:
    """
    Manages automatic subscription renewals.

    Features:
    - Daily check at 00:00 KST
    - Process payments 3 days before expiration
    - Retry failed payments (up to 3 times)
    - Update subscription status
    - Send notifications (email/SMS)
    """

    def __init__(self):
        self.running = False
        self.thread = None
        print("[SubscriptionScheduler] Initialized")

    def check_expiring_subscriptions(self):
        """
        Check for subscriptions expiring in 3 days and process renewals.
        """
        print(f"[SubscriptionScheduler] Running daily check at {datetime.now()}")
        session = get_db_session()

        try:
            # Calculate date 3 days from now
            renewal_date = datetime.utcnow() + timedelta(days=3)
            renewal_date_str = renewal_date.strftime('%Y-%m-%d')

            # Find subscriptions expiring within 3 days
            expiring_subs = session.query(Subscription).filter(
                Subscription.status == 'active',
                Subscription.current_period_end <= renewal_date,
                Subscription.current_period_end >= datetime.utcnow()
            ).all()

            print(f"[SubscriptionScheduler] Found {len(expiring_subs)} expiring subscriptions")

            for subscription in expiring_subs:
                self.process_renewal(subscription, session)

        except Exception as e:
            print(f"[SubscriptionScheduler] Error checking subscriptions: {e}")
        finally:
            session.close()

    def process_renewal(self, subscription, session):
        """
        Process renewal payment for a subscription.

        Args:
            subscription: Subscription object
            session: Database session
        """
        user_id = subscription.user_id
        plan_id = subscription.plan_id

        print(f"[SubscriptionScheduler] Processing renewal for user {user_id}, plan {plan_id}")

        try:
            # Get user's active billing key
            billing_key_obj = session.query(BillingKey).filter_by(
                user_id=user_id,
                status='active'
            ).order_by(BillingKey.created_at.desc()).first()

            if not billing_key_obj:
                print(f"[SubscriptionScheduler] No billing key found for user {user_id}")
                self.send_notification(
                    user_id,
                    'billing_key_missing',
                    f"구독 갱신을 위한 결제 수단이 등록되어 있지 않습니다."
                )
                return

            # Get plan details
            from backend.models.subscription_models import Plan
            plan = session.query(Plan).filter_by(id=plan_id).first()

            if not plan:
                print(f"[SubscriptionScheduler] Plan {plan_id} not found")
                return

            # Calculate amount based on plan
            amount = plan.price

            # Execute payment with retry logic
            success = self.execute_payment_with_retry(
                billing_key_obj.billing_key,
                billing_key_obj.customer_key,
                amount,
                user_id,
                plan.name,
                max_retries=3
            )

            if success:
                # Update subscription (extend end_date)
                if plan.duration_months:
                    new_end_date = subscription.end_date + timedelta(days=30 * plan.duration_months)
                else:
                    new_end_date = subscription.end_date + timedelta(days=365)

                subscription.end_date = new_end_date
                subscription.updated_at = datetime.utcnow()
                session.commit()

                print(f"[SubscriptionScheduler] Renewal successful for user {user_id}")
                self.send_notification(
                    user_id,
                    'renewal_success',
                    f"{plan.name} 구독이 {new_end_date.strftime('%Y-%m-%d')}까지 연장되었습니다."
                )

                # Update last_used_at for billing key
                billing_key_obj.last_used_at = datetime.utcnow()
                session.commit()

            else:
                print(f"[SubscriptionScheduler] Renewal failed for user {user_id}")
                self.send_notification(
                    user_id,
                    'renewal_failed',
                    f"{plan.name} 구독 갱신에 실패했습니다. 결제 수단을 확인해주세요."
                )

        except Exception as e:
            session.rollback()
            print(f"[SubscriptionScheduler] Error processing renewal for user {user_id}: {e}")

    def execute_payment_with_retry(self, billing_key, customer_key, amount, user_id, plan_name, max_retries=3):
        """
        Execute payment with retry logic.

        Args:
            billing_key: Toss Payments billing key
            customer_key: Customer identifier
            amount: Payment amount
            user_id: User ID
            plan_name: Plan name for order description
            max_retries: Maximum number of retry attempts

        Returns:
            bool: True if payment successful, False otherwise
        """
        order_id = f"RENEWAL_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        for attempt in range(1, max_retries + 1):
            print(f"[SubscriptionScheduler] Payment attempt {attempt}/{max_retries} for user {user_id}")

            try:
                response = requests.post(
                    f'{TOSS_API_URL}/{billing_key}',
                    headers=get_auth_header(),
                    json={
                        'customerKey': customer_key,
                        'amount': amount,
                        'orderId': f"{order_id}_RETRY{attempt}",
                        'orderName': f'CoinPulse {plan_name} 구독 갱신'
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    payment_data = response.json()
                    print(f"[SubscriptionScheduler] Payment successful: {payment_data.get('paymentKey')}")
                    return True
                else:
                    error = response.json()
                    print(f"[SubscriptionScheduler] Payment failed (attempt {attempt}): {error.get('message')}")

                    # Wait before retry (exponential backoff)
                    if attempt < max_retries:
                        wait_time = 2 ** attempt  # 2, 4, 8 seconds
                        print(f"[SubscriptionScheduler] Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)

            except Exception as e:
                print(f"[SubscriptionScheduler] Payment error (attempt {attempt}): {e}")

                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)

        return False

    def send_notification(self, user_id, notification_type, message):
        """
        Send notification to user (email/SMS).

        Args:
            user_id: User ID
            notification_type: Type of notification
            message: Notification message

        TODO: Implement email/SMS sending
        """
        print(f"[SubscriptionScheduler] Notification ({notification_type}) for user {user_id}: {message}")

        # TODO: Implement actual notification sending
        # - Email: using SendGrid, AWS SES, or similar
        # - SMS: using Twilio, AWS SNS, or similar
        # - In-app notification: save to database

    def run_scheduler(self):
        """
        Run the scheduler in background thread.
        """
        print("[SubscriptionScheduler] Starting scheduler...")

        # Schedule daily check at 00:00 KST (UTC+9)
        # Note: schedule library uses local time
        schedule.every().day.at("00:00").do(self.check_expiring_subscriptions)

        # Also run immediately on startup (for testing)
        # self.check_expiring_subscriptions()

        self.running = True

        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def start(self):
        """
        Start the scheduler in a background thread.
        """
        if self.thread and self.thread.is_alive():
            print("[SubscriptionScheduler] Already running")
            return

        self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.thread.start()
        print("[SubscriptionScheduler] Started in background thread")

    def stop(self):
        """
        Stop the scheduler.
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[SubscriptionScheduler] Stopped")


# Global scheduler instance
_scheduler_instance = None


def get_scheduler():
    """
    Get global scheduler instance (singleton).
    """
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = SubscriptionScheduler()
    return _scheduler_instance


def start_scheduler():
    """
    Start the global scheduler.
    """
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler


def stop_scheduler():
    """
    Stop the global scheduler.
    """
    scheduler = get_scheduler()
    scheduler.stop()
