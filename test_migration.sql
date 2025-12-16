INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Generating static SQL
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
[Alembic] Successfully imported CoinPulse models
[Alembic] Found 16 tables:
  - email_verifications
  - holdings_history
  - orders
  - password_resets
  - price_cache
  - sessions
  - strategy_performance
  - swing_position_history
  - swing_positions
  - swing_trading_logs
  - sync_status
  - system_logs
  - trading_signals
  - user_api_keys
  - user_configs
  - users
[Alembic] Using default SQLite: sqlite:///data/coinpulse.db
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

INFO  [alembic.runtime.migration] Running upgrade  -> b68429ce9c72, Current schema snapshot
-- Running upgrade  -> b68429ce9c72

INSERT INTO alembic_version (version_num) VALUES ('b68429ce9c72') RETURNING version_num;

INFO  [alembic.runtime.migration] Running upgrade b68429ce9c72 -> e7aa0867203d, Consolidate User model and add authentication tables
-- Running upgrade b68429ce9c72 -> e7aa0867203d

CREATE TABLE email_verifications (
    id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    token VARCHAR(255) NOT NULL, 
    expires_at DATETIME NOT NULL, 
    verified BOOLEAN, 
    verified_at DATETIME, 
    created_at DATETIME, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_email_verifications_token ON email_verifications (token);

CREATE INDEX ix_email_verifications_user_id ON email_verifications (user_id);

CREATE TABLE password_resets (
    id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    token VARCHAR(255) NOT NULL, 
    expires_at DATETIME NOT NULL, 
    used BOOLEAN, 
    used_at DATETIME, 
    created_at DATETIME, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_password_resets_token ON password_resets (token);

CREATE INDEX ix_password_resets_user_id ON password_resets (user_id);

CREATE TABLE sessions (
    id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    token_jti VARCHAR(255) NOT NULL, 
    token_type VARCHAR(20), 
    expires_at DATETIME NOT NULL, 
    revoked BOOLEAN, 
    revoked_at DATETIME, 
    ip_address VARCHAR(50), 
    user_agent TEXT, 
    created_at DATETIME, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_sessions_expires_at ON sessions (expires_at);

CREATE UNIQUE INDEX ix_sessions_token_jti ON sessions (token_jti);

CREATE INDEX ix_sessions_user_id ON sessions (user_id);

CREATE TABLE user_api_keys (
    id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    key_name VARCHAR(100) NOT NULL, 
    api_key VARCHAR(255) NOT NULL, 
    is_active BOOLEAN, 
    last_used_at DATETIME, 
    expires_at DATETIME, 
    created_at DATETIME, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_user_api_keys_api_key ON user_api_keys (api_key);

CREATE INDEX ix_user_api_keys_user_id ON user_api_keys (user_id);

ERROR [alembic.util.messaging] This operation cannot proceed in --sql mode; batch mode with dialect sqlite requires a live database connection with which to reflect the table "swing_position_history". To generate a batch SQL migration script using table "move and copy", a complete Table object should be passed to the "copy_from" argument of the batch_alter_table() method so that table reflection can be skipped.
FAILED: This operation cannot proceed in --sql mode; batch mode with dialect sqlite requires a live database connection with which to reflect the table "swing_position_history". To generate a batch SQL migration script using table "move and copy", a complete Table object should be passed to the "copy_from" argument of the batch_alter_table() method so that table reflection can be skipped.
