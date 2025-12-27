# -*- coding: utf-8 -*-
"""
Clear Surge Alert History

Deletes all records from:
- surge_alerts table
- surge_candidates_cache table

This prepares the database for backfilling historical signals.
"""

import os
import sys
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from backend.database.connection import get_db_session


def clear_surge_data():
    """Clear all surge alert and cache data"""

    print("=" * 80)
    print("Clear Surge Alert History")
    print("=" * 80)
    print()

    with get_db_session() as session:
        # Count existing records
        count_alerts = session.execute(
            text("SELECT COUNT(*) FROM surge_alerts")
        ).scalar()

        print(f"[INFO] Existing records:")
        print(f"  - surge_alerts: {count_alerts}")
        print()

        # Confirm deletion
        if count_alerts > 0:
            print("[WARNING] This will DELETE ALL surge alert data!")
            print()

            # Delete surge_alerts
            print(f"[INFO] Deleting {count_alerts} records from surge_alerts...")
            session.execute(text("DELETE FROM surge_alerts"))
            print("[OK] surge_alerts cleared")

            # Commit changes
            session.commit()

            print()
            print("=" * 80)
            print("Data Cleared Successfully")
            print("=" * 80)
        else:
            print("[INFO] No data to clear")


if __name__ == "__main__":
    print(f"[START] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    clear_surge_data()

    print()
    print(f"[DONE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
