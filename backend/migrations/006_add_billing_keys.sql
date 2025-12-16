-- Migration: Add billing_keys table for Toss Payments
-- Created: 2025-12-16
-- Purpose: Store billing keys for recurring payment subscriptions

CREATE TABLE IF NOT EXISTS billing_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    customer_key VARCHAR(100) NOT NULL UNIQUE,
    billing_key VARCHAR(100) NOT NULL,

    -- Card Information
    card_company VARCHAR(50),
    card_number VARCHAR(20),
    card_type VARCHAR(20),

    -- Billing Data (JSON)
    billing_data JSONB,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_billing_keys_user_id ON billing_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_billing_keys_customer_key ON billing_keys(customer_key);
CREATE INDEX IF NOT EXISTS idx_billing_keys_user_status ON billing_keys(user_id, status);
CREATE INDEX IF NOT EXISTS idx_billing_keys_status ON billing_keys(status);

-- Comments
COMMENT ON TABLE billing_keys IS 'Toss Payments billing keys for recurring subscriptions';
COMMENT ON COLUMN billing_keys.customer_key IS 'Toss Payments customer identifier';
COMMENT ON COLUMN billing_keys.billing_key IS 'Toss Payments billing key for auto-payment';
COMMENT ON COLUMN billing_keys.billing_data IS 'Complete billing response from Toss Payments API';
COMMENT ON COLUMN billing_keys.status IS 'active, inactive, or expired';
