"""
CoinPulse Subscription Models
Database models for subscription and payment management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import enum

# Import unified Base from database connection
from backend.database.connection import Base


class SubscriptionPlan(enum.Enum):
    """Subscription plan types"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class BillingPeriod(enum.Enum):
    """Billing period types"""
    MONTHLY = "monthly"
    ANNUAL = "annual"


class SubscriptionStatus(enum.Enum):
    """Subscription status types"""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"
    TRIAL = "trial"


class PaymentStatus(enum.Enum):
    """Payment/Transaction status types"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentMethod(enum.Enum):
    """Payment method types"""
    CARD = "card"
    KAKAO = "kakao"
    TOSS = "toss"


class Subscription(Base):
    """
    Subscription model
    Represents a user's subscription to a plan
    """
    __tablename__ = 'user_subscriptions'
    __table_args__ = {'extend_existing': True}

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # User reference (foreign key to users table)
    user_id = Column(Integer, nullable=False, index=True)

    # Subscription details (using String to match database VARCHAR type)
    plan = Column(String(50), nullable=False, default='free')
    billing_period = Column(String(50), nullable=False, default='monthly')
    status = Column(String(50), nullable=False, default='pending')

    # Pricing
    amount = Column(Integer, nullable=False, default=0)  # Amount in KRW
    currency = Column(String(3), nullable=False, default='KRW')

    # Payment
    payment_method = Column(String(50), nullable=True)  # e.g., 'card', 'bank_transfer'
    auto_renew = Column(Boolean, default=False, nullable=False)  # Auto-renewal enabled

    # Dates
    expires_at = Column(DateTime, nullable=True)  # Subscription expiration date
    started_at = Column(DateTime, nullable=True)  # When subscription became active
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    trial_ends_at = Column(DateTime, nullable=True)  # For trial periods
    cancelled_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan={self.plan}, status={self.status})>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan': self.plan,  # Already string, no .value needed
            'billing_period': self.billing_period,  # Already string
            'status': self.status,  # Already string
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'auto_renew': self.auto_renew,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'trial_ends_at': self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def is_active(self):
        """Check if subscription is currently active"""
        if self.status != 'active':  # Use string comparison
            return False
        if self.current_period_end and datetime.utcnow() > self.current_period_end:
            return False
        return True

    def days_until_renewal(self):
        """Calculate days until next renewal"""
        if not self.current_period_end:
            return None
        delta = self.current_period_end - datetime.utcnow()
        return max(0, delta.days)


class Transaction(Base):
    """
    Transaction model
    Represents a payment transaction
    """
    __tablename__ = 'transactions'
    __table_args__ = {'extend_existing': True}

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    subscription_id = Column(Integer, ForeignKey('user_subscriptions.id', ondelete='CASCADE'), nullable=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    # Transaction details
    transaction_id = Column(String(100), unique=True, nullable=False, index=True)  # External transaction ID
    amount = Column(Integer, nullable=False)  # Amount in KRW
    currency = Column(String(3), nullable=False, default='KRW')

    # Payment details
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)

    # Billing info
    billing_email = Column(String(255), nullable=True)
    billing_name = Column(String(255), nullable=True)
    billing_country = Column(String(2), nullable=True)

    # Gateway response (store as JSON text)
    gateway_response = Column(Text, nullable=True)  # JSON string
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)

    # Refund info
    refunded = Column(Boolean, nullable=False, default=False)
    refund_amount = Column(Integer, nullable=True)
    refunded_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)

    # Relationships

    def __repr__(self):
        return f"<Transaction(id={self.id}, transaction_id={self.transaction_id}, status={self.status.value}, amount={self.amount})>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'subscription_id': self.subscription_id,
            'user_id': self.user_id,
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method.value,
            'status': self.status.value,
            'billing_email': self.billing_email,
            'billing_name': self.billing_name,
            'billing_country': self.billing_country,
            'error_message': self.error_message,
            'error_code': self.error_code,
            'refunded': self.refunded,
            'refund_amount': self.refund_amount,
            'refunded_at': self.refunded_at.isoformat() if self.refunded_at else None,
            'created_at': self.created_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }


# Plan pricing configuration
PLAN_PRICING = {
    SubscriptionPlan.FREE: {
        BillingPeriod.MONTHLY: 0,
        BillingPeriod.ANNUAL: 0
    },
    SubscriptionPlan.BASIC: {
        BillingPeriod.MONTHLY: 49000,
        BillingPeriod.ANNUAL: 470400  # 20% discount (₩39,200/month)
    },
    SubscriptionPlan.PRO: {
        BillingPeriod.MONTHLY: 99000,
        BillingPeriod.ANNUAL: 950400  # 20% discount (₩79,200/month)
    },
    SubscriptionPlan.ENTERPRISE: {
        BillingPeriod.MONTHLY: None,  # Custom pricing (hidden from public)
        BillingPeriod.ANNUAL: None
    }
}


def get_plan_price(plan: SubscriptionPlan, billing_period: BillingPeriod) -> int:
    """
    Get the price for a plan and billing period

    Args:
        plan: The subscription plan
        billing_period: The billing period

    Returns:
        Price in KRW (integer)
    """
    return PLAN_PRICING.get(plan, {}).get(billing_period, 0)


def calculate_next_billing_date(billing_period: BillingPeriod, start_date: datetime = None) -> datetime:
    """
    Calculate the next billing date based on billing period

    Args:
        billing_period: The billing period
        start_date: The start date (default: now)

    Returns:
        Next billing date
    """
    if start_date is None:
        start_date = datetime.utcnow()

    if billing_period == BillingPeriod.MONTHLY:
        # Add 30 days
        return start_date + timedelta(days=30)
    elif billing_period == BillingPeriod.ANNUAL:
        # Add 365 days
        return start_date + timedelta(days=365)
    else:
        raise ValueError(f"Unknown billing period: {billing_period}")


def generate_transaction_id() -> str:
    """
    Generate a unique transaction ID

    Returns:
        Transaction ID string
    """
    import secrets
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    random_suffix = secrets.token_hex(8)
    return f"TXN_{timestamp}_{random_suffix}"
