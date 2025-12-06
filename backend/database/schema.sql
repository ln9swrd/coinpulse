-- Swing Trading Multi-User Database Schema
-- Supports 100+ concurrent users

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    api_key TEXT UNIQUE NOT NULL,  -- For API authentication
    upbit_access_key TEXT,
    upbit_secret_key TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- User Trading Configurations
CREATE TABLE IF NOT EXISTS user_configs (
    config_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    total_budget_krw INTEGER DEFAULT 40000,
    min_order_amount INTEGER DEFAULT 6000,
    max_order_amount INTEGER DEFAULT 40000,
    max_concurrent_positions INTEGER DEFAULT 3,
    holding_period_days INTEGER DEFAULT 3,
    force_sell_after_period BOOLEAN DEFAULT 0,
    take_profit_min REAL DEFAULT 0.08,
    take_profit_max REAL DEFAULT 0.15,
    stop_loss_min REAL DEFAULT 0.03,
    stop_loss_max REAL DEFAULT 0.05,
    emergency_stop_loss REAL DEFAULT 0.03,
    auto_stop_on_loss BOOLEAN DEFAULT 1,
    swing_trading_enabled BOOLEAN DEFAULT 0,
    test_mode BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Active Positions
CREATE TABLE IF NOT EXISTS positions (
    position_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    coin_symbol TEXT NOT NULL,
    buy_price REAL NOT NULL,
    quantity REAL NOT NULL,
    order_amount REAL NOT NULL,
    buy_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'open',  -- open, closed
    current_price REAL,
    current_value REAL,
    profit_loss REAL DEFAULT 0,
    profit_loss_percent REAL DEFAULT 0,
    highest_price REAL,
    lowest_price REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE(user_id, coin_symbol)  -- One position per coin per user
);

-- Position History
CREATE TABLE IF NOT EXISTS position_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    position_id INTEGER,
    coin_symbol TEXT NOT NULL,
    buy_price REAL NOT NULL,
    sell_price REAL NOT NULL,
    quantity REAL NOT NULL,
    buy_amount REAL NOT NULL,
    sell_amount REAL NOT NULL,
    profit_loss REAL NOT NULL,
    profit_loss_percent REAL NOT NULL,
    buy_time TIMESTAMP NOT NULL,
    sell_time TIMESTAMP NOT NULL,
    holding_hours REAL,
    holding_days INTEGER,
    close_reason TEXT,  -- take_profit, stop_loss, emergency_stop, manual, holding_period
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Trading Logs
CREATE TABLE IF NOT EXISTS trading_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL,  -- buy_signal, sell_signal, buy_executed, sell_executed, error
    coin_symbol TEXT,
    price REAL,
    amount REAL,
    reason TEXT,
    details TEXT,  -- JSON string for additional data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_positions_user ON positions(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_history_user ON position_history(user_id);
CREATE INDEX IF NOT EXISTS idx_history_time ON position_history(sell_time);
CREATE INDEX IF NOT EXISTS idx_logs_user ON trading_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_time ON trading_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_users_api_key ON users(api_key);
