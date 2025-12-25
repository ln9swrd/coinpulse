# -*- coding: utf-8 -*-
"""
Add Signal Monitoring Columns

Adds columns needed for real-time signal monitoring:
- peak_price: Track highest price reached
- last_checked_at: Last monitoring check timestamp
- close_reason: Reason for signal closure
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from backend.database.connection import get_db_session
from datetime import datetime


def add_monitoring_columns():
    """Add monitoring columns to surge_alerts table"""

    print("="*80)
    print("Add Signal Monitoring Columns")
    print("="*80)
    print()

    with get_db_session() as session:
        # Check if columns exist
        check_query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'surge_alerts'
              AND column_name IN ('peak_price', 'last_checked_at', 'close_reason')
        """)

        result = session.execute(check_query)
        existing_columns = {row[0] for row in result.fetchall()}

        print(f"[INFO] Existing columns: {existing_columns}")
        print()

        # Add peak_price column
        if 'peak_price' not in existing_columns:
            print("[INFO] Adding 'peak_price' column...")
            alter_query = text("""
                ALTER TABLE surge_alerts
                ADD COLUMN peak_price BIGINT NULL
            """)
            session.execute(alter_query)
            print("[OK] 'peak_price' column added")
        else:
            print("[SKIP] 'peak_price' column already exists")

        # Add last_checked_at column
        if 'last_checked_at' not in existing_columns:
            print("[INFO] Adding 'last_checked_at' column...")
            alter_query = text("""
                ALTER TABLE surge_alerts
                ADD COLUMN last_checked_at TIMESTAMP NULL
            """)
            session.execute(alter_query)
            print("[OK] 'last_checked_at' column added")
        else:
            print("[SKIP] 'last_checked_at' column already exists")

        # Add close_reason column
        if 'close_reason' not in existing_columns:
            print("[INFO] Adding 'close_reason' column...")
            alter_query = text("""
                ALTER TABLE surge_alerts
                ADD COLUMN close_reason VARCHAR(255) NULL
            """)
            session.execute(alter_query)
            print("[OK] 'close_reason' column added")
        else:
            print("[SKIP] 'close_reason' column already exists")

        # Commit all changes
        session.commit()

        print()
        print("="*80)
        print("Migration Complete")
        print("="*80)

        # Initialize peak_price for existing active signals
        print()
        print("[INFO] Initializing peak_price for active signals...")

        init_query = text("""
            UPDATE surge_alerts
            SET peak_price = GREATEST(entry_price, COALESCE(exit_price, entry_price))
            WHERE peak_price IS NULL
              AND entry_price IS NOT NULL
        """)

        result = session.execute(init_query)
        session.commit()

        print(f"[OK] Initialized peak_price for {result.rowcount} signals")


if __name__ == "__main__":
    print(f"[START] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    add_monitoring_columns()

    print()
    print(f"[DONE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
