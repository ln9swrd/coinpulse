"""
Populate coin_price_history with historical BTC/ETH/XRP prices.

This script fetches historical daily candle data from Upbit for BTC, ETH, and XRP
and stores it in the shared coin_price_history table.

Usage:
    python scripts/populate_coin_price_history.py [days]

Examples:
    python scripts/populate_coin_price_history.py 365  # Last 365 days
    python scripts/populate_coin_price_history.py 0    # All available history (max 2000 days)
"""

import sys
import os
from datetime import datetime, timedelta, timezone
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.connection import get_db_session
from backend.common.upbit_api import UpbitAPI
from sqlalchemy import text


def get_historical_prices(api, market, days):
    """
    Get historical daily candle data for a market.

    Args:
        api: UpbitAPI instance
        market: Market code (e.g., 'KRW-BTC')
        days: Number of days (0 = all available, max 200 per request)

    Returns:
        list: List of candle data dicts with date, open, high, low, close, volume
    """
    try:
        print(f"[CoinPrice] Fetching {market} prices...")

        all_candles = []

        if days == 0:
            # Get all available data (max ~2000 days)
            max_candles = 2000
            count_per_request = 200
        else:
            max_candles = days
            count_per_request = min(200, days)

        fetched_count = 0
        to_date = None  # Start from today

        while fetched_count < max_candles:
            # Calculate how many to fetch in this request
            remaining = max_candles - fetched_count
            count = min(count_per_request, remaining)

            # Fetch candles
            params = {'market': market, 'count': count}
            if to_date:
                params['to'] = to_date

            candles = api.get_candles_days(**params)

            if not candles:
                break

            all_candles.extend(candles)
            fetched_count += len(candles)

            # For next iteration, use the oldest candle's datetime as 'to'
            if len(candles) == count:
                oldest_candle_time = candles[-1].get('candle_date_time_kst', '')
                if oldest_candle_time:
                    # Use the full datetime string (업비트 API accepts this format)
                    to_date = oldest_candle_time
                else:
                    break
            else:
                # Got fewer candles than requested, we're at the end
                break

            # Rate limiting
            time.sleep(0.1)

            if days == 0:
                print(f"  Fetched {fetched_count} candles so far...")

        print(f"  ✓ Fetched {len(all_candles)} candles for {market}")

        return all_candles

    except Exception as e:
        print(f"  ❌ Error fetching {market}: {e}")
        return []


def insert_candles(db, market, candles):
    """
    Insert candle data into coin_price_history table.

    Args:
        db: Database session
        market: Market code
        candles: List of candle data dicts

    Returns:
        int: Number of rows inserted
    """
    try:
        inserted = 0
        skipped = 0

        for candle in candles:
            # Extract data
            date_str = candle.get('candle_date_time_kst', '')[:10]  # YYYY-MM-DD
            open_price = float(candle.get('opening_price', 0))
            high_price = float(candle.get('high_price', 0))
            low_price = float(candle.get('low_price', 0))
            close_price = float(candle.get('trade_price', 0))
            volume = float(candle.get('candle_acc_trade_volume', 0))

            if not date_str or close_price == 0:
                continue

            # Insert with ON CONFLICT DO NOTHING (skip duplicates)
            query = text("""
                INSERT INTO coin_price_history
                (market, date, open_price, high_price, low_price, close_price, volume)
                VALUES (:market, :date, :open_price, :high_price, :low_price, :close_price, :volume)
                ON CONFLICT (market, date) DO NOTHING
            """)

            result = db.execute(query, {
                'market': market,
                'date': date_str,
                'open_price': open_price,
                'high_price': high_price,
                'low_price': low_price,
                'close_price': close_price,
                'volume': volume
            })

            if result.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

        db.commit()

        return inserted, skipped

    except Exception as e:
        db.rollback()
        print(f"  ❌ Error inserting data for {market}: {e}")
        return 0, 0


def main():
    """Main function."""
    print("=" * 70)
    print("  Populate Coin Price History")
    print("=" * 70)
    print()

    # Get days parameter
    if len(sys.argv) > 1:
        days = int(sys.argv[1])
        print(f"[CoinPrice] Using days from command line: {days}")
    else:
        days = 365
        print(f"[CoinPrice] Using default days: {days}")

    if days == 0:
        print("[CoinPrice] Mode: ALL AVAILABLE HISTORY (max ~2000 days)")
    else:
        print(f"[CoinPrice] Mode: LAST {days} DAYS")

    print()

    # Initialize API (no auth needed for public data)
    # Pass None for keys since we're only fetching public market data
    api = UpbitAPI(access_key=None, secret_key=None)

    # Markets to fetch
    markets = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP']

    db = get_db_session()

    total_inserted = 0
    total_skipped = 0

    for market in markets:
        print(f"[CoinPrice] Processing {market}...")

        # Fetch historical prices
        candles = get_historical_prices(api, market, days)

        if candles:
            # Insert into database
            inserted, skipped = insert_candles(db, market, candles)
            total_inserted += inserted
            total_skipped += skipped

            print(f"  ✓ {market}: {inserted} inserted, {skipped} skipped (duplicates)")
        else:
            print(f"  ⚠️  {market}: No data fetched")

        print()

    db.close()

    # Summary
    print("=" * 70)
    print("  Summary")
    print("=" * 70)
    print(f"Total Records Inserted: {total_inserted}")
    print(f"Total Skipped (Duplicates): {total_skipped}")
    print("=" * 70)
    print()

    if total_inserted > 0:
        print("✓ Coin price history populated successfully!")
        print()
        print("Next steps:")
        print("1. Update backfill script to use shared coin prices")
        print("2. Create API endpoint: /api/coin-prices/history")
        print("3. Update frontend to fetch coin prices separately")
    else:
        print("⚠️  No new records inserted (data already exists or fetch failed)")

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print("[CoinPrice] Interrupted by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"[CoinPrice] Fatal error: {e}")
        sys.exit(1)
