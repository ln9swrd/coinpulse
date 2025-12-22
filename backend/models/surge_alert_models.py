# -*- coding: utf-8 -*-
"""
Surge Alert Models
급등 알림 시스템 모델

참고 문서: docs/features/SURGE_ALERT_SYSTEM.md
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index, BigInteger, Text
from datetime import datetime
from backend.database.connection import Base


class SurgeAlert(Base):
    """
    급등 알림 기록

    사용자에게 전송된 급등 알림을 기록하여 주간 한도를 추적
    """
    __tablename__ = 'surge_alerts'
    __table_args__ = {'extend_existing': True}

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # User reference
    user_id = Column(Integer, nullable=False, index=True)

    # Market info
    market = Column(String(20), nullable=False)  # 'KRW-BTC'
    coin = Column(String(10), nullable=False)    # 'BTC'

    # Signal info
    confidence = Column(Float, nullable=False)   # 85.5
    signal_type = Column(String(20), nullable=False)  # 'favorite', 'high_confidence', 'additional_buy'

    # Price info
    current_price = Column(BigInteger, nullable=True)   # Current price at signal time
    target_price = Column(BigInteger, nullable=True)    # Predicted target price
    expected_return = Column(Float, nullable=True)      # Expected return %

    # Alert metadata
    reason = Column(Text, nullable=True)         # Why this alert was sent
    alert_message = Column(Text, nullable=True)  # Telegram message content
    telegram_sent = Column(Boolean, default=False)  # Successfully sent via Telegram
    telegram_message_id = Column(String(100), nullable=True)  # Telegram message ID

    # Timing
    sent_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    week_number = Column(Integer, nullable=False, index=True)  # 202452 (YYYYWW format)

    # User action
    user_action = Column(String(20), nullable=True)  # 'bought', 'ignored', 'added_to_favorites'
    action_timestamp = Column(DateTime, nullable=True)

    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_surge_alerts_user_week', 'user_id', 'week_number'),
        Index('idx_surge_alerts_market', 'market'),
        Index('idx_surge_alerts_sent_at', 'sent_at'),
        {'extend_existing': True}
    )

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'market': self.market,
            'coin': self.coin,
            'confidence': self.confidence,
            'signal_type': self.signal_type,
            'current_price': self.current_price,
            'target_price': self.target_price,
            'expected_return': self.expected_return,
            'reason': self.reason,
            'telegram_sent': self.telegram_sent,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'week_number': self.week_number,
            'user_action': self.user_action,
            'action_timestamp': self.action_timestamp.isoformat() if self.action_timestamp else None
        }

    @staticmethod
    def get_current_week_number():
        """Get current week number in YYYYWW format"""
        now = datetime.utcnow()
        week_num = now.isocalendar()[1]  # ISO week number
        return int(f"{now.year}{week_num:02d}")

    def __repr__(self):
        return f"<SurgeAlert(id={self.id}, user_id={self.user_id}, market={self.market}, confidence={self.confidence}, week={self.week_number})>"


class UserFavoriteCoin(Base):
    """
    사용자 관심 코인 설정

    사용자가 우선적으로 모니터링하고 알림을 받을 코인 (최대 5개)
    """
    __tablename__ = 'user_favorite_coins'
    __table_args__ = {'extend_existing': True}

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # User reference
    user_id = Column(Integer, nullable=False, index=True)

    # Coin info
    coin = Column(String(10), nullable=False)  # 'BTC', 'ETH', 'XRP', etc.
    market = Column(String(20), nullable=False)  # 'KRW-BTC' (computed from coin)

    # Alert settings
    alert_enabled = Column(Boolean, default=True, nullable=False)  # Receive surge alerts
    auto_trading_enabled = Column(Boolean, default=False, nullable=False)  # Auto execute trades (Pro only)

    # Risk settings
    risk_level = Column(String(20), default='moderate', nullable=False)  # 'conservative', 'moderate', 'aggressive'
    stop_loss_enabled = Column(Boolean, default=False, nullable=False)  # Enable stop-loss

    # Additional settings (for future use)
    min_confidence = Column(Float, nullable=True)  # Minimum confidence threshold (default: plan-based)
    max_position_size = Column(BigInteger, nullable=True)  # Maximum position size in KRW

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint: one user can't have duplicate coins
    __table_args__ = (
        Index('idx_user_favorite_coins_user', 'user_id'),
        Index('idx_user_favorite_coins_unique', 'user_id', 'coin', unique=True),
        {'extend_existing': True}
    )

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'coin': self.coin,
            'market': self.market,
            'alert_enabled': self.alert_enabled,
            'auto_trading_enabled': self.auto_trading_enabled,
            'risk_level': self.risk_level,
            'stop_loss_enabled': self.stop_loss_enabled,
            'min_confidence': self.min_confidence,
            'max_position_size': self.max_position_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def coin_to_market(coin):
        """Convert coin symbol to market code"""
        return f"KRW-{coin.upper()}"

    def __repr__(self):
        return f"<UserFavoriteCoin(id={self.id}, user_id={self.user_id}, coin={self.coin}, alert={self.alert_enabled})>"


# 초기화 함수
def init_db(engine):
    """Create database tables"""
    Base.metadata.create_all(engine)
    print("[SurgeAlert] Database tables created: surge_alerts, user_favorite_coins")


if __name__ == "__main__":
    print("Surge Alert Models")
    print("=" * 60)

    # Example usage
    print("\n1. SurgeAlert Example:")
    alert = SurgeAlert(
        user_id=1,
        market="KRW-BTC",
        coin="BTC",
        confidence=85.5,
        signal_type="favorite",
        current_price=52000000,
        target_price=54000000,
        expected_return=3.8,
        week_number=SurgeAlert.get_current_week_number()
    )
    print(f"   Market: {alert.market}")
    print(f"   Confidence: {alert.confidence}%")
    print(f"   Expected Return: {alert.expected_return}%")
    print(f"   Week Number: {alert.week_number}")

    print("\n2. UserFavoriteCoin Example:")
    favorite = UserFavoriteCoin(
        user_id=1,
        coin="BTC",
        market=UserFavoriteCoin.coin_to_market("BTC"),
        alert_enabled=True,
        auto_trading_enabled=False,
        risk_level="moderate",
        stop_loss_enabled=True
    )
    print(f"   Coin: {favorite.coin}")
    print(f"   Market: {favorite.market}")
    print(f"   Alert Enabled: {favorite.alert_enabled}")
    print(f"   Risk Level: {favorite.risk_level}")

    print("\n✅ Models defined successfully")
