# -*- coding: utf-8 -*-
"""
Backtest Script: Find 10%+ surge patterns
Analyze pre-surge characteristics to optimize V2 scoring
"""

import json
import time
from datetime import datetime, timedelta
from backend.common.upbit_api import UpbitAPI
from backend.services.surge_predictor import SurgePredictor
import os

def analyze_surge_patterns():
    """
    Find coins with 10%+ surge since 2025-10-01
    Analyze their pre-surge characteristics
    """
    # Initialize API
    access_key = os.getenv('UPBIT_ACCESS_KEY', '')
    secret_key = os.getenv('UPBIT_SECRET_KEY', '')
    api = UpbitAPI(access_key, secret_key)

    # Load config
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    predictor = SurgePredictor(config)

    # Get all KRW markets
    print("Fetching all KRW markets...")
    all_markets = api.get_markets()
    krw_markets = [m['market'] for m in all_markets if m['market'].startswith('KRW-')]

    print(f"Total KRW markets: {len(krw_markets)}")
    print("=" * 100)

    surge_events = []

    for i, market in enumerate(krw_markets, 1):
        try:
            print(f"[{i}/{len(krw_markets)}] Analyzing {market}...", end=' ')

            # Get daily candles since 2025-10-01
            # We need ~90 days to find surges
            candles = api.get_candles_days(market, count=90)

            if not candles or len(candles) < 10:
                print("Insufficient data")
                continue

            # Find 10%+ surge events
            surges = find_surge_events(candles)

            if surges:
                print(f"Found {len(surges)} surge events")

                # Analyze each surge
                for surge in surges:
                    # Get pre-surge data (3 days before)
                    pre_surge_candles = get_pre_surge_data(candles, surge['surge_index'])

                    if not pre_surge_candles:
                        continue

                    # Analyze with V2 logic
                    entry_price = surge['entry_price']
                    result = predictor.analyze_coin(market, pre_surge_candles, entry_price)

                    surge_event = {
                        'market': market,
                        'surge_date': surge['surge_date'],
                        'entry_price': entry_price,
                        'peak_price': surge['peak_price'],
                        'peak_gain': surge['peak_gain'],
                        'v2_score': result.get('score', 0),
                        'v2_timing': result.get('entry_timing', 'unknown'),
                        'v2_signals': result.get('signals', {}),
                        'days_to_peak': surge['days_to_peak']
                    }

                    surge_events.append(surge_event)
            else:
                print("No surges")

            # Rate limit protection
            time.sleep(0.1)

        except Exception as e:
            print(f"Error: {str(e)[:50]}")
            continue

    print("=" * 100)
    print(f"\nTotal surge events found: {len(surge_events)}")

    # Analyze results
    analyze_results(surge_events)

    # Save results
    output_file = 'backtest_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(surge_events, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to {output_file}")

    return surge_events


def find_surge_events(candles):
    """
    Find 10%+ surge events in candle data

    Returns list of surge events with:
    - surge_date
    - entry_price (price at Day 0)
    - peak_price (highest price in next 3 days)
    - peak_gain (%)
    - days_to_peak
    """
    surges = []

    # Reverse to chronological order (oldest first)
    candles_chrono = list(reversed(candles))

    # Skip recent 3 days (no future data)
    for i in range(len(candles_chrono) - 3):
        entry_candle = candles_chrono[i]
        entry_price = float(entry_candle['trade_price'])
        entry_date = entry_candle['candle_date_time_kst']

        # Check if entry date is after 2025-10-01
        entry_dt = datetime.strptime(entry_date[:10], '%Y-%m-%d')
        if entry_dt < datetime(2025, 10, 1):
            continue

        # Find peak in next 3 days
        next_3_days = candles_chrono[i+1:i+4]

        if not next_3_days:
            continue

        peak_price = max(float(c['high_price']) for c in next_3_days)
        peak_gain = ((peak_price - entry_price) / entry_price) * 100

        # Find days to peak
        days_to_peak = 0
        for j, candle in enumerate(next_3_days, 1):
            if float(candle['high_price']) == peak_price:
                days_to_peak = j
                break

        # 10%+ surge
        if peak_gain >= 10.0:
            surges.append({
                'surge_index': i,
                'surge_date': entry_date,
                'entry_price': entry_price,
                'peak_price': peak_price,
                'peak_gain': peak_gain,
                'days_to_peak': days_to_peak
            })

    return surges


