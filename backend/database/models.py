"""
Database Models Module

Defines SQLAlchemy ORM models for all database tables.
"""

from sqlalchemy import Column, String, Integer, Numeric, DateTime, Boolean, Text, JSON, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from .connection import Base
import json
from datetime import datetime


class Order(Base):
    """
    Orders table - All trading orders and transactions.

    Primary source of truth for trading history.
    Stores both manual and automated trades.
    """
    __tablename__ = 'orders'

    # Primary Key
    uuid = Column(String(36), primary_key=True, comment='Upbit order UUID')

    # Order Info
    market = Column(String(20), nullable=False, index=True, comment='Market code (KRW-BTC)')
    side = Column(String(10), nullable=False, index=True, comment='bid/ask')
    ord_type = Column(String(20), comment='limit/market/price')
    state = Column(String(20), nullable=False, index=True, comment='done/wait/cancel')

    # Price & Volume
    price = Column(Numeric(20, 8), comment='Order price')
    avg_price = Column(Numeric(20, 8), comment='Actual executed price')
    volume = Column(Numeric(20, 8), comment='Order volume')
    executed_volume = Column(Numeric(20, 8), comment='Executed volume')
    remaining_volume = Column(Numeric(20, 8), comment='Remaining volume')

    # Amounts
    paid_fee = Column(Numeric(20, 8), comment='Trading fee paid')
    locked = Column(Numeric(20, 8), comment='Locked amount')
    executed_funds = Column(Numeric(20, 8), comment='Total executed funds')
    remaining_funds = Column(Numeric(20, 8), comment='Remaining funds')

    # Timestamps
    created_at = Column(DateTime, comment='Order creation time (UTC)')
    executed_at = Column(DateTime, index=True, comment='Order execution time (UTC)')
    kr_time = Column(String(50), comment='Korean time for display')

    # Strategy Info (CoinPulse specific)
    strategy = Column(String(20), comment='manual/auto')
    strategy_name = Column(String(50), index=True, comment='trend_following/momentum/etc')
    signal_source = Column(String(100), comment='rsi/macd/sma/manual')

    # Raw Data & Metadata
    raw_data = Column(JSON, comment='Original JSON from Upbit API')
    trades = Column(JSON, comment='Trade execution details array')

    # Timestamps (DB management)
    synced_at = Column(DateTime, default=datetime.utcnow, comment='When synced to DB')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Last update time')

    # Indexes
    __table_args__ = (
        Index('idx_market_executed_at', 'market', 'executed_at'),
        Index('idx_strategy_state', 'strategy_name', 'state'),
    )

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'uuid': self.uuid,
            'market': self.market,
            'side': self.side,
            'ord_type': self.ord_type,
            'state': self.state,
            'price': float(self.price) if self.price else None,
            'avg_price': float(self.avg_price) if self.avg_price else None,
            'volume': float(self.volume) if self.volume else None,
            'executed_volume': float(self.executed_volume) if self.executed_volume else None,
            'paid_fee': float(self.paid_fee) if self.paid_fee else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'kr_time': self.kr_time,
            'strategy': self.strategy,
            'strategy_name': self.strategy_name,
            'signal_source': self.signal_source
        }


class HoldingsHistory(Base):
    """
    Holdings History table - Portfolio snapshots over time.

    Captures portfolio state at regular intervals for historical analysis.
    """
    __tablename__ = 'holdings_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_time = Column(DateTime, nullable=False, index=True, comment='Snapshot timestamp')

    # KRW Balance
    krw_balance = Column(Numeric(20, 2), comment='Available KRW')
    krw_locked = Column(Numeric(20, 2), comment='Locked KRW (in orders)')
    krw_total = Column(Numeric(20, 2), comment='Total KRW')

    # Portfolio Summary
    total_value = Column(Numeric(20, 2), comment='Total assets (KRW + crypto)')
    crypto_value = Column(Numeric(20, 2), comment='Crypto value only')
    total_profit = Column(Numeric(20, 2), comment='Unrealized profit')
    total_profit_rate = Column(Numeric(10, 4), comment='Profit rate (%)')
    coin_count = Column(Integer, comment='Number of coins held')

    # Holdings Detail (JSON)
    holdings_detail = Column(JSON, comment='Array of coin holdings with details')

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'snapshot_time': self.snapshot_time.isoformat(),
            'krw_total': float(self.krw_total) if self.krw_total else 0,
            'total_value': float(self.total_value) if self.total_value else 0,
            'crypto_value': float(self.crypto_value) if self.crypto_value else 0,
            'total_profit': float(self.total_profit) if self.total_profit else 0,
            'total_profit_rate': float(self.total_profit_rate) if self.total_profit_rate else 0,
            'coin_count': self.coin_count,
            'holdings_detail': self.holdings_detail
        }


