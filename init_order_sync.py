"""
Initial Order Sync Script

Initializes database and performs first-time sync of all trading orders.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.database.connection import init_database
from backend.services.order_sync_service import OrderSyncService
from backend.common.upbit_api import UpbitAPI
from backend.common.config_loader import load_api_keys


def main():
    print("\n" + "="*70)
    print("COINPULSE ORDER SYNCHRONIZATION - INITIAL SYNC")
    print("="*70 + "\n")

    # Step 1: Initialize database (settings loaded from .env)
    print("[1/3] Initializing database...")
    try:
        engine = init_database(create_tables=True)
        print("[OK] Database initialized\n")
    except Exception as e:
        print(f"[ERROR] Failed to initialize database: {e}")
        return

    # Step 2: Initialize Upbit API
    print("[2/3] Loading API keys...")
    try:
        access_key, secret_key = load_api_keys()
        if not access_key or not secret_key:
            print("[ERROR] API keys not found!")
            print("Please set UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY environment variables")
            return

        upbit_api = UpbitAPI(access_key, secret_key)
        print(f"[OK] API keys loaded\n")
    except Exception as e:
        print(f"[ERROR] Failed to load API keys: {e}")
        return

    # Step 3: Run initial sync
    print("[3/3] Starting initial order synchronization...")
    print("This may take a few minutes depending on your trading history...\n")

    try:
        sync_service = OrderSyncService(upbit_api)

        # Sync all markets
        result = sync_service.initial_full_sync(
            market=None,  # All markets
            max_orders=10000  # Safety limit
        )

        if result['success']:
            print(f"\n[SUCCESS] Synchronization completed!")
            print(f"  - Total orders synced: {result['synced_count']}")
            print(f"  - Pages fetched: {result['pages']}")
            if result['errors']:
                print(f"  - Errors: {len(result['errors'])}")
                print("\nError details:")
                for error in result['errors'][:5]:  # Show first 5 errors
                    print(f"  - {error}")
        else:
            print(f"\n[FAILED] Synchronization failed: {result.get('error')}")
            print(f"  - Orders synced before failure: {result['synced_count']}")

    except Exception as e:
        print(f"\n[ERROR] Unexpected error during sync: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*70)
    print("SYNC COMPLETE")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()
