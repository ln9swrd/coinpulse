-- Create upbit_api_keys table for encrypted API key storage
-- This table stores user-specific Upbit API credentials in encrypted format

CREATE TABLE IF NOT EXISTS upbit_api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    access_key_encrypted TEXT NOT NULL,
    secret_key_encrypted TEXT NOT NULL,
    key_name VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    last_used_at TIMESTAMP,
    last_error_at TIMESTAMP,
    error_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_upbit_api_keys_user_id ON upbit_api_keys(user_id);

-- Create index on is_active for filtering active keys
CREATE INDEX IF NOT EXISTS idx_upbit_api_keys_active ON upbit_api_keys(is_active);

-- Display table structure
\d upbit_api_keys