class PriceCache(Base):
    """
    Price Cache table - Historical price data cache.

    Reduces API calls by caching OHLCV data.
    """
    __tablename__ = 'price_cache'

    market = Column(String(20), primary_key=True, comment='Market code')
    timeframe = Column(String(10), primary_key=True, comment='1m/5m/1h/1d')
    timestamp = Column(DateTime, primary_key=True, comment='Candle timestamp')

    # OHLCV
    open = Column(Numeric(20, 8), comment='Open price')
    high = Column(Numeric(20, 8), comment='High price')
    low = Column(Numeric(20, 8), comment='Low price')
    close = Column(Numeric(20, 8), comment='Close price')
    volume = Column(Numeric(20, 8), comment='Trading volume')

    # Metadata
    cached_at = Column(DateTime, default=datetime.utcnow, comment='When cached')

    __table_args__ = (
        Index('idx_market_timeframe_timestamp', 'market', 'timeframe', 'timestamp'),
    )

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'market': self.market,
            'timeframe': self.timeframe,
            'timestamp': self.timestamp.isoformat(),
            'open': float(self.open) if self.open else None,
            'high': float(self.high) if self.high else None,
            'low': float(self.low) if self.low else None,
            'close': float(self.close) if self.close else None,
            'volume': float(self.volume) if self.volume else None
        }


class TradingSignal(Base):
    """
    Trading Signals table - Automated trading signals history.

    Records all signals generated by trading strategies.
    """
    __tablename__ = 'trading_signals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_time = Column(DateTime, nullable=False, index=True, comment='Signal generation time')
    market = Column(String(20), nullable=False, index=True, comment='Market code')

    # Signal Info
    signal_type = Column(String(10), nullable=False, comment='buy/sell/hold')
    strategy_name = Column(String(50), index=True, comment='Strategy that generated signal')
    confidence = Column(Numeric(5, 4), comment='Signal confidence 0.0-1.0')

    # Indicator Values (at signal time)
    rsi = Column(Numeric(10, 4), comment='RSI value')
    macd = Column(Numeric(20, 8), comment='MACD value')
    macd_signal = Column(Numeric(20, 8), comment='MACD signal line')
    sma_20 = Column(Numeric(20, 8), comment='20-period SMA')
    sma_50 = Column(Numeric(20, 8), comment='50-period SMA')

    # Action Taken
    action_taken = Column(Boolean, default=False, comment='Whether order was placed')
    order_uuid = Column(String(36), ForeignKey('orders.uuid'), comment='Related order UUID')

    # Raw Data
    raw_indicators = Column(JSON, comment='All indicator values at signal time')

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    order = relationship('Order', backref='trading_signals')

    __table_args__ = (
        Index('idx_signal_time_market', 'signal_time', 'market'),
        Index('idx_strategy_signal_type', 'strategy_name', 'signal_type'),
    )

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'signal_time': self.signal_time.isoformat(),
            'market': self.market,
            'signal_type': self.signal_type,
            'strategy_name': self.strategy_name,
            'confidence': float(self.confidence) if self.confidence else None,
            'rsi': float(self.rsi) if self.rsi else None,
            'action_taken': self.action_taken,
            'order_uuid': self.order_uuid
        }


