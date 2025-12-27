#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Database Migration: Add trade_amount and trade_quantity columns to surge_alerts table
Date: 2025-12-26
Issue: PositionMonitor service fails with missing columns
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_db_session
from sqlalchemy import text
import psycopg2

def migrate():
    """Add missing columns to surge_alerts table"""
    print("[Migration] Starting: Add missing columns to surge_alerts")

    try:
        with get_db_session() as session:
            # Add trade_amount column
            try:
                alter_query1 = text("ALTER TABLE surge_alerts ADD COLUMN trade_amount BIGINT")
                session.execute(alter_query1)
                print("[Migration] SUCCESS: Added 'trade_amount' column")
            except psycopg2.errors.DuplicateColumn:
                print("[Migration] - Column 'trade_amount' already exists")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print("[Migration] - Column 'trade_amount' already exists")
                else:
                    raise

            # Add trade_quantity column
            try:
                alter_query2 = text("ALTER TABLE surge_alerts ADD COLUMN trade_quantity FLOAT")
                session.execute(alter_query2)
                print("[Migration] SUCCESS: Added 'trade_quantity' column")
            except psycopg2.errors.DuplicateColumn:
                print("[Migration] - Column 'trade_quantity' already exists")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print("[Migration] - Column 'trade_quantity' already exists")
                else:
                    raise

            session.commit()
            print("[Migration] SUCCESS: All columns checked/added successfully!")
            return True

    except Exception as e:
        print(f"[Migration] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
