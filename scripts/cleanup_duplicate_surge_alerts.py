# -*- coding: utf-8 -*-
"""
Cleanup duplicate surge alerts (same market + same day)
급등 알림 중복 레코드 정리 (같은 코인 + 같은 날)

같은 날 여러 번 저장된 레코드 중 가장 최근 레코드만 남기고 삭제
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database.connection import get_db_session
from sqlalchemy import text


def cleanup_duplicate_surge_alerts(dry_run=True):
    """
    Remove duplicate surge alerts (keep only the latest record per market per day)

    Args:
        dry_run: If True, only show what would be deleted without actually deleting
    """
    print("=" * 70)
    print("Surge Alerts Duplicate Cleanup")
    print("=" * 70)

    if dry_run:
        print("\n[DRY RUN MODE] - No actual deletion will occur")
    else:
        print("\n[LIVE MODE] - Records will be permanently deleted!")

    session = get_db_session()

    try:
        # Step 1: Find duplicates
        print("\n[1/3] Analyzing duplicates...")

        result = session.execute(text("""
            WITH ranked_alerts AS (
                SELECT
                    id,
                    market,
                    DATE(sent_at) as alert_date,
                    sent_at,
                    confidence,
                    ROW_NUMBER() OVER (
                        PARTITION BY market, DATE(sent_at)
                        ORDER BY sent_at DESC
                    ) as rn
                FROM surge_alerts
            )
            SELECT
                market,
                alert_date,
                COUNT(*) as total_records,
                MAX(sent_at) as latest_time,
                ARRAY_AGG(id ORDER BY sent_at) as all_ids
            FROM ranked_alerts
            GROUP BY market, alert_date
            HAVING COUNT(*) > 1
            ORDER BY total_records DESC, alert_date DESC;
        """))

        duplicates = result.fetchall()

        if not duplicates:
            print("[OK] No duplicates found!")
            return

        print(f"[INFO] Found {len(duplicates)} groups with duplicates:\n")

        total_to_delete = 0
        deletion_plan = []

        for market, alert_date, count, latest_time, all_ids in duplicates:
            ids_to_delete = all_ids[:-1]  # All except the last one (latest)
            id_to_keep = all_ids[-1]

            total_to_delete += len(ids_to_delete)
            deletion_plan.append((market, alert_date, ids_to_delete, id_to_keep))

            print(f"  {market} on {alert_date}:")
            print(f"    - Total: {count} records")
            print(f"    - Keep: ID {id_to_keep} (latest: {latest_time})")
            print(f"    - Delete: {len(ids_to_delete)} records (IDs: {ids_to_delete})")

        print(f"\n[SUMMARY] Total records to delete: {total_to_delete}")

        # Step 2: Delete duplicates
        if dry_run:
            print("\n[DRY RUN] Skipping actual deletion")
        else:
            print("\n[2/3] Deleting duplicates...")

            for market, alert_date, ids_to_delete, id_to_keep in deletion_plan:
                session.execute(
                    text("DELETE FROM surge_alerts WHERE id = ANY(:ids)"),
                    {'ids': ids_to_delete}
                )
                print(f"  [OK] Deleted {len(ids_to_delete)} records for {market} on {alert_date}")

            session.commit()
            print(f"\n[OK] Successfully deleted {total_to_delete} duplicate records")

        # Step 3: Verify results
        print("\n[3/3] Verification...")

        result = session.execute(text("""
            SELECT
                market,
                DATE(sent_at) as alert_date,
                COUNT(*) as records
            FROM surge_alerts
            GROUP BY market, DATE(sent_at)
            HAVING COUNT(*) > 1;
        """))

        remaining_duplicates = result.fetchall()

        if remaining_duplicates:
            print(f"[WARNING] Still {len(remaining_duplicates)} groups with duplicates")
        else:
            print("[OK] No more duplicates!")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        session.rollback()
    finally:
        session.close()

    print("\n" + "=" * 70)
    print("Cleanup completed!")
    print("=" * 70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cleanup duplicate surge alerts")
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually delete records (default is dry-run)'
    )

    args = parser.parse_args()

    cleanup_duplicate_surge_alerts(dry_run=not args.execute)