class StrategyPerformance(Base):
    """
    Strategy Performance table - Strategy performance metrics.

    Tracks performance metrics for each trading strategy.
    """
    __tablename__ = 'strategy_performance'

    id = Column(Integer, primary_key=True, autoincrement=True)
    market = Column(String(20), nullable=False, index=True, comment='Market code')
    strategy_name = Column(String(50), nullable=False, index=True, comment='Strategy name')
    period_start = Column(DateTime, nullable=False, comment='Analysis period start')
    period_end = Column(DateTime, nullable=False, comment='Analysis period end')

    # Performance Metrics
    total_trades = Column(Integer, default=0, comment='Total number of trades')
    winning_trades = Column(Integer, default=0, comment='Number of winning trades')
    losing_trades = Column(Integer, default=0, comment='Number of losing trades')
    win_rate = Column(Numeric(5, 4), comment='Win rate (0.0-1.0)')

    total_profit = Column(Numeric(20, 2), comment='Total profit/loss')
    total_profit_rate = Column(Numeric(10, 4), comment='Total profit rate (%)')
    max_drawdown = Column(Numeric(10, 4), comment='Maximum drawdown (%)')
    sharpe_ratio = Column(Numeric(10, 4), comment='Sharpe ratio')

    # Trade Stats
    avg_profit_per_trade = Column(Numeric(20, 2), comment='Average profit per trade')
    avg_holding_time = Column(Integer, comment='Average holding time (seconds)')

    # Metadata
    calculated_at = Column(DateTime, default=datetime.utcnow, comment='When calculated')

    __table_args__ = (
        Index('idx_market_strategy', 'market', 'strategy_name'),
        Index('idx_period', 'period_start', 'period_end'),
    )

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'market': self.market,
            'strategy_name': self.strategy_name,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'total_trades': self.total_trades,
            'win_rate': float(self.win_rate) if self.win_rate else 0,
            'total_profit': float(self.total_profit) if self.total_profit else 0,
            'total_profit_rate': float(self.total_profit_rate) if self.total_profit_rate else 0,
            'sharpe_ratio': float(self.sharpe_ratio) if self.sharpe_ratio else 0
        }


class SyncStatus(Base):
    """
    Sync Status table - Tracks API synchronization state.

    Monitors sync status for each market to enable incremental sync.
    """
    __tablename__ = 'sync_status'

    market = Column(String(20), primary_key=True, comment='Market code (or "all")')
    last_sync = Column(DateTime, comment='Last successful sync time')
    last_order_uuid = Column(String(36), comment='Last synced order UUID')
    total_orders = Column(Integer, default=0, comment='Total orders synced')
    last_error = Column(Text, comment='Last error message')
    sync_count = Column(Integer, default=0, comment='Number of syncs performed')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'market': self.market,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'last_order_uuid': self.last_order_uuid,
            'total_orders': self.total_orders,
            'sync_count': self.sync_count,
            'last_error': self.last_error
        }


class SystemLog(Base):
    """
    System Logs table - Application logs for debugging.

    Stores system events, errors, and important operations.
    """
    __tablename__ = 'system_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_time = Column(DateTime, default=datetime.utcnow, index=True, comment='Log timestamp')
    level = Column(String(20), nullable=False, index=True, comment='INFO/WARNING/ERROR')
    component = Column(String(100), comment='Component name (e.g., AutoTradingEngine)')
    message = Column(Text, comment='Log message')
    details = Column(JSON, comment='Additional details (JSON)')

    __table_args__ = (
        Index('idx_log_time_level', 'log_time', 'level'),
    )

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'log_time': self.log_time.isoformat(),
            'level': self.level,
            'component': self.component,
            'message': self.message,
            'details': self.details
        }


# ============================================================
# Swing Trading Multi-User System Models
# ============================================================

