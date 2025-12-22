#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create plan_configs table directly using SQL
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import init_database
from sqlalchemy import text

def create_plan_configs_table():
    """Create plan_configs table using raw SQL"""

    print("=" * 60)
    print("Creating plan_configs Table")
    print("=" * 60)

    engine = init_database(create_tables=False)

    sql = """
CREATE TABLE IF NOT EXISTS plan_configs (
    id SERIAL PRIMARY KEY,
    plan_code VARCHAR(50) UNIQUE NOT NULL,

    -- Basic info
    plan_name VARCHAR(100) NOT NULL,
    plan_name_ko VARCHAR(100),
    description TEXT,
    display_order INTEGER DEFAULT 0 NOT NULL,

    -- Pricing
    monthly_price INTEGER DEFAULT 0 NOT NULL,
    annual_price INTEGER DEFAULT 0 NOT NULL,
    setup_fee INTEGER DEFAULT 0 NOT NULL,
    annual_discount_rate INTEGER DEFAULT 0 NOT NULL,
    trial_days INTEGER DEFAULT 0 NOT NULL,

    -- Monitoring limits
    max_coins INTEGER DEFAULT 1 NOT NULL,
    max_watchlists INTEGER DEFAULT 1 NOT NULL,

    -- Auto-trading limits
    auto_trading_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    max_auto_strategies INTEGER DEFAULT 0 NOT NULL,
    max_concurrent_trades INTEGER DEFAULT 0 NOT NULL,

    -- Analysis features
    advanced_indicators BOOLEAN DEFAULT FALSE NOT NULL,
    custom_indicators BOOLEAN DEFAULT FALSE NOT NULL,
    backtesting_enabled BOOLEAN DEFAULT FALSE NOT NULL,

    -- Data features
    history_days INTEGER DEFAULT 7 NOT NULL,
    data_export BOOLEAN DEFAULT FALSE NOT NULL,
    api_access BOOLEAN DEFAULT FALSE NOT NULL,

    -- Email Notification Features
    email_notifications_enabled BOOLEAN DEFAULT FALSE NOT NULL,
    daily_email_limit INTEGER DEFAULT 0 NOT NULL,
    signal_notifications BOOLEAN DEFAULT FALSE NOT NULL,
    portfolio_notifications BOOLEAN DEFAULT FALSE NOT NULL,
    trade_notifications BOOLEAN DEFAULT FALSE NOT NULL,
    system_notifications BOOLEAN DEFAULT FALSE NOT NULL,

    -- Support
    support_level VARCHAR(50) DEFAULT 'community' NOT NULL,
    response_time_hours INTEGER DEFAULT 72 NOT NULL,

    -- Other features
    white_labeling BOOLEAN DEFAULT FALSE NOT NULL,
    sla_guarantee BOOLEAN DEFAULT FALSE NOT NULL,
    custom_development BOOLEAN DEFAULT FALSE NOT NULL,

    -- Display settings
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_featured BOOLEAN DEFAULT FALSE NOT NULL,
    is_visible BOOLEAN DEFAULT TRUE NOT NULL,
    badge_text VARCHAR(50),
    cta_text VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
"""

    index_sql = """
CREATE INDEX IF NOT EXISTS idx_plan_configs_plan_code ON plan_configs(plan_code);
"""

    try:
        with engine.connect() as conn:
            # Create table
            print("\n[INFO] Creating plan_configs table...")
            conn.execute(text(sql))
            conn.commit()
            print("[OK] Table created successfully")

            # Create index
            print("[INFO] Creating index...")
            conn.execute(text(index_sql))
            conn.commit()
            print("[OK] Index created successfully")

        print("\n" + "=" * 60)
        print("[SUCCESS] plan_configs table is ready")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n[ERROR] Failed to create table: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    try:
        success = create_plan_configs_table()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Operation interrupted by user")
        sys.exit(1)
