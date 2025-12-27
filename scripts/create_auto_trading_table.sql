-- Create surge_auto_trading_settings table
CREATE TABLE IF NOT EXISTS surge_auto_trading_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,

    -- Basic settings
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    total_budget BIGINT NOT NULL DEFAULT 1000000,
    amount_per_trade BIGINT NOT NULL DEFAULT 100000,

    -- Risk management
    risk_level VARCHAR(20) NOT NULL DEFAULT 'moderate',
    stop_loss_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    stop_loss_percent FLOAT NOT NULL DEFAULT -5.0,
    take_profit_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    take_profit_percent FLOAT NOT NULL DEFAULT 10.0,

    -- Filtering
    min_confidence FLOAT NOT NULL DEFAULT 80.0,
    max_positions INTEGER NOT NULL DEFAULT 5,
    excluded_coins JSON,
    avoid_high_price_entry BOOLEAN NOT NULL DEFAULT TRUE,

    -- Position strategy
    position_strategy VARCHAR(20) NOT NULL DEFAULT 'single',
    max_amount_per_coin BIGINT,
    allow_duplicate_positions BOOLEAN NOT NULL DEFAULT FALSE,

    -- Notifications
    telegram_enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- Dynamic target settings
    use_dynamic_target BOOLEAN NOT NULL DEFAULT TRUE,
    min_target_percent FLOAT NOT NULL DEFAULT 3.0,
    max_target_percent FLOAT NOT NULL DEFAULT 10.0,
    target_calculation_mode VARCHAR(20) NOT NULL DEFAULT 'dynamic',

    -- Statistics
    total_trades INTEGER NOT NULL DEFAULT 0,
    successful_trades INTEGER NOT NULL DEFAULT 0,
    total_profit_loss BIGINT NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create index on user_id
CREATE INDEX IF NOT EXISTS idx_surge_auto_trading_settings_user ON surge_auto_trading_settings(user_id);

-- Insert default settings for user_id=1 (test user)
INSERT INTO surge_auto_trading_settings (
    user_id, enabled, total_budget, amount_per_trade,
    risk_level, stop_loss_enabled, stop_loss_percent,
    take_profit_enabled, take_profit_percent,
    min_confidence, max_positions, telegram_enabled,
    use_dynamic_target, min_target_percent, max_target_percent
) VALUES (
    1, TRUE, 1000000, 100000,
    'moderate', TRUE, -5.0,
    TRUE, 10.0,
    70.0, 5, TRUE,
    TRUE, 3.0, 10.0
)
ON CONFLICT (user_id) DO NOTHING;