def get_pre_surge_data(candles, surge_index):
    """
    Get candles up to surge point (for V2 analysis)
    We want at least 30 days before surge
    """
    candles_chrono = list(reversed(candles))

    # Get candles up to surge point (not including surge day)
    pre_surge = candles_chrono[:surge_index]

    if len(pre_surge) < 30:
        return None

    # Reverse back to recent-first order (V2 expects this)
    return list(reversed(pre_surge))


def analyze_results(surge_events):
    """
    Analyze V2 scores vs actual surge outcomes
    """
    if not surge_events:
        print("\nNo surge events to analyze")
        return

    print("\n" + "=" * 100)
    print("BACKTEST RESULTS ANALYSIS")
    print("=" * 100)

    # Sort by V2 score
    surge_events.sort(key=lambda x: x['v2_score'], reverse=True)

    # Score brackets
    brackets = [
        (80, 100, "80-100"),
        (70, 79, "70-79"),
        (60, 69, "60-69"),
        (50, 59, "50-59"),
        (40, 49, "40-49"),
        (0, 39, "0-39")
    ]

    print("\nScore Distribution:")
    print("-" * 100)
    print(f"{'Score Range':12} | {'Count':>6} | {'Avg Gain':>9} | {'Max Gain':>9} | {'Min Gain':>9}")
    print("-" * 100)

    for min_score, max_score, label in brackets:
        events = [e for e in surge_events if min_score <= e['v2_score'] <= max_score]

        if events:
            avg_gain = sum(e['peak_gain'] for e in events) / len(events)
            max_gain = max(e['peak_gain'] for e in events)
            min_gain = min(e['peak_gain'] for e in events)

            print(f"{label:12} | {len(events):6} | {avg_gain:8.1f}% | {max_gain:8.1f}% | {min_gain:8.1f}%")

    print("-" * 100)

    # Top 20 surges
    print("\nTop 20 Surges by V2 Score:")
    print("-" * 100)
    print(f"{'Rank':4} | {'Market':12} | {'V2 Score':8} | {'Timing':8} | {'Gain':8} | {'Date':10}")
    print("-" * 100)

    for i, event in enumerate(surge_events[:20], 1):
        print(f"{i:4} | {event['market']:12} | {event['v2_score']:8.0f} | {event['v2_timing']:8} | "
              f"{event['peak_gain']:7.1f}% | {event['surge_date'][:10]}")

    print("-" * 100)

    # Bottom 20 surges (missed by V2)
    print("\nBottom 20 Surges (Missed by V2):")
    print("-" * 100)
    print(f"{'Rank':4} | {'Market':12} | {'V2 Score':8} | {'Timing':8} | {'Gain':8} | {'Date':10}")
    print("-" * 100)

    for i, event in enumerate(surge_events[-20:], 1):
        print(f"{i:4} | {event['market']:12} | {event['v2_score']:8.0f} | {event['v2_timing']:8} | "
              f"{event['peak_gain']:7.1f}% | {event['surge_date'][:10]}")

    print("-" * 100)

    # Calculate optimal threshold
    print("\nOptimal Score Threshold Analysis:")
    print("-" * 100)
    print(f"{'Threshold':10} | {'Signals':>7} | {'Avg Gain':>9} | {'Miss Rate':>10}")
    print("-" * 100)

    for threshold in [40, 45, 50, 55, 60, 65, 70, 75, 80]:
        signals = [e for e in surge_events if e['v2_score'] >= threshold]

        if signals:
            avg_gain = sum(e['peak_gain'] for e in signals) / len(signals)
            miss_rate = (len(surge_events) - len(signals)) / len(surge_events) * 100

            print(f"{threshold:10} | {len(signals):7} | {avg_gain:8.1f}% | {miss_rate:9.1f}%")

    print("-" * 100)


if __name__ == '__main__':
    print("Starting backtest analysis...")
    print("This will take several minutes due to API rate limits...")
    print()

    surge_events = analyze_surge_patterns()

    print("\nBacktest complete!")