class User(Base):
    """
    Consolidated Users table - Unified user accounts for all CoinPulse features.

    Merges swing trading and authentication systems.
    Supports 100+ concurrent users with individual profiles and API keys.
    """
    __tablename__ = 'users'

    # Primary Key (standardized to 'id')
    id = Column(Integer, primary_key=True, autoincrement=True, comment='User ID')

    # Core Account Info
    username = Column(String(100), unique=True, nullable=False, index=True, comment='Unique username')
    email = Column(String(255), unique=True, nullable=False, index=True, comment='Email address')
    password_hash = Column(String(255), nullable=False, comment='Bcrypt hashed password')

    # Upbit API Credentials (encrypted in production)
    upbit_access_key = Column(Text, nullable=True, comment='Upbit API access key')
    upbit_secret_key = Column(Text, nullable=True, comment='Upbit API secret key')

    # Account Status
    is_active = Column(Boolean, default=True, index=True, comment='Account active status')
    is_verified = Column(Boolean, default=False, comment='Email verification status (new name)')
    email_verified_at = Column(DateTime, nullable=True, comment='Email verification timestamp')
    is_admin = Column(Boolean, default=False, nullable=False, comment='Admin user flag')

    # Authentication & Session
    last_login_at = Column(DateTime, nullable=True, comment='Last successful login')
    api_key = Column(String(64), unique=True, nullable=True, index=True, comment='API authentication key (legacy)')

    # Additional Profile Info
    full_name = Column(String(255), nullable=True, comment='Full name')
    phone = Column(String(50), nullable=True, comment='Phone number')

    # Telegram Integration
    telegram_chat_id = Column(String(50), nullable=True, unique=True, index=True, comment='Telegram chat ID for notifications')
    telegram_username = Column(String(100), nullable=True, comment='Telegram username')
    telegram_linked_at = Column(DateTime, nullable=True, comment='When Telegram was linked')

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, comment='Account creation time')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Last update time')

    # Relationships - Swing Trading
    config = relationship('UserConfig', back_populates='user', uselist=False, cascade='all, delete-orphan')
    positions = relationship('SwingPosition', back_populates='user', cascade='all, delete-orphan')
    position_history = relationship('SwingPositionHistory', back_populates='user', cascade='all, delete-orphan')
    trading_logs = relationship('SwingTradingLog', back_populates='user', cascade='all, delete-orphan')

    # Relationships - Authentication
    sessions = relationship('Session', back_populates='user', cascade='all, delete-orphan')
    email_verifications = relationship('EmailVerification', back_populates='user', cascade='all, delete-orphan')
    password_resets = relationship('PasswordReset', back_populates='user', cascade='all, delete-orphan')
    user_api_keys = relationship('UserAPIKey', back_populates='user', cascade='all, delete-orphan')
    billing_keys = relationship('BillingKey', back_populates='user', cascade='all, delete-orphan')

    def to_dict(self, include_sensitive=False, include_api_keys=False):
        """
        Convert model instance to dictionary.

        Args:
            include_sensitive: Whether to include sensitive information
            include_api_keys: Whether to include API keys (with secret key masked)

        Returns:
            dict: User data
        """
        data = {
            'id': self.id,
            'user_id': self.id,  # Compatibility field
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'email_verified_at': self.email_verified_at.isoformat() if self.email_verified_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'full_name': self.full_name,
            'phone': self.phone,
            'is_admin': self.is_admin,  # Admin flag
            'telegram_linked': bool(self.telegram_chat_id),  # Telegram link status
            'telegram_username': self.telegram_username,
            'telegram_linked_at': self.telegram_linked_at.isoformat() if self.telegram_linked_at else None
        }

        if include_sensitive:
            data['has_upbit_keys'] = bool(self.upbit_access_key and self.upbit_secret_key)

        # Include API keys if requested (for settings page)
        if include_api_keys:
            data['upbit_access_key'] = self.upbit_access_key if self.upbit_access_key else None
            # Mask secret key for security (show only last 4 characters)
            if self.upbit_secret_key:
                secret_key = self.upbit_secret_key
                data['upbit_secret_key_masked'] = '****' + secret_key[-4:] if len(secret_key) > 4 else '****'
            else:
                data['upbit_secret_key_masked'] = None

        return data

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"


class TelegramLinkCode(Base):
    """
    Telegram Link Codes table - Temporary codes for linking Telegram accounts.
    """
    __tablename__ = 'telegram_link_codes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    code = Column(String(6), unique=True, nullable=False, index=True, comment='6-digit linking code')
    telegram_chat_id = Column(String(50), nullable=True, comment='Telegram chat ID')
    telegram_username = Column(String(100), nullable=True, comment='Telegram username')
    expires_at = Column(DateTime, nullable=False, comment='Code expiration time')
    used = Column(Boolean, default=False, comment='Whether code has been used')
    used_at = Column(DateTime, nullable=True, comment='When code was used')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Code creation time')

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'code': self.code,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used': self.used,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<TelegramLinkCode(id={self.id}, user_id={self.user_id}, code='{self.code}')>"


