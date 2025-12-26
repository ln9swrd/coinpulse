#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Database Migration: Add trade_amount column to surge_alerts table
Date: 2025-12-26
Issue: PositionMonitor service fails with "surge_alerts.trade_amount 칼럼 없음"
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_db_session
from sqlalchemy import text

def migrate():
    """Add trade_amount column to surge_alerts table"""
    print("[Migration] Starting: Add trade_amount column")

    try:
        with get_db_session() as session:
            # Check if column already exists
            check_query = text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'surge_alerts'
                AND column_name = 'trade_amount'
            """)

            result = session.execute(check_query).fetchone()

            if result:
                print("[Migration] SUCCESS: Column 'trade_amount' already exists. Skipping.")
                return True

            # Add column
            print("[Migration] Adding column 'trade_amount' to surge_alerts...")
            alter_query = text("""
                ALTER TABLE surge_alerts
                ADD COLUMN trade_amount BIGINT
            """)

            session.execute(alter_query)
            session.commit()

            print("[Migration] SUCCESS: Column 'trade_amount' added successfully!")
            return True

    except Exception as e:
        print(f"[Migration] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
