# -*- coding: utf-8 -*-
"""
Surge Alert System Models
급등 알림 자동매매 및 투자조언 알림 모델

참고 문서: docs/features/SURGE_ALERT_SYSTEM.md v2.0
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index, BigInteger, Text, JSON, Numeric
from datetime import datetime
from backend.database.connection import Base


class UserAdvisoryCoin(Base):
    """
    투자조언 알림 코인 (Investment Advisory)

    사용자가 선택한 코인에 대한 투자 조언 알림
    - 알림만 제공 (자동 실행 없음)
    - 요금제별 개수 제한 (Free: 0, Basic: 3, Pro: 5)
    """
    __tablename__ = 'user_advisory_coins'
    __table_args__ = {'extend_existing': True}

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # User reference
    user_id = Column(Integer, nullable=False, index=True)

    # Coin info
    coin = Column(String(10), nullable=False)  # 'BTC', 'ETH', etc.
    market = Column(String(20), nullable=False)  # 'KRW-BTC'

    # Settings
    alert_enabled = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Unique constraint
    __table_args__ = (
        Index('idx_user_advisory_coins_user', 'user_id'),
        Index('idx_user_advisory_coins_unique', 'user_id', 'coin', unique=True),
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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def coin_to_market(coin):
        """Convert coin symbol to market code"""
        return f"KRW-{coin.upper()}"

    def __repr__(self):
        return f"<UserAdvisoryCoin(id={self.id}, user_id={self.user_id}, coin={self.coin})>"


class SurgeAutoTradingSettings(Base):
    """
    급등 알림 자동매매 설정

    시스템이 급등 감지 시 자동 매수 설정
    - 예산 및 1회 금액 설정
    - 위험 관리 (손절/익절)
    - 필터링 옵션
    """
    __tablename__ = 'surge_auto_trading_settings'
    __table_args__ = {'extend_existing': True}

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # User reference (unique - one setting per user)
    user_id = Column(Integer, nullable=False, unique=True, index=True)

    # Basic settings
    enabled = Column(Boolean, default=False, nullable=False)
    total_budget = Column(BigInteger, nullable=False, default=1000000)  # 총 예산 (원)
    amount_per_trade = Column(BigInteger, nullable=False, default=100000)  # 1회 투자금액 (원)

    # Risk management (Preset-based)
    risk_level = Column(String(20), default='balanced', nullable=False)  # Preset: conservative/balanced/aggressive
    stop_loss_enabled = Column(Boolean, default=True, nullable=False)
    stop_loss_percent = Column(Float, default=-5.0, nullable=False)  # -5% (updated by preset)
    take_profit_enabled = Column(Boolean, default=True, nullable=False)
    take_profit_percent = Column(Float, default=10.0, nullable=False)  # +10% (updated by preset)

    # Filtering
    min_confidence = Column(Float, default=65.0, nullable=False)  # Minimum confidence threshold (updated by preset)
    max_positions = Column(Integer, default=5, nullable=False)  # Maximum concurrent positions
    excluded_coins = Column(JSON, nullable=True)  # ['DOGE', 'SHIB'] - coins to exclude
    avoid_high_price_entry = Column(Boolean, default=True, nullable=False)  # 고점 진입 방지 (avoid buying at peak prices)

    # Position strategy (NEW - User selectable)
    position_strategy = Column(String(20), default='single', nullable=False)  # 'single' or 'multiple'
    max_amount_per_coin = Column(BigInteger, nullable=True)  # Max amount per coin (for 'multiple' strategy)
    allow_duplicate_positions = Column(Boolean, default=False, nullable=False)  # Allow multiple positions per coin

    # Notifications
    telegram_enabled = Column(Boolean, default=True, nullable=False)

    # Dynamic Target Price Settings (NEW - Adjusted for 3-day holding)
    use_dynamic_target = Column(Boolean, default=True, nullable=False)  # 동적 목표가 사용
    min_target_percent = Column(Float, default=3.0, nullable=False)  # 최소 목표 수익률 (%)
    max_target_percent = Column(Float, default=10.0, nullable=False)  # 최대 목표 수익률 (%)
    target_calculation_mode = Column(String(20), default='dynamic', nullable=False)  # fixed/dynamic/hybrid

    # Statistics
    total_trades = Column(Integer, default=0, nullable=False)
    successful_trades = Column(Integer, default=0, nullable=False)
    total_profit_loss = Column(BigInteger, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'enabled': self.enabled,
            'total_budget': self.total_budget,
            'amount_per_trade': self.amount_per_trade,
            'risk_level': self.risk_level,
            'stop_loss_enabled': self.stop_loss_enabled,
            'stop_loss_percent': self.stop_loss_percent,
            'take_profit_enabled': self.take_profit_enabled,
            'take_profit_percent': self.take_profit_percent,
            'min_confidence': self.min_confidence,
            'max_positions': self.max_positions,
            'excluded_coins': self.excluded_coins or [],
            'avoid_high_price_entry': self.avoid_high_price_entry,
            'position_strategy': self.position_strategy,
            'max_amount_per_coin': self.max_amount_per_coin,
            'allow_duplicate_positions': self.allow_duplicate_positions,
            'telegram_enabled': self.telegram_enabled,
            'use_dynamic_target': self.use_dynamic_target,
            'min_target_percent': self.min_target_percent,
            'max_target_percent': self.max_target_percent,
            'target_calculation_mode': self.target_calculation_mode,
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'total_profit_loss': self.total_profit_loss,
            'success_rate': (self.successful_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def get_remaining_budget(self):
        """Calculate remaining budget"""
        # TODO: Calculate based on current positions
        return self.total_budget

    def can_trade(self):
        """Check if trading is possible"""
        return (
            self.enabled and
            self.get_remaining_budget() >= self.amount_per_trade
        )

    def __repr__(self):
        return f"<SurgeAutoTradingSettings(id={self.id}, user_id={self.user_id}, enabled={self.enabled})>"


class SurgeAlert(Base):
    """
    급등 알림 기록

    급등 감지 및 자동매매 실행 기록
    - 주간 한도 추적
    - 자동매매 실행 여부
    - 손익 추적
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
    signal_type = Column(String(20), nullable=False, default='surge')  # 'surge' or 'advisory'
    confidence = Column(Float, nullable=False)   # 85.5
    expected_return = Column(Float, nullable=True)  # Expected return percentage

    # Price info (Numeric(20, 6) for up to 6 decimal places)
    current_price = Column(Numeric(20, 6), nullable=True)   # Current price (for monitoring)
    peak_price = Column(Numeric(20, 6), nullable=True)      # Peak price reached
    entry_price = Column(Numeric(20, 6), nullable=True)      # Entry price at signal time
    target_price = Column(Numeric(20, 6), nullable=True)     # Predicted target price
    stop_loss_price = Column(Numeric(20, 6), nullable=True)  # Stop loss price
    exit_price = Column(Numeric(20, 6), nullable=True)       # Exit price when signal closed

    # Auto trading info
    auto_traded = Column(Boolean, default=False, nullable=False)  # Was auto-traded?
    trade_amount = Column(Numeric(20, 6), nullable=True)      # Trade amount in KRW (supports decimal)
    trade_quantity = Column(Float, nullable=True)         # Quantity purchased
    order_id = Column(String(50), nullable=True)          # Upbit order ID

    # Result info
    status = Column(String(20), nullable=True)            # pending/executed/stopped/completed
    profit_loss = Column(Numeric(20, 6), nullable=True)       # Profit/loss in KRW (supports decimal)
    profit_loss_percent = Column(Float, nullable=True)    # Profit/loss %
    close_reason = Column(String(100), nullable=True)     # Reason for closing position

    # Alert metadata
    reason = Column(Text, nullable=True)                  # Why this alert was sent
    alert_message = Column(Text, nullable=True)           # Telegram message content
    telegram_sent = Column(Boolean, default=False)        # Successfully sent via Telegram
    telegram_message_id = Column(String(100), nullable=True)  # Telegram message ID

    # Timing
    sent_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)         # When trade was executed
    closed_at = Column(DateTime, nullable=True)           # When position was closed
    last_checked_at = Column(DateTime, nullable=True)     # Last time position was checked
    week_number = Column(Integer, nullable=False, index=True)  # 202452 (YYYYWW format)

    # User action
    user_action = Column(String(20), nullable=True)       # bought/ignored/closed
    action_timestamp = Column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_surge_alerts_user_week', 'user_id', 'week_number'),
        Index('idx_surge_alerts_market', 'market'),
        Index('idx_surge_alerts_sent_at', 'sent_at'),
        Index('idx_surge_alerts_auto_traded', 'auto_traded'),
        {'extend_existing': True}
    )

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'market': self.market,
            'coin': self.coin,
            'signal_type': self.signal_type,
            'confidence': self.confidence,
            'expected_return': self.expected_return,
            'current_price': self.current_price,
            'peak_price': self.peak_price,
            'entry_price': self.entry_price,
            'target_price': self.target_price,
            'stop_loss_price': self.stop_loss_price,
            'exit_price': self.exit_price,
            'auto_traded': self.auto_traded,
            'trade_amount': self.trade_amount,
            'trade_quantity': self.trade_quantity,
            'order_id': self.order_id,
            'status': self.status,
            'profit_loss': self.profit_loss,
            'profit_loss_percent': self.profit_loss_percent,
            'close_reason': self.close_reason,
            'reason': self.reason,
            'telegram_sent': self.telegram_sent,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'last_checked_at': self.last_checked_at.isoformat() if self.last_checked_at else None,
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
        return f"<SurgeAlert(id={self.id}, user_id={self.user_id}, market={self.market}, auto_traded={self.auto_traded})>"