class UserConfig(Base):
    """
    User Trading Configurations table.

    Stores individual user trading settings.
    """
    __tablename__ = 'user_configs'

    config_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)

    # Budget Settings
    total_budget_krw = Column(Integer, default=40000, comment='Total budget in KRW')
    budget_per_position_krw = Column(Integer, default=10000, comment='Budget per position in KRW')
    min_order_amount = Column(Integer, default=6000, comment='Minimum order amount')
    max_order_amount = Column(Integer, default=40000, comment='Maximum order amount')
    max_concurrent_positions = Column(Integer, default=3, comment='Max concurrent positions')

    # Monitored Coins (JSON array)
    monitored_coins = Column(JSON, default=list, comment='List of monitored coin symbols')

    # Holding Strategy
    holding_period_days = Column(Integer, default=3, comment='Target holding period')
    force_sell_after_period = Column(Boolean, default=False, comment='Force sell after period')

    # Profit Targets
    take_profit_min = Column(Numeric(5, 4), default=0.08, comment='Min take profit (8%)')
    take_profit_max = Column(Numeric(5, 4), default=0.15, comment='Max take profit (15%)')
    stop_loss_min = Column(Numeric(5, 4), default=0.03, comment='Min stop loss (3%)')
    stop_loss_max = Column(Numeric(5, 4), default=0.05, comment='Max stop loss (5%)')

    # Risk Management
    emergency_stop_loss = Column(Numeric(5, 4), default=0.03, comment='Emergency stop loss (3%)')
    auto_stop_on_loss = Column(Boolean, default=True, comment='Auto stop on loss')

    # System Settings
    auto_trading_enabled = Column(Boolean, default=False, comment='Auto trading enabled')
    swing_trading_enabled = Column(Boolean, default=False, comment='Swing trading enabled')
    test_mode = Column(Boolean, default=True, comment='Test mode (no real orders)')

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship('User', back_populates='config')

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'config_id': self.config_id,
            'user_id': self.user_id,
            'total_budget_krw': self.total_budget_krw,
            'min_order_amount': self.min_order_amount,
            'max_order_amount': self.max_order_amount,
            'max_concurrent_positions': self.max_concurrent_positions,
            'holding_period_days': self.holding_period_days,
            'take_profit_min': float(self.take_profit_min) if self.take_profit_min else 0.08,
            'take_profit_max': float(self.take_profit_max) if self.take_profit_max else 0.15,
            'swing_trading_enabled': self.swing_trading_enabled,
            'test_mode': self.test_mode
        }


class SwingPosition(Base):
    """
    Active Swing Positions table.

    Tracks currently open positions for all users.
    """
    __tablename__ = 'swing_positions'

    position_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    coin_symbol = Column(String(20), nullable=False, comment='Market code (KRW-BTC)')

    # Entry Info
    buy_price = Column(Numeric(20, 8), nullable=False, comment='Buy price')
    quantity = Column(Numeric(20, 8), nullable=False, comment='Quantity purchased')
    order_amount = Column(Numeric(20, 2), nullable=False, comment='Total order amount in KRW')
    buy_time = Column(DateTime, default=datetime.utcnow, comment='Purchase time')

    # Status
    status = Column(String(20), default='open', index=True, comment='open/closed')

    # Current State
    current_price = Column(Numeric(20, 8), comment='Current price')
    current_value = Column(Numeric(20, 2), comment='Current position value')
    profit_loss = Column(Numeric(20, 2), default=0, comment='Unrealized P/L')
    profit_loss_percent = Column(Numeric(10, 4), default=0, comment='P/L percentage')

    # Price Tracking
    highest_price = Column(Numeric(20, 8), comment='Highest price since purchase')
    lowest_price = Column(Numeric(20, 8), comment='Lowest price since purchase')

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship('User', back_populates='positions')

    # Indexes
    __table_args__ = (
        Index('idx_user_coin', 'user_id', 'coin_symbol'),
        Index('idx_user_status', 'user_id', 'status'),
    )

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'position_id': self.position_id,
            'user_id': self.user_id,
            'coin_symbol': self.coin_symbol,
            'buy_price': float(self.buy_price) if self.buy_price else 0,
            'quantity': float(self.quantity) if self.quantity else 0,
            'order_amount': float(self.order_amount) if self.order_amount else 0,
            'buy_time': self.buy_time.isoformat() if self.buy_time else None,
            'status': self.status,
            'current_price': float(self.current_price) if self.current_price else 0,
            'profit_loss': float(self.profit_loss) if self.profit_loss else 0,
            'profit_loss_percent': float(self.profit_loss_percent) if self.profit_loss_percent else 0
        }


