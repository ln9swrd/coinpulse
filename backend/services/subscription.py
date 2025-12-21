"""
CoinPulse - Subscription Service
구독 관리 및 정기 결제 자동화 서비스
"""

import os
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from backend.models.subscription_models import (
    Subscription, Transaction,
    SubscriptionPlan, BillingPeriod, SubscriptionStatus, PaymentStatus
)
from backend.database.models import User
from backend.services.toss_payment import get_toss_payment_service

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    구독 관리 서비스
    
    주요 기능:
    - 구독 생성/조회/업데이트/취소
    - 정기 결제 자동화
    - 구독 업그레이드/다운그레이드
    """
    
    def __init__(self):
        """Initialize Subscription Service"""
        self.toss_service = get_toss_payment_service()
    
    def create_subscription(
        self,
        db: Session,
        user_id: int,
        user_email: str,
        plan: str,
        billing_period: str = 'monthly'
    ) -> Subscription:
        """
        새 구독 생성
        
        Args:
            db: Database session
            user_id: 사용자 ID
            user_email: 사용자 이메일
            plan: 구독 플랜 (free/premium/enterprise)
            billing_period: 결제 주기 (monthly/annual)
            
        Returns:
            Subscription: 생성된 구독
        """
        # 가격 설정
        prices = {
            'premium': {'monthly': 29000, 'annual': 290000},
            'enterprise': {'monthly': 99000, 'annual': 990000}
        }
        
        amount = 0
        if plan in prices:
            amount = prices[plan][billing_period]
        
        # 구독 생성
        subscription = Subscription(
            user_id=user_id,
            user_email=user_email,
            plan=SubscriptionPlan[plan.upper()],
            billing_period=BillingPeriod[billing_period.upper()],
            status=SubscriptionStatus.PENDING,
            amount=amount,
            currency='KRW'
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        logger.info(f"[Subscription] Created: user={user_id}, plan={plan}, amount={amount}")
        return subscription
    
    def activate_subscription(
        self,
        db: Session,
        subscription_id: int,
        payment_key: str,
        transaction_id: str
    ) -> Subscription:
        """
        구독 활성화 (결제 완료 후)
        
        Args:
            db: Database session
            subscription_id: 구독 ID
            payment_key: 토스 결제 키
            transaction_id: 트랜잭션 ID
            
        Returns:
            Subscription: 활성화된 구독
        """
        subscription = db.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()
        
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        # 구독 기간 설정
        now = datetime.utcnow()
        if subscription.billing_period == BillingPeriod.MONTHLY:
            period_end = now + timedelta(days=30)
        else:  # ANNUAL
            period_end = now + timedelta(days=365)
        
        # 구독 업데이트
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.started_at = now
        subscription.current_period_start = now
        subscription.current_period_end = period_end
        
        # 트랜잭션 생성
        transaction = Transaction(
            subscription_id=subscription.id,
            user_id=subscription.user_id,
            transaction_id=transaction_id,
            amount=subscription.amount,
            currency=subscription.currency,
            payment_method='toss',
            status=PaymentStatus.SUCCEEDED,
            payment_key=payment_key
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(subscription)
        
        logger.info(f"[Subscription] Activated: id={subscription_id}, end={period_end}")
        return subscription
    
    def cancel_subscription(
        self,
        db: Session,
        subscription_id: int,
        reason: str = 'User requested'
    ) -> Subscription:
        """
        구독 취소
        
        Args:
            db: Database session
            subscription_id: 구독 ID
            reason: 취소 사유
            
        Returns:
            Subscription: 취소된 구독
        """
        subscription = db.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()
        
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = datetime.utcnow()
        
        db.commit()
        db.refresh(subscription)
        
        logger.info(f"[Subscription] Cancelled: id={subscription_id}, reason={reason}")
        return subscription
    
    def get_user_subscription(
        self,
        db: Session,
        user_id: int
    ) -> Optional[Subscription]:
        """
        사용자의 활성 구독 조회
        
        Args:
            db: Database session
            user_id: 사용자 ID
            
        Returns:
            Optional[Subscription]: 활성 구독 (없으면 None)
        """
        return db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.ACTIVE
        ).first()
    
    def get_subscription_transactions(
        self,
        db: Session,
        subscription_id: int
    ) -> List[Transaction]:
        """
        구독의 모든 트랜잭션 조회
        
        Args:
            db: Database session
            subscription_id: 구독 ID
            
        Returns:
            List[Transaction]: 트랜잭션 목록
        """
        return db.query(Transaction).filter(
            Transaction.subscription_id == subscription_id
        ).order_by(Transaction.created_at.desc()).all()
    
    def process_renewal_payment(
        self,
        db: Session,
        subscription: Subscription,
        billing_key: str
    ) -> Transaction:
        """
        정기 결제 실행 (자동 갱신)
        
        Args:
            db: Database session
            subscription: 구독 객체
            billing_key: 토스 빌링 키
            
        Returns:
            Transaction: 결제 트랜잭션
        """
        # 사용자 정보 조회
        user = db.query(User).filter(User.id == subscription.user_id).first()
        if not user:
            raise ValueError(f"User not found: {subscription.user_id}")

        # 주문 ID 생성
        order_id = f"SUB-{subscription.id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        order_name = f"{subscription.plan.value.title()} Plan ({subscription.billing_period.value})"

        try:
            # 토스페이먼츠로 자동 결제
            result = self.toss_service.charge_billing(
                billing_key=billing_key,
                customer_key=f"USER-{subscription.user_id}",
                amount=subscription.amount,
                order_id=order_id,
                order_name=order_name,
                customer_email=user.email
            )
            
            # 트랜잭션 생성
            transaction = Transaction(
                subscription_id=subscription.id,
                user_id=subscription.user_id,
                transaction_id=result.get('orderId'),
                amount=subscription.amount,
                currency=subscription.currency,
                payment_method='toss',
                status=PaymentStatus.SUCCEEDED,
                payment_key=result.get('paymentKey')
            )
            
            # 구독 기간 연장
            if subscription.billing_period == BillingPeriod.MONTHLY:
                subscription.current_period_end += timedelta(days=30)
            else:
                subscription.current_period_end += timedelta(days=365)
            
            db.add(transaction)
            db.commit()
            db.refresh(transaction)
            
            logger.info(f"[Subscription] Renewal succeeded: id={subscription.id}")
            return transaction
            
        except Exception as e:
            logger.error(f"[Subscription] Renewal failed: {str(e)}")
            
            # 실패 트랜잭션 기록
            transaction = Transaction(
                subscription_id=subscription.id,
                user_id=subscription.user_id,
                transaction_id=order_id,
                amount=subscription.amount,
                currency=subscription.currency,
                payment_method='toss',
                status=PaymentStatus.FAILED
            )
            
            db.add(transaction)
            db.commit()
            
            raise
    
    def check_expired_subscriptions(self, db: Session) -> List[Subscription]:
        """
        만료된 구독 확인 및 상태 업데이트
        
        Args:
            db: Database session
            
        Returns:
            List[Subscription]: 만료된 구독 목록
        """
        now = datetime.utcnow()
        
        expired = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.current_period_end <= now
        ).all()
        
        for subscription in expired:
            subscription.status = SubscriptionStatus.EXPIRED
            subscription.ended_at = now
        
        if expired:
            db.commit()
            logger.info(f"[Subscription] Expired {len(expired)} subscriptions")
        
        return expired


# Singleton instance
_subscription_service = None

def get_subscription_service() -> SubscriptionService:
    """Get or create SubscriptionService singleton"""
    global _subscription_service
    if _subscription_service is None:
        _subscription_service = SubscriptionService()
    return _subscription_service
