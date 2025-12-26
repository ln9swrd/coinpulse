-- Migration: Add trade_amount column to surge_alerts table
-- Date: 2025-12-26
-- Description: Fix database schema mismatch causing PositionMonitor errors

-- Check current structure (optional, for verification)
-- \d surge_alerts

-- Add missing column (PostgreSQL)
ALTER TABLE surge_alerts
ADD COLUMN IF NOT EXISTS trade_amount BIGINT;

-- Verify column was added
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'surge_alerts' AND column_name = 'trade_amount';

COMMIT;
