# -*- coding: utf-8 -*-
"""
Cleanup low-confidence surge alerts (confidence < 60%)
기준미달 급등 알림 삭제 (신뢰도 60% 미만)

급등 예측 최소 기준(60점) 미만의 레코드 삭제
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database.connection import get_db_session
from sqlalchemy import text


def cleanup_low_confidence_alerts(dry_run=True, min_confidence=0.6):
    """
    Remove surge alerts below minimum confidence threshold

    Args:
        dry_run: If True, only show what would be deleted without actually deleting
        min_confidence: Minimum confidence threshold (default: 0.6 = 60%)
    """
    print("=" * 70)
    print("Low-Confidence Surge Alerts Cleanup")
    print("=" * 70)

    if dry_run:
        print("\n[DRY RUN MODE] - No actual deletion will occur")
    else:
        print("\n[LIVE MODE] - Records will be permanently deleted!")

    print(f"Minimum confidence threshold: {min_confidence * 100}%")

    session = get_db_session()

    try:
        # Step 1: Find low-confidence alerts
        print("\n[1/3] Analyzing low-confidence alerts...")

        result = session.execute(text("""
            SELECT
                COUNT(*) as total_count,
                MIN(confidence) as min_confidence,
                MAX(confidence) as max_confidence,
                AVG(confidence) as avg_confidence
            FROM surge_alerts
            WHERE confidence < :min_confidence;
        """), {'min_confidence': min_confidence})

        stats = result.fetchone()
        total_count, min_conf, max_conf, avg_conf = stats

        if total_count == 0:
            print(f"[OK] No alerts below {min_confidence * 100}% confidence found!")
            return

        print(f"[INFO] Found {total_count} alerts below threshold:\n")
        print(f"  - Confidence range: {min_conf * 100:.1f}% ~ {max_conf * 100:.1f}%")
        print(f"  - Average confidence: {avg_conf * 100:.1f}%")

        # Show sample records
        print("\n[2/3] Sample records to be deleted:")
        result = session.execute(text("""
            SELECT
                id,
                market,
                confidence,
                sent_at,
                status
            FROM surge_alerts
            WHERE confidence < :min_confidence
            ORDER BY confidence ASC
            LIMIT 10;
        """), {'min_confidence': min_confidence})

        samples = result.fetchall()
        print(f"\n{'ID':<8} {'Market':<15} {'Confidence':<12} {'Sent At':<20} {'Status'}")
        print("-" * 70)
        for id, market, conf, sent_at, status in samples:
            print(f"{id:<8} {market:<15} {conf * 100:>6.1f}% {str(sent_at)[:19]:<20} {status or 'N/A'}")

        if total_count > 10:
            print(f"... and {total_count - 10} more records")

        # Step 3: Delete
        if dry_run:
            print("\n[DRY RUN] Skipping actual deletion")
        else:
            print("\n[3/3] Deleting low-confidence alerts...")

            result = session.execute(
                text("DELETE FROM surge_alerts WHERE confidence < :min_confidence"),
                {'min_confidence': min_confidence}
            )
            session.commit()

            deleted_count = result.rowcount
            print(f"\n[OK] Successfully deleted {deleted_count} low-confidence alerts")

        # Verify results
        print("\n[VERIFICATION]")

        result = session.execute(text("""
            SELECT
                COUNT(*) as remaining_count,
                MIN(confidence) as min_confidence,
                MAX(confidence) as max_confidence
            FROM surge_alerts;
        """))

        remaining, min_conf, max_conf = result.fetchone()

        print(f"  - Remaining alerts: {remaining}")
        if remaining > 0:
            print(f"  - Confidence range: {min_conf * 100:.1f}% ~ {max_conf * 100:.1f}%")

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

    parser = argparse.ArgumentParser(description="Cleanup low-confidence surge alerts")
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually delete records (default is dry-run)'
    )
    parser.add_argument(
        '--min-confidence',
        type=float,
        default=0.6,
        help='Minimum confidence threshold (0.0-1.0, default: 0.6)'
    )

    args = parser.parse_args()

    cleanup_low_confidence_alerts(
        dry_run=not args.execute,
        min_confidence=args.min_confidence
    )
