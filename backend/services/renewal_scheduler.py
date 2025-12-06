"""
CoinPulse - Subscription Renewal Scheduler
정기 결제 자동화 스케줄러

자동으로 만료 예정 구독을 확인하고 갱신 결제를 실행합니다.
"""

import os
import time
import schedule
import logging
from datetime import datetime, timedelta
from typing import List

from backend.database.connection import get_db_session
from backend.models.subscription_models import Subscription, SubscriptionStatus
from backend.services.subscription import get_subscription_service

logger = logging.getLogger(__name__)

# Services
subscription_service = get_subscription_service()


class SubscriptionRenewalScheduler:
    """
    정기 결제 자동화 스케줄러
    
    기능:
    - 매일 만료 예정 구독 확인
    - 자동 갱신 결제 실행
    - 실패 시 재시도
    """
    
    def __init__(self):
        """Initialize scheduler"""
        self.running = False
        logger.info("[Scheduler] Initialized")
    
    def check_and_renew_subscriptions(self):
        """
        만료 예정 구독을 확인하고 갱신 결제 실행
        """
        logger.info("[Scheduler] Checking subscriptions for renewal...")
        
        try:
            db = next(get_db_session())
            
            # 3일 이내 만료 예정 구독 조회
            renewal_date = datetime.utcnow() + timedelta(days=3)
            
            subscriptions = db.query(Subscription).filter(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.current_period_end <= renewal_date,
                Subscription.current_period_end > datetime.utcnow()
            ).all()
            
            logger.info(f"[Scheduler] Found {len(subscriptions)} subscriptions to renew")
            
            # 각 구독에 대해 갱신 시도
            for subscription in subscriptions:
                try:
                    self._process_renewal(db, subscription)
                except Exception as e:
                    logger.error(
                        f"[Scheduler] Renewal failed for subscription {subscription.id}: {str(e)}"
                    )
            
            db.close()
            logger.info("[Scheduler] Subscription renewal check completed")
            
        except Exception as e:
            logger.error(f"[Scheduler] Error in renewal check: {str(e)}")
    
    def _process_renewal(self, db, subscription: Subscription):
        """
        개별 구독 갱신 처리
        
        Args:
            db: Database session
            subscription: 구독 객체
        """
        # 빌링키 조회 (실제로는 DB에서 가져와야 함)
        # 여기서는 예시로 하드코딩
        billing_key = f"BILLING-{subscription.user_id}"
        
        try:
            # 갱신 결제 실행
            transaction = subscription_service.process_renewal_payment(
                db=db,
                subscription=subscription,
                billing_key=billing_key
            )
            
            logger.info(
                f"[Scheduler] Renewal succeeded: "
                f"subscription={subscription.id}, "
                f"transaction={transaction.id}"
            )
            
        except Exception as e:
            logger.error(
                f"[Scheduler] Renewal payment failed: "
                f"subscription={subscription.id}, "
                f"error={str(e)}"
            )
            raise
    
    def check_expired_subscriptions(self):
        """만료된 구독 확인 및 상태 업데이트"""
        logger.info("[Scheduler] Checking for expired subscriptions...")
        
        try:
            db = next(get_db_session())
            
            expired = subscription_service.check_expired_subscriptions(db)
            
            if expired:
                logger.info(f"[Scheduler] Marked {len(expired)} subscriptions as expired")
            
            db.close()
            
        except Exception as e:
            logger.error(f"[Scheduler] Error checking expired subscriptions: {str(e)}")
    
    def start(self):
        """스케줄러 시작"""
        if self.running:
            logger.warning("[Scheduler] Already running")
            return
        
        self.running = True
        logger.info("[Scheduler] Starting...")
        
        # 스케줄 설정
        # 매일 오전 9시에 갱신 확인
        schedule.every().day.at("09:00").do(self.check_and_renew_subscriptions)
        
        # 매일 자정에 만료 확인
        schedule.every().day.at("00:00").do(self.check_expired_subscriptions)
        
        # 테스트용: 1분마다 실행 (프로덕션에서는 제거)
        if os.getenv('FLASK_ENV') == 'development':
            schedule.every(1).minutes.do(self.check_expired_subscriptions)
            logger.info("[Scheduler] Running in development mode (1-minute intervals)")
        
        logger.info("[Scheduler] Scheduled tasks:")
        logger.info("  - Renewal check: Daily at 09:00")
        logger.info("  - Expiration check: Daily at 00:00")
        
        # 스케줄 실행 루프
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 체크
        except KeyboardInterrupt:
            logger.info("[Scheduler] Stopped by user")
        except Exception as e:
            logger.error(f"[Scheduler] Unexpected error: {str(e)}")
        finally:
            self.running = False
            logger.info("[Scheduler] Stopped")
    
    def stop(self):
        """스케줄러 중지"""
        logger.info("[Scheduler] Stopping...")
        self.running = False


# Singleton instance
_scheduler = None

def get_renewal_scheduler() -> SubscriptionRenewalScheduler:
    """Get or create SubscriptionRenewalScheduler singleton"""
    global _scheduler
    if _scheduler is None:
        _scheduler = SubscriptionRenewalScheduler()
    return _scheduler


def start_renewal_scheduler_background():
    """백그라운드에서 스케줄러 시작"""
    import threading
    
    scheduler = get_renewal_scheduler()
    
    def run():
        scheduler.start()
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    
    logger.info("[Scheduler] Started in background thread")


if __name__ == '__main__':
    # 스탠드얼론 실행
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    scheduler = get_renewal_scheduler()
    scheduler.start()