class SwingPositionHistory(Base):
    """
    Position History table - Closed positions.

    Records all closed positions for performance analysis.
    """
    __tablename__ = 'swing_position_history'

    history_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    position_id = Column(Integer, comment='Original position ID')
    coin_symbol = Column(String(20), nullable=False, index=True)

    # Trade Info
    buy_price = Column(Numeric(20, 8), nullable=False)
    sell_price = Column(Numeric(20, 8), nullable=False)
    quantity = Column(Numeric(20, 8), nullable=False)
    buy_amount = Column(Numeric(20, 2), nullable=False)
    sell_amount = Column(Numeric(20, 2), nullable=False)

    # Performance
    profit_loss = Column(Numeric(20, 2), nullable=False, comment='Realized P/L')
    profit_loss_percent = Column(Numeric(10, 4), nullable=False, comment='P/L percentage')

    # Timing
    buy_time = Column(DateTime, nullable=False)
    sell_time = Column(DateTime, nullable=False, index=True)
    holding_hours = Column(Numeric(10, 2), comment='Holding duration in hours')
    holding_days = Column(Integer, comment='Holding duration in days')

    # Exit Reason
    close_reason = Column(String(50), comment='take_profit/stop_loss/emergency_stop/manual/holding_period')

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship('User', back_populates='position_history')

    # Indexes
    __table_args__ = (
        Index('idx_user_sell_time', 'user_id', 'sell_time'),
        Index('idx_coin_sell_time', 'coin_symbol', 'sell_time'),
    )

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'history_id': self.history_id,
            'user_id': self.user_id,
            'coin_symbol': self.coin_symbol,
            'buy_price': float(self.buy_price) if self.buy_price else 0,
            'sell_price': float(self.sell_price) if self.sell_price else 0,
            'quantity': float(self.quantity) if self.quantity else 0,
            'profit_loss': float(self.profit_loss) if self.profit_loss else 0,
            'profit_loss_percent': float(self.profit_loss_percent) if self.profit_loss_percent else 0,
            'buy_time': self.buy_time.isoformat() if self.buy_time else None,
            'sell_time': self.sell_time.isoformat() if self.sell_time else None,
            'holding_hours': float(self.holding_hours) if self.holding_hours else 0,
            'close_reason': self.close_reason
        }


class SwingTradingLog(Base):
    """
    Trading Logs table - All trading actions.

    Comprehensive log of all trading activities per user.
    """
    __tablename__ = 'swing_trading_logs'

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Action Info
    action = Column(String(50), nullable=False, index=True, comment='buy_signal/sell_signal/buy_executed/sell_executed/error')
    coin_symbol = Column(String(20), index=True)
    price = Column(Numeric(20, 8))
    amount = Column(Numeric(20, 2))

    # Context
    reason = Column(Text, comment='Action reason')
    details = Column(JSON, comment='Additional data (JSON)')

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = relationship('User', back_populates='trading_logs')

    # Indexes
    __table_args__ = (
        Index('idx_user_action_time', 'user_id', 'action', 'created_at'),
    )

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'log_id': self.log_id,
            'user_id': self.user_id,
            'action': self.action,
            'coin_symbol': self.coin_symbol,
            'price': float(self.price) if self.price else None,
            'amount': float(self.amount) if self.amount else None,
            'reason': self.reason,
            'details': self.details,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================================
# Authentication System Models
# ============================================================

