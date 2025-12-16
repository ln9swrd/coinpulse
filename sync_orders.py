"""
Order Synchronization Script

Manually trigger order synchronization from Upbit API to database.

Usage:
    python sync_orders.py --initial          # Full sync (first time)
    python sync_orders.py --incremental      # New orders only
    python sync_orders.py --market KRW-BTC   # Specific market only
"""

import sys
import argparse
import json
from backend.common import UpbitAPI, load_api_keys
from backend.services.order_sync_service import OrderSyncService
from backend.database import init_database


def load_config():
    """Load trading server configuration."""
    try:
        with open('trading_server_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("[Warning] trading_server_config.json not found, using defaults")
        return {}


def main():
    """Run order synchronization."""
    parser = argparse.ArgumentParser(description='Synchronize Upbit orders to database')
    parser.add_argument('--initial', action='store_true', help='Perform initial full sync')
    parser.add_argument('--incremental', action='store_true', help='Perform incremental sync (new orders only)')
    parser.add_argument('--market', type=str, help='Market code to sync (e.g., KRW-BTC)')
    parser.add_argument('--max', type=int, default=10000, help='Maximum orders to sync (default: 10000)')

    args = parser.parse_args()

    # Load configuration
    config = load_config()

    # Check if database exists, initialize if needed
    print("[Sync] Initializing database connection...")
    init_database(create_tables=True, config=config)

    # Load API keys
    access_key, secret_key = load_api_keys()
    if not access_key or not secret_key:
        print("[Sync] ERROR: Upbit API keys not found in environment!")
        print("Please set UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY")
        return

    # Create API and sync service
    upbit_api = UpbitAPI(access_key, secret_key)
    sync_service = OrderSyncService(upbit_api)

    # Determine sync mode
    if args.initial:
        print("\n[Sync] Running INITIAL FULL SYNC")
        print("This will fetch all completed orders from Upbit (up to 3 months)")
        if args.market:
            print(f"Market filter: {args.market}")
        print()

        result = sync_service.initial_full_sync(market=args.market, max_orders=args.max)

    elif args.incremental:
        print("\n[Sync] Running INCREMENTAL SYNC")
        print("This will fetch only new orders since last sync")
        print()

        result = sync_service.incremental_sync(market=args.market)

    else:
        print("ERROR: Please specify either --initial or --incremental")
        parser.print_help()
        return

    # Print results
    print("\n" + "="*60)
    print("SYNC RESULTS:")
    print("="*60)
    for key, value in result.items():
        if key == 'errors' and value:
            print(f"{key}: {len(value)} errors")
            for error in value[:5]:  # Show first 5 errors
                print(f"  - {error}")
        else:
            print(f"{key}: {value}")
    print("="*60)


if __name__ == '__main__':
    main()
