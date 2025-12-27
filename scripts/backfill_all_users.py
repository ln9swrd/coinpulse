"""
Backfill Balance History for All Users

Automatically finds all users with Upbit API keys configured
and runs balance history backfill for each user.

Usage:
    python scripts/backfill_all_users.py [days]

Examples:
    python scripts/backfill_all_users.py 365  # 365 days for all users
    python scripts/backfill_all_users.py 0    # All history for all users
    python scripts/backfill_all_users.py      # Default: 365 days
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.connection import get_db_session
from sqlalchemy import text
from scripts.backfill_balance_history import backfill_balance_history


def get_users_with_api_keys():
    """
    Get all users who have Upbit API keys configured.

    Returns:
        list: List of user IDs with API keys
    """
    try:
        db = get_db_session()

        # Query users with Upbit API keys (active and verified)
        query = text("""
            SELECT DISTINCT user_id
            FROM upbit_api_keys
            WHERE is_active = true
            AND access_key_encrypted IS NOT NULL
            AND access_key_encrypted != ''
            AND secret_key_encrypted IS NOT NULL
            AND secret_key_encrypted != ''
            ORDER BY user_id
        """)

        result = db.execute(query)
        user_ids = [row[0] for row in result]

        db.close()

        return user_ids

    except Exception as e:
        print(f"[BackfillAll] Error getting users: {e}")
        return []


def check_existing_snapshots(user_id):
    """
    Check how many snapshots already exist for a user.

    Args:
        user_id: User ID to check

    Returns:
        int: Number of existing snapshots
    """
    try:
        db = get_db_session()

        query = text("""
            SELECT COUNT(*)
            FROM holdings_history
            WHERE user_id = :user_id
        """)

        result = db.execute(query, {'user_id': user_id})
        count = result.scalar() or 0

        db.close()

        return count

    except Exception as e:
        print(f"[BackfillAll] Error checking snapshots for user {user_id}: {e}")
        return 0


def main():
    """Main function to backfill all users."""

    print("=" * 70)
    print("  Backfill Balance History for All Users")
    print("=" * 70)
    print()

    # Get days parameter
    if len(sys.argv) > 1:
        days = int(sys.argv[1])
        print(f"[BackfillAll] Using days from command line: {days}")
    else:
        days = 365
        print(f"[BackfillAll] Using default days: {days}")

    if days == 0:
        print("[BackfillAll] Mode: ALL HISTORY (entire trading history)")
    else:
        print(f"[BackfillAll] Mode: LAST {days} DAYS")

    print()

    # Get all users with API keys
    print("[BackfillAll] Step 1: Finding users with Upbit API keys...")
    user_ids = get_users_with_api_keys()

    if not user_ids:
        print("[BackfillAll] ❌ No users with API keys found")
        print("[BackfillAll] Please ensure users have configured their Upbit API keys")
        return

    print(f"[BackfillAll] ✓ Found {len(user_ids)} user(s) with API keys: {user_ids}")
    print()

    # Process each user
    print("[BackfillAll] Step 2: Processing users...")
    print()

    start_time = datetime.now()
    success_count = 0
    skip_count = 0
    error_count = 0

    for idx, user_id in enumerate(user_ids, 1):
        print("-" * 70)
        print(f"[BackfillAll] Processing User {user_id} ({idx}/{len(user_ids)})")
        print("-" * 70)

        try:
            # Check if user already has snapshots
            existing_count = check_existing_snapshots(user_id)

            if existing_count > 0:
                print(f"[BackfillAll] ⚠️  User {user_id} already has {existing_count} snapshots")
                print(f"[BackfillAll] Skipping backfill (to avoid duplicates)")
                print(f"[BackfillAll] To force re-backfill, delete existing data first:")
                print(f"[BackfillAll]   DELETE FROM holdings_history WHERE user_id = {user_id};")
                skip_count += 1
                print()
                continue

            # Run backfill for this user
            print(f"[BackfillAll] Starting backfill for User {user_id}...")
            print()

            backfill_balance_history(user_id, days=days)

            # Check results
            final_count = check_existing_snapshots(user_id)
            print()
            print(f"[BackfillAll] ✓ User {user_id} completed: {final_count} snapshots created")
            success_count += 1

        except Exception as e:
            print()
            print(f"[BackfillAll] ❌ Error processing User {user_id}: {e}")
            error_count += 1

        print()

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("=" * 70)
    print("  Backfill Summary")
    print("=" * 70)
    print(f"Total Users Found:    {len(user_ids)}")
    print(f"Successfully Backfilled: {success_count}")
    print(f"Skipped (Has Data):   {skip_count}")
    print(f"Errors:               {error_count}")
    print(f"Duration:             {duration:.1f} seconds")
    print("=" * 70)

    if success_count > 0:
        print()
        print("✓ Backfill completed successfully!")
        print()
        print("Next steps:")
        print("1. Users can now view their balance history chart")
        print("2. Chart will auto-update with new snapshots (via background sync)")
        print("3. Visit: https://coinpulse.sinsi.ai/dashboard.html#realtime")

    if error_count > 0:
        print()
        print(f"⚠️  {error_count} user(s) failed to backfill")
        print("Check the error messages above for details")

    if skip_count > 0:
        print()
        print(f"ℹ️  {skip_count} user(s) skipped (already have data)")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("[BackfillAll] Interrupted by user (Ctrl+C)")
        print("[BackfillAll] Partial data may have been saved")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"[BackfillAll] Fatal error: {e}")
        sys.exit(1)
