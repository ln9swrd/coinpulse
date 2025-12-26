-- Migration: Change price columns from BIGINT to NUMERIC(20,6)
-- Reason: Support decimal prices for low-value coins (e.g., DOGE, SHIB)
-- Date: 2025-12-26

-- Backup table first (optional, for safety)
-- CREATE TABLE surge_alerts_backup AS SELECT * FROM surge_alerts;

-- Change price columns to NUMERIC(20, 6)
ALTER TABLE surge_alerts
    ALTER COLUMN entry_price TYPE NUMERIC(20, 6),
    ALTER COLUMN target_price TYPE NUMERIC(20, 6),
    ALTER COLUMN stop_loss_price TYPE NUMERIC(20, 6),
    ALTER COLUMN exit_price TYPE NUMERIC(20, 6),
    ALTER COLUMN trade_amount TYPE NUMERIC(20, 6),
    ALTER COLUMN profit_loss TYPE NUMERIC(20, 6);

-- Verify changes
SELECT column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name = 'surge_alerts'
  AND column_name IN ('entry_price', 'target_price', 'stop_loss_price', 'exit_price', 'trade_amount', 'profit_loss');

-- Expected output:
-- entry_price      | numeric | 20 | 6
-- target_price     | numeric | 20 | 6
-- stop_loss_price  | numeric | 20 | 6
-- exit_price       | numeric | 20 | 6
-- trade_amount     | numeric | 20 | 6
-- profit_loss      | numeric | 20 | 6
