# -*- coding: utf-8 -*-
"""
Auto-close surge signals based on time and momentum

Criteria:
1. Close signals older than 72 hours (3 days)
2. Close signals with insufficient upward momentum
3. Consolidate duplicate signals for same coin (keep latest)
"""

import os
import sys
import requests
from datetime import datetime, timedelta

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from backend.database.connection import get_db_session


def get_current_price(market):
    """Get current price from Upbit API"""
    try:
        response = requests.get(
            'https://api.upbit.com/v1/ticker',
            params={'markets': market},
            timeout=5
        )
        if response.status_code == 200:
            ticker_data = response.json()
            if ticker_data and len(ticker_data) > 0:
                return int(ticker_data[0]['trade_price'])
    except Exception as e:
        print(f"[ERROR] Failed to get price for {market}: {e}")
    return None


def check_momentum(entry_price, current_price, target_price):
    """
    Check if signal has upward momentum

    Returns:
        (has_momentum: bool, reason: str, change_percent: float)
    """
    if not entry_price or not current_price:
        return False, "Missing price data", 0.0

    change_percent = ((current_price - entry_price) / entry_price) * 100

    # Negative momentum: price dropped
    if change_percent < -2.0:
        return False, f"Price dropped {abs(change_percent):.2f}%", change_percent

    # Stagnant: less than 1% move in 72 hours
    if abs(change_percent) < 1.0:
        return False, f"Stagnant (only {change_percent:.2f}% move)", change_percent

    # If target price exists, check if we're moving towards it
    if target_price:
        progress = ((current_price - entry_price) / (target_price - entry_price)) * 100
        if progress < 10:  # Less than 10% progress towards target
            return False, f"Low progress towards target ({progress:.1f}%)", change_percent

    return True, "Good momentum", change_percent


def auto_close_signals():
    """Auto-close surge signals based on criteria"""
    print("=" * 80)
    print("Auto-Close Surge Signals")
    print("=" * 80)
    print()

    cutoff_time = datetime.utcnow() - timedelta(hours=72)

    with get_db_session() as session:
        # Get all active (non-closed) signals
        query = text("""
            SELECT id, market, coin, status, entry_price, target_price,
                   sent_at, closed_at,
                   EXTRACT(EPOCH FROM (NOW() - sent_at))/3600 as hours_ago
            FROM surge_alerts
            WHERE (closed_at IS NULL OR status != 'closed')
              AND status IN ('pending', 'active')
            ORDER BY sent_at DESC
        """)

        result = session.execute(query)
        signals = result.fetchall()

        print(f"[INFO] Active signals to check: {len(signals)}")
        print()

        closed_count = 0
        kept_count = 0

        # Track coins to consolidate duplicates
        coin_signals = {}

        for signal in signals:
            sid, market, coin, status, entry, target, sent_at, closed_at, hours_ago = signal

            # Track for duplicate consolidation
            if coin not in coin_signals:
                coin_signals[coin] = []
            coin_signals[coin].append({
                'id': sid,
                'hours_ago': hours_ago,
                'sent_at': sent_at
            })

            print(f"[{closed_count + kept_count + 1}/{len(signals)}] {coin} (ID: {sid})")
            print(f"  Market: {market}")
            print(f"  Status: {status}")
            print(f"  Hours ago: {hours_ago:.1f}h")
            print(f"  Entry: {entry:,}원" if entry else "  Entry: N/A")

            should_close = False
            close_reason = ""

            # Check 1: Time-based (72 hours)
            if hours_ago >= 72:
                should_close = True
                close_reason = f"Expired (>{hours_ago:.0f}h old)"

            # Check 2: Momentum-based (if not already closing due to time)
            if not should_close and entry:
                current_price = get_current_price(market)
                if current_price:
                    print(f"  Current: {current_price:,}원")
                    has_momentum, reason, change_pct = check_momentum(entry, current_price, target)

                    if not has_momentum:
                        should_close = True
                        close_reason = reason
                    else:
                        print(f"  ✓ {reason} ({change_pct:+.2f}%)")
                else:
                    print(f"  ⚠ Could not fetch current price")

            # Close the signal if needed
            if should_close:
                print(f"  ✗ CLOSING: {close_reason}")

                # Get exit price
                exit_price = get_current_price(market) if market else None
                if not exit_price and target:
                    exit_price = target
                elif not exit_price and entry:
                    exit_price = entry

                # Update signal
                update_query = text("""
                    UPDATE surge_alerts
                    SET status = 'closed',
                        closed_at = NOW(),
                        exit_price = :exit_price
                    WHERE id = :sid
                """)

                session.execute(update_query, {
                    'sid': sid,
                    'exit_price': exit_price
                })

                closed_count += 1
            else:
                print(f"  ✓ Keeping signal")
                kept_count += 1

            print()

        # Consolidate duplicates (keep only latest for each coin)
        print("=" * 80)
        print("Consolidating Duplicate Signals")
        print("=" * 80)
        print()

        duplicate_closed = 0
        for coin, coin_list in coin_signals.items():
            if len(coin_list) > 1:
                # Sort by sent_at (latest first)
                coin_list.sort(key=lambda x: x['sent_at'], reverse=True)

                # Keep first (latest), close others
                keep_id = coin_list[0]['id']
                print(f"{coin}: {len(coin_list)} signals found")
                print(f"  ✓ Keeping latest: ID {keep_id}")

                for i, sig in enumerate(coin_list[1:], 1):
                    sid = sig['id']
                    print(f"  ✗ Closing duplicate #{i}: ID {sid}")

                    # Get current price for exit
                    market = f"KRW-{coin}"
                    exit_price = get_current_price(market)

                    update_query = text("""
                        UPDATE surge_alerts
                        SET status = 'closed',
                            closed_at = NOW(),
                            exit_price = COALESCE(:exit_price, entry_price, target_price)
                        WHERE id = :sid
                    """)

                    session.execute(update_query, {
                        'sid': sid,
                        'exit_price': exit_price
                    })

                    duplicate_closed += 1

                print()

        # Commit all changes
        session.commit()

        print("=" * 80)
        print("Summary")
        print("=" * 80)
        print(f"Total signals checked: {len(signals)}")
        print(f"Closed (time/momentum): {closed_count}")
        print(f"Closed (duplicates): {duplicate_closed}")
        print(f"Kept active: {kept_count - duplicate_closed}")
        print(f"Total closed: {closed_count + duplicate_closed}")
        print("=" * 80)


if __name__ == "__main__":
    print(f"[START] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    auto_close_signals()

    print()
    print(f"[DONE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