# 초기화 함수
def init_db(engine):
    """Create database tables"""
    Base.metadata.create_all(engine)
    print("[SurgeAlert] Database tables created: user_advisory_coins, surge_auto_trading_settings, surge_alerts")


if __name__ == "__main__":
    print("Surge Alert System Models v2.0")
    print("=" * 60)

    print("\n1. UserAdvisoryCoin (투자조언 알림)")
    advisory = UserAdvisoryCoin(
        user_id=1,
        coin="BTC",
        market="KRW-BTC",
        alert_enabled=True
    )
    print(f"   User: {advisory.user_id}")
    print(f"   Coin: {advisory.coin}")
    print(f"   Market: {advisory.market}")

    print("\n2. SurgeAutoTradingSettings (급등 자동매매)")
    settings = SurgeAutoTradingSettings(
        user_id=1,
        enabled=True,
        total_budget=1000000,
        amount_per_trade=100000,
        risk_level='moderate',
        stop_loss_percent=-5.0,
        take_profit_percent=10.0
    )
    print(f"   Enabled: {settings.enabled}")
    print(f"   Budget: {settings.total_budget:,}원")
    print(f"   Per Trade: {settings.amount_per_trade:,}원")
    print(f"   Can Trade: {settings.can_trade()}")

    print("\n3. SurgeAlert (급등 알림 기록)")
    alert = SurgeAlert(
        user_id=1,
        market="KRW-DOGE",
        coin="DOGE",
        confidence=85.5,
        entry_price=180,
        auto_traded=True,
        trade_amount=100000,
        trade_quantity=555.5,
        week_number=SurgeAlert.get_current_week_number()
    )
    print(f"   Market: {alert.market}")
    print(f"   Confidence: {alert.confidence}%")
    print(f"   Auto Traded: {alert.auto_traded}")
    print(f"   Amount: {alert.trade_amount:,}원")
    print(f"   Week: {alert.week_number}")

    print("\n✅ Models defined successfully (v2.0)")