class Session(Base):
    """
    Session model for JWT token tracking and blacklisting.

    Tracks active and revoked authentication sessions.
    """
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token_jti = Column(String(255), unique=True, nullable=False, index=True, comment='JWT Token ID')
    token_type = Column(String(20), default='access', comment='access or refresh')
    expires_at = Column(DateTime, nullable=False, index=True, comment='Token expiration time')
    revoked = Column(Boolean, default=False, comment='Token revocation status')
    revoked_at = Column(DateTime, nullable=True, comment='Revocation timestamp')
    ip_address = Column(String(50), nullable=True, comment='Client IP address')
    user_agent = Column(Text, nullable=True, comment='Client user agent')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Session creation time')

    # Relationship
    user = relationship('User', back_populates='sessions')

    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, jti='{self.token_jti[:8]}...')>"


class EmailVerification(Base):
    """
    Email verification token model.

    Manages email verification process for new accounts.
    """
    __tablename__ = 'email_verifications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True, comment='Verification token')
    expires_at = Column(DateTime, nullable=False, comment='Token expiration')
    verified = Column(Boolean, default=False, comment='Verification status')
    verified_at = Column(DateTime, nullable=True, comment='Verification timestamp')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Token creation time')

    # Relationship
    user = relationship('User', back_populates='email_verifications')

    def __repr__(self):
        return f"<EmailVerification(id={self.id}, user_id={self.user_id}, verified={self.verified})>"


class PasswordReset(Base):
    """
    Password reset token model.

    Manages password reset requests and tokens.
    """
    __tablename__ = 'password_resets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True, comment='Reset token')
    expires_at = Column(DateTime, nullable=False, comment='Token expiration')
    used = Column(Boolean, default=False, comment='Token usage status')
    used_at = Column(DateTime, nullable=True, comment='Token usage timestamp')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Token creation time')

    # Relationship
    user = relationship('User', back_populates='password_resets')

    def __repr__(self):
        return f"<PasswordReset(id={self.id}, user_id={self.user_id}, used={self.used})>"


class UserAPIKey(Base):
    """
    User API key model for programmatic access.

    Allows users to create API keys for external integrations.
    """
    __tablename__ = 'user_api_keys'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    key_name = Column(String(100), nullable=False, comment='API key name/description')
    api_key = Column(String(255), unique=True, nullable=False, index=True, comment='API key value')
    is_active = Column(Boolean, default=True, comment='Key active status')
    last_used_at = Column(DateTime, nullable=True, comment='Last usage timestamp')
    expires_at = Column(DateTime, nullable=True, comment='Optional expiration')
    created_at = Column(DateTime, default=datetime.utcnow, comment='Key creation time')

    # Relationship
    user = relationship('User', back_populates='user_api_keys')

    def __repr__(self):
        return f"<UserAPIKey(id={self.id}, user_id={self.user_id}, name='{self.key_name}')>"


class BillingKey(Base):
    """
    Billing Key model for Toss Payments recurring payments.

    Stores billing keys for automatic subscription renewals.
    """
    __tablename__ = 'billing_keys'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    customer_key = Column(String(100), unique=True, nullable=False, index=True, comment='Toss Payments customer key')
    billing_key = Column(String(100), nullable=False, comment='Toss Payments billing key')

    # Card Information (from billing_data)
    card_company = Column(String(50), comment='Card issuer company')
    card_number = Column(String(20), comment='Masked card number')
    card_type = Column(String(20), comment='신용/체크')

    # Billing Data (raw JSON)
    billing_data = Column(JSON, comment='Complete billing data from Toss Payments')

    # Status
    status = Column(String(20), default='active', index=True, comment='active/inactive/expired')

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, comment='Billing key creation time')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Last update time')
    last_used_at = Column(DateTime, nullable=True, comment='Last payment execution')

    # Relationship
    user = relationship('User', back_populates='billing_keys')

    # Indexes
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
    )

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'customer_key': self.customer_key,
            'billing_key': self.billing_key[:8] + '...' if self.billing_key else None,  # Masked
            'card_company': self.card_company,
            'card_number': self.card_number,
            'card_type': self.card_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None
        }

    def __repr__(self):
        return f"<BillingKey(id={self.id}, user_id={self.user_id}, customer_key='{self.customer_key}')>"
