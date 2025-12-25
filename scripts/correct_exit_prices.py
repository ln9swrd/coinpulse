# -*- coding: utf-8 -*-
"""
Correct Exit Prices for Closed Surge Signals

This script recalculates exit prices for closed signals by finding the peak price
between signal detection time and closure time.

Logic:
1. Query all closed surge signals
2. For each signal, fetch historical candle data (sent_at ~ closed_at)
3. Find the highest price (peak) during that period
4. Update exit_price to the peak price
5. This represents the best possible exit if sold at peak

Note: This is more realistic than using current price at closure.
"""

import os
import sys
import requests
import time
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from backend.database.connection import get_db_session


def get_candle_data(market, from_date, to_date):
    """
    Get daily candle data from Upbit API

    Args:
        market: Market symbol (e.g., 'KRW-BTC')
        from_date: Start date (datetime)
        to_date: End date (datetime)

    Returns:
        List of candle data (newest first)
    """
    try:
        # Calculate days
        days = (to_date - from_date).days + 2  # Add buffer
        days = min(days, 200)  # Upbit max: 200 candles

        response = requests.get(
            'https://api.upbit.com/v1/candles/days',
            params={
                'market': market,
                'count': days,
                'to': to_date.strftime('%Y-%m-%dT%H:%M:%S')
            },
            timeout=10
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"[ERROR] Failed to get candles for {market}: {response.status_code}")
            return []

    except Exception as e:
        print(f"[ERROR] Failed to fetch candles for {market}: {e}")
        return []


def find_peak_price(candle_data, from_date, to_date):
    """
    Find the peak (highest) price in candle data within date range

    Args:
        candle_data: List of candle data
        from_date: Start date (datetime)
        to_date: End date (datetime)

    Returns:
        (peak_price: int, peak_date: datetime)
    """
    if not candle_data:
        return None, None

    peak_price = 0
    peak_date = None

    # Convert to dates for comparison (ignore time)
    from_date_only = from_date.date()
    to_date_only = to_date.date()

    for candle in candle_data:
        # Parse candle date
        candle_time_str = candle.get('candle_date_time_kst', '')
        try:
            candle_time = datetime.strptime(candle_time_str, '%Y-%m-%dT%H:%M:%S')
        except:
            continue

        # Check if within range (date only, ignore time)
        candle_date = candle_time.date()
        if candle_date < from_date_only or candle_date > to_date_only:
            continue

        # Get high price
        high_price = int(candle.get('high_price', 0))

        if high_price > peak_price:
            peak_price = high_price
            peak_date = candle_time

    return peak_price, peak_date


def correct_exit_prices():
    """
    Correct exit prices for all closed signals
    """
    print("=" * 80)
    print("Correct Exit Prices for Closed Surge Signals")
    print("=" * 80)
    print()

    with get_db_session() as session:
        # Get all closed signals
        query = text("""
            SELECT id, market, coin, status, entry_price, target_price, exit_price,
                   sent_at, closed_at,
                   EXTRACT(EPOCH FROM (closed_at - sent_at))/3600 as duration_hours
            FROM surge_alerts
            WHERE status IN ('closed', 'win', 'lose', 'expired')
              AND sent_at IS NOT NULL
              AND (closed_at IS NOT NULL OR status IN ('win', 'lose', 'expired'))
            ORDER BY sent_at DESC
        """)

        result = session.execute(query)
        signals = result.fetchall()

        print(f"[INFO] Found {len(signals)} closed signals to correct")
        print()

        corrected = 0
        skipped = 0
        failed = 0

        for signal in signals:
            sid, market, coin, status, entry, target, old_exit, sent_at, closed_at, duration = signal

            print(f"[{corrected + skipped + failed + 1}/{len(signals)}] {coin} (ID: {sid})")
            print(f"  Market: {market}")
            print(f"  Status: {status}")
            print(f"  Entry: {entry:,}원" if entry else "  Entry: N/A")
            print(f"  Old Exit: {old_exit:,}원" if old_exit else "  Old Exit: N/A")
            print(f"  Period: {sent_at.strftime('%Y-%m-%d')} ~ {closed_at.strftime('%Y-%m-%d') if closed_at else 'N/A'}")

            # Validate
            if not market or not sent_at:
                print(f"  [SKIP] Skipping (missing market or sent_at)")
                skipped += 1
                print()
                continue

            # Use closed_at or now
            end_date = closed_at if closed_at else datetime.now()

            # Fetch candle data
            print(f"  [FETCH] Fetching candle data...")
            candle_data = get_candle_data(market, sent_at, end_date)

            if not candle_data:
                print(f"  [ERROR] Failed to fetch candle data")
                failed += 1
                print()
                time.sleep(0.2)  # Rate limit
                continue

            # Find peak price
            peak_price, peak_date = find_peak_price(candle_data, sent_at, end_date)

            if not peak_price:
                print(f"  [ERROR] No peak price found")
                failed += 1
                print()
                time.sleep(0.2)
                continue

            print(f"  [PEAK] Peak: {peak_price:,}won at {peak_date.strftime('%Y-%m-%d')}")

            # Calculate gain
            if entry and entry > 0:
                gain_pct = ((peak_price - entry) / entry) * 100
                print(f"  [GAIN] Gain: {gain_pct:+.2f}%")

            # Update exit_price
            update_query = text("""
                UPDATE surge_alerts
                SET exit_price = :exit_price
                WHERE id = :sid
            """)

            session.execute(update_query, {
                'sid': sid,
                'exit_price': peak_price
            })

            print(f"  [OK] Updated: {old_exit:,}won -> {peak_price:,}won" if old_exit else f"  [OK] Set to: {peak_price:,}won")

            corrected += 1
            print()

            # Rate limit
            time.sleep(0.2)

        # Commit all changes
        session.commit()

        print("=" * 80)
        print("Summary")
        print("=" * 80)
        print(f"Total signals: {len(signals)}")
        print(f"Corrected: {corrected}")
        print(f"Skipped: {skipped}")
        print(f"Failed: {failed}")
        print("=" * 80)


if __name__ == "__main__":
    print(f"[START] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    correct_exit_prices()

    print()
    print(f"[DONE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
