# -*- coding: utf-8 -*-
"""
Analyze backtest patterns to identify scoring issues
Compare high-score vs zero-score surges
"""

import json
import statistics

def analyze_patterns():
    """Analyze backtest results to find scoring optimization opportunities"""

    # Load results
    with open('backtest_results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)

    print("=" * 100)
    print("PATTERN ANALYSIS: High Score vs Zero Score")
    print("=" * 100)

    # Group by score
    high_score = [r for r in results if r['v2_score'] >= 60]
    mid_score = [r for r in results if 30 <= r['v2_score'] < 60]
    low_score = [r for r in results if 1 <= r['v2_score'] < 30]
    zero_score = [r for r in results if r['v2_score'] == 0]

    print(f"\nGroup Statistics:")
    print(f"High Score (60+):  {len(high_score):4} surges, avg gain: {avg_gain(high_score):.1f}%")
    print(f"Mid Score (30-59): {len(mid_score):4} surges, avg gain: {avg_gain(mid_score):.1f}%")
    print(f"Low Score (1-29):  {len(low_score):4} surges, avg gain: {avg_gain(low_score):.1f}%")
    print(f"Zero Score (0):    {len(zero_score):4} surges, avg gain: {avg_gain(zero_score):.1f}%")

    # Find high-gain zero-score surges (biggest misses)
    high_gain_zeros = [r for r in zero_score if r['peak_gain'] >= 30]
    high_gain_zeros.sort(key=lambda x: x['peak_gain'], reverse=True)

    print(f"\n" + "=" * 100)
    print(f"BIGGEST MISSES: Zero Score but 30%+ Gain ({len(high_gain_zeros)} events)")
    print("=" * 100)

    print(f"\nTop 20 Missed Opportunities:")
    print("-" * 100)
    for i, event in enumerate(high_gain_zeros[:20], 1):
        print(f"{i:2}. {event['market']:12} | Gain: {event['peak_gain']:6.1f}% | "
              f"Date: {event['surge_date'][:10]} | Timing: {event['v2_timing']}")

        # Show signals
        signals = event.get('v2_signals', {})
        if signals:
            print(f"    Signals: ", end="")
            for key, val in signals.items():
                if isinstance(val, dict):
                    score = val.get('score', 0)
                    print(f"{key}={score} ", end="")
            print()

    # Analyze signal patterns
    print("\n" + "=" * 100)
    print("SIGNAL PATTERN COMPARISON")
    print("=" * 100)

    # Compare average signal scores
    signal_types = ['accumulation', 'support_bounce', 'early_momentum', 'volume_timing', 'pattern']

    print(f"\nAverage Signal Scores:")
    print("-" * 100)
    print(f"{'Signal Type':20} | {'High (60+)':>10} | {'Zero (0)':>10} | {'Diff':>8}")
    print("-" * 100)

    for sig_type in signal_types:
        high_avg = avg_signal_score(high_score, sig_type)
        zero_avg = avg_signal_score(zero_score, sig_type)
        diff = high_avg - zero_avg

        print(f"{sig_type:20} | {high_avg:10.1f} | {zero_avg:10.1f} | {diff:+8.1f}")

    # Find common patterns in high-score surges
    print("\n" + "=" * 100)
    print("HIGH SCORE (60+) PATTERN DETAILS")
    print("=" * 100)

    print(f"\nAll {len(high_score)} high-score surges:")
    print("-" * 100)

    for event in high_score:
        print(f"\n{event['market']:12} | Score: {event['v2_score']:3.0f} | "
              f"Gain: {event['peak_gain']:6.1f}% | Date: {event['surge_date'][:10]}")

        signals = event.get('v2_signals', {})
        if signals:
            print("  Signals breakdown:")
            for key, val in signals.items():
                if isinstance(val, dict):
                    score = val.get('score', 0)
                    details = {k: v for k, v in val.items() if k != 'score'}
                    print(f"    {key:20}: {score:2.0f} points - {details}")

    # Analyze zero-score patterns
    print("\n" + "=" * 100)
    print("ZERO SCORE PATTERN DETAILS (Sample 20)")
    print("=" * 100)

    print(f"\nSample from {len(zero_score)} zero-score surges:")
    print("-" * 100)

    for event in zero_score[:20]:
        print(f"\n{event['market']:12} | Score: 0 | "
              f"Gain: {event['peak_gain']:6.1f}% | Date: {event['surge_date'][:10]}")

        signals = event.get('v2_signals', {})
        if signals:
            print("  Signals breakdown:")
            for key, val in signals.items():
                if isinstance(val, dict):
                    score = val.get('score', 0)
                    details = {k: v for k, v in val.items() if k != 'score'}
                    if score > 0 or details:  # Show even if 0 score to see why
                        print(f"    {key:20}: {score:2.0f} points - {details}")

    # Calculate signal correlations
    print("\n" + "=" * 100)
    print("SIGNAL EFFECTIVENESS ANALYSIS")
    print("=" * 100)

    print("\nCorrelation: Signal Score vs Actual Gain")
    print("-" * 100)

    # For each signal type, calculate correlation with gain
    for sig_type in signal_types:
        # Get all events with this signal
        events_with_signal = []
        for event in results:
            signals = event.get('v2_signals', {})
            if sig_type in signals and isinstance(signals[sig_type], dict):
                sig_score = signals[sig_type].get('score', 0)
                gain = event['peak_gain']
                events_with_signal.append((sig_score, gain))

        if len(events_with_signal) > 10:
            # Calculate average gain for different score ranges
            low_sig = [g for s, g in events_with_signal if s == 0]
            mid_sig = [g for s, g in events_with_signal if 1 <= s < 10]
            high_sig = [g for s, g in events_with_signal if s >= 10]

            print(f"\n{sig_type}:")
            if low_sig:
                print(f"  Score 0:      {len(low_sig):4} events, avg gain: {statistics.mean(low_sig):6.1f}%")
            if mid_sig:
                print(f"  Score 1-9:    {len(mid_sig):4} events, avg gain: {statistics.mean(mid_sig):6.1f}%")
            if high_sig:
                print(f"  Score 10+:    {len(high_sig):4} events, avg gain: {statistics.mean(high_sig):6.1f}%")

    # Recommendations
    print("\n" + "=" * 100)
    print("RECOMMENDATIONS FOR V2 LOGIC ADJUSTMENT")
    print("=" * 100)

    print("""
    Based on the analysis:

    1. CRITICAL ISSUE: 93.4% of surges scored 0-39 points
       - These missed opportunities had avg 20.8% gain
       - Many 30%+ gains were completely missed

    2. SIGNAL EFFECTIVENESS:
       - Need to compare which signals actually correlate with gains
       - Current scoring may be too restrictive

    3. NEXT STEPS:
       a) Identify which conditions cause 0 scores most often
       b) Relax those conditions or reduce their weight
       c) Focus on signals that actually predict gains
       d) Aim for 70+ score to have 25%+ avg gain
       e) Aim for 40+ score threshold (capture more opportunities)

    4. PROPOSED CHANGES:
       - Lower minimum requirements for each signal
       - Increase point allocation for early signals
       - Reduce penalties for late entry (still valid if early enough)
       - Add more scoring tiers (not just 0 or max points)
    """)


def avg_gain(events):
    """Calculate average gain from list of events"""
    if not events:
        return 0.0
    return sum(e['peak_gain'] for e in events) / len(events)


def avg_signal_score(events, signal_type):
    """Calculate average score for a specific signal type"""
    scores = []
    for event in events:
        signals = event.get('v2_signals', {})
        if signal_type in signals and isinstance(signals[signal_type], dict):
            scores.append(signals[signal_type].get('score', 0))

    if not scores:
        return 0.0
    return sum(scores) / len(scores)


if __name__ == '__main__':
    analyze_patterns()
