"""
CoinPulse Subscription Service
Handles subscription and payment business logic
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional, Dict, Any
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.subscription_models import (
    Subscription, Transaction, SubscriptionPlan, BillingPeriod,
    SubscriptionStatus, PaymentStatus, PaymentMethod,
    get_plan_price, calculate_next_billing_date, generate_transaction_id
)


class SubscriptionService:
    """
    Service for managing subscriptions and payments
    """

    def __init__(self, database_url: str = None):
        """
        Initialize the subscription service

        Args:
            database_url: Database connection string (optional)
        """
        # Get database URL
        if database_url is None:
            database_url = os.getenv('DATABASE_URL')

        if not database_url:
            database_url = 'sqlite:///data/coinpulse.db'

        # Convert postgres:// to postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)

        # Create engine
        if database_url.startswith('sqlite'):
            self.engine = create_engine(database_url, echo=False)
        else:
            self.engine = create_engine(
                database_url,
                pool_size=10,
                max_overflow=20,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=False
            )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False
        )

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    def create_subscription(
        self,
        user_id: int,
        user_email: str,
        plan: str,
        billing_period: str,
        payment_method: str,
        billing_info: Dict[str, Any],
        card_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new subscription

        Args:
            user_id: User ID
            user_email: User email
            plan: Plan name ('free', 'premium', 'enterprise')
            billing_period: Billing period ('monthly', 'annual')
            payment_method: Payment method ('card', 'kakao', 'toss')
            billing_info: Billing information dict
            card_info: Card information dict (optional)

        Returns:
            Dict with subscription and transaction info
        """
        session = self.get_session()
        try:
            # Convert strings to enums
            plan_enum = SubscriptionPlan(plan)
            billing_period_enum = BillingPeriod(billing_period)
            payment_method_enum = PaymentMethod(payment_method)

            # Get plan price
            amount = get_plan_price(plan_enum, billing_period_enum)

            # Check if free plan
            if plan_enum == SubscriptionPlan.FREE:
                # Create free subscription without payment
                subscription = Subscription(
                    user_id=user_id,
                    user_email=user_email,
                    plan=plan_enum,
                    billing_period=billing_period_enum,
                    status=SubscriptionStatus.ACTIVE,
                    amount=0,
                    currency='KRW',
                    started_at=datetime.utcnow(),
                    current_period_start=datetime.utcnow(),
                    current_period_end=None  # Free plan never expires
                )
                session.add(subscription)
                session.commit()
                session.refresh(subscription)

                return {
                    'success': True,
                    'subscription': subscription.to_dict(),
                    'transaction': None
                }

            # For paid plans, create pending subscription
            subscription = Subscription(
                user_id=user_id,
                user_email=user_email,
                plan=plan_enum,
                billing_period=billing_period_enum,
                status=SubscriptionStatus.PENDING,
                amount=amount,
                currency='KRW'
            )
            session.add(subscription)
            session.flush()  # Get subscription ID

            # Create transaction
            transaction_id = generate_transaction_id()
            transaction = Transaction(
                subscription_id=subscription.id,
                user_id=user_id,
                transaction_id=transaction_id,
                amount=amount,
                currency='KRW',
                payment_method=payment_method_enum,
                status=PaymentStatus.PENDING,
                billing_email=billing_info.get('email'),
                billing_name=f"{billing_info.get('first_name', '')} {billing_info.get('last_name', '')}".strip(),
                billing_country=billing_info.get('country')
            )
            session.add(transaction)
            session.commit()
            session.refresh(subscription)
            session.refresh(transaction)

            return {
                'success': True,
                'subscription': subscription.to_dict(),
                'transaction': transaction.to_dict(),
                'requires_payment': True
            }

        except Exception as e:
            session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            session.close()

    def process_payment(
        self,
        transaction_id: str,
        success: bool = True,
        gateway_response: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a payment (mock implementation)

        Args:
            transaction_id: Transaction ID
            success: Whether payment succeeded
            gateway_response: Gateway response dict (optional)
            error_code: Error code if failed (optional)
            error_message: Error message if failed (optional)

        Returns:
            Dict with result
        """
        session = self.get_session()
        try:
            # Find transaction
            transaction = session.query(Transaction).filter(
                Transaction.transaction_id == transaction_id
            ).first()

            if not transaction:
                return {
                    'success': False,
                    'error': 'Transaction not found'
                }

            # Update transaction status
            if success:
                transaction.status = PaymentStatus.SUCCEEDED
                transaction.processed_at = datetime.utcnow()

                if gateway_response:
                    transaction.gateway_response = json.dumps(gateway_response)

                # Activate subscription
                if transaction.subscription_id:
                    subscription = session.query(Subscription).filter(
                        Subscription.id == transaction.subscription_id
                    ).first()

                    if subscription:
                        now = datetime.utcnow()
                        subscription.status = SubscriptionStatus.ACTIVE
                        subscription.started_at = now
                        subscription.current_period_start = now
                        subscription.current_period_end = calculate_next_billing_date(
                            subscription.billing_period,
                            now
                        )

                session.commit()
                session.refresh(transaction)

                result = {
                    'success': True,
                    'transaction': transaction.to_dict(),
                    'message': 'Payment processed successfully'
                }

                if transaction.subscription_id:
                    session.refresh(subscription)
                    result['subscription'] = subscription.to_dict()

                return result

            else:
                # Payment failed
                transaction.status = PaymentStatus.FAILED
                transaction.error_code = error_code
                transaction.error_message = error_message
                transaction.processed_at = datetime.utcnow()

                if gateway_response:
                    transaction.gateway_response = json.dumps(gateway_response)

                session.commit()
                session.refresh(transaction)

                return {
                    'success': False,
                    'transaction': transaction.to_dict(),
                    'error': error_message or 'Payment failed'
                }

        except Exception as e:
            session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            session.close()

    def get_user_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user's active subscription

        Args:
            user_id: User ID

        Returns:
            Subscription dict or None
        """
        session = self.get_session()
        try:
            subscription = session.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.status == 'active'  # Use string instead of enum
            ).order_by(Subscription.created_at.desc()).first()

            if subscription:
                return subscription.to_dict()
            return None

        finally:
            session.close()

    def cancel_subscription(self, subscription_id: int, user_id: int) -> Dict[str, Any]:
        """
        Cancel a subscription

        Args:
            subscription_id: Subscription ID
            user_id: User ID (for verification)

        Returns:
            Dict with result
        """
        session = self.get_session()
        try:
            subscription = session.query(Subscription).filter(
                Subscription.id == subscription_id,
                Subscription.user_id == user_id
            ).first()

            if not subscription:
                return {
                    'success': False,
                    'error': 'Subscription not found'
                }

            if subscription.status != SubscriptionStatus.ACTIVE:
                return {
                    'success': False,
                    'error': 'Subscription is not active'
                }

            # Cancel subscription (will remain active until period end)
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = datetime.utcnow()

            session.commit()
            session.refresh(subscription)

            return {
                'success': True,
                'subscription': subscription.to_dict(),
                'message': 'Subscription cancelled. Will remain active until current period ends.'
            }

        except Exception as e:
            session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            session.close()

    def get_user_transactions(self, user_id: int, limit: int = 10) -> list:
        """
        Get user's transaction history

        Args:
            user_id: User ID
            limit: Number of transactions to return

        Returns:
            List of transaction dicts
        """
        session = self.get_session()
        try:
            transactions = session.query(Transaction).filter(
                Transaction.user_id == user_id
            ).order_by(Transaction.created_at.desc()).limit(limit).all()

            return [t.to_dict() for t in transactions]

        finally:
            session.close()

    def get_subscription_by_id(self, subscription_id: int) -> Optional[Dict[str, Any]]:
        """
        Get subscription by ID

        Args:
            subscription_id: Subscription ID

        Returns:
            Subscription dict or None
        """
        session = self.get_session()
        try:
            subscription = session.query(Subscription).filter(
                Subscription.id == subscription_id
            ).first()

            if subscription:
                return subscription.to_dict()
            return None

        finally:
            session.close()

    def mock_payment_process(
        self,
        transaction_id: str,
        success_rate: float = 0.9
    ) -> Dict[str, Any]:
        """
        Mock payment processing for testing

        Args:
            transaction_id: Transaction ID
            success_rate: Probability of success (0.0-1.0)

        Returns:
            Dict with result
        """
        import random

        # Simulate payment processing delay
        import time
        time.sleep(0.5)

        # Randomly determine success
        success = random.random() < success_rate

        if success:
            return self.process_payment(
                transaction_id=transaction_id,
                success=True,
                gateway_response={
                    'gateway': 'mock',
                    'payment_id': f'MOCK_{transaction_id}',
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        else:
            return self.process_payment(
                transaction_id=transaction_id,
                success=False,
                error_code='MOCK_PAYMENT_DECLINED',
                error_message='Mock payment declined for testing'
            )
