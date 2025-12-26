# -*- coding: utf-8 -*-
"""
Import Backtest Data to Database
Import historical surge signals (score >= 60) from backtest results
"""

import json
from datetime import datetime
from backend.database.connection import get_db_session
from sqlalchemy import text
import os

def import_backtest_data(min_score=60):
    """
    Import backtest surge events to surge_alerts table

    Args:
        min_score: Minimum score threshold (default 60)
    """

    # Load backtest results
    print("Loading backtest results...")
    with open('backtest_results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)

    print(f"Total events in backtest: {len(results)}")

    # Filter by score
    candidates = [r for r in results if r['v2_score'] >= min_score]
    print(f"Events with score >= {min_score}: {len(candidates)}")

    if not candidates:
        print("No candidates to import")
        return

    # Get user ID (use admin/system user)
    # For demo purposes, we'll use user_id = 1
    # In production, you should create a "system" or "backtest" user
    user_id = 1

    print("\n" + "=" * 100)
    print(f"Importing {len(candidates)} surge signals to database...")
    print("=" * 100)

    with get_db_session() as session:
        imported = 0
        skipped = 0

        for event in candidates:
            try:
                market = event['market']
                surge_date = event['surge_date']
                entry_price = event['entry_price']
                peak_price = event['peak_price']
                peak_gain = event['peak_gain']
                score = event['v2_score']
                timing = event['v2_timing']
                pattern_type = event.get('pattern_type', 'unknown')

                # Parse date
                sent_at = datetime.strptime(surge_date[:19], '%Y-%m-%dT%H:%M:%S')

                # Calculate target and stop loss
                target_price = int(entry_price * 1.10)  # +10%
                stop_loss_price = int(entry_price * 0.95)  # -5%

                # Calculate days to peak
                days_to_peak = event.get('days_to_peak', 1)

                # Determine status and close info
                if peak_gain >= 10:
                    status = 'win'
                    exit_price = int(entry_price * 1.10)  # Target reached
                    profit_loss = exit_price - entry_price
                    profit_loss_percent = 10.0
                    close_reason = 'target_reached'
                elif peak_gain >= 5:
                    status = 'closed'
                    exit_price = int(peak_price)
                    profit_loss = exit_price - entry_price
                    profit_loss_percent = peak_gain
                    close_reason = 'manual_close'
                else:
                    status = 'lose'
                    exit_price = int(entry_price * 0.95)  # Stop loss
                    profit_loss = exit_price - entry_price
                    profit_loss_percent = -5.0
                    close_reason = 'stop_loss'

                # Create reason text
                signals = event.get('v2_signals', {})
                reason_parts = []

                if pattern_type == 'A_Accumulation':
                    reason_parts.append('Pattern A: Accumulation phase')
                elif pattern_type == 'B_OversoldBounce':
                    reason_parts.append('Pattern B: Oversold bounce')

                for sig_name, sig_data in signals.items():
                    if isinstance(sig_data, dict):
                        sig_score = sig_data.get('score', 0)
                        if sig_score > 0:
                            reason_parts.append(f'{sig_name}: {sig_score}pts')

                reason = ', '.join(reason_parts[:3])  # Top 3 signals

                alert_message = f"[BACKTEST] {market} surge detected (Score: {score}, {pattern_type})"

                # Check if already exists
                check_query = text("""
                    SELECT id FROM surge_alerts
                    WHERE market = :market AND sent_at = :sent_at AND user_id = :user_id
                """)

                existing = session.execute(check_query, {
                    'market': market,
                    'sent_at': sent_at,
                    'user_id': user_id
                }).fetchone()

                if existing:
                    skipped += 1
                    continue

                # Insert surge alert
                insert_query = text("""
                    INSERT INTO surge_alerts (
                        user_id, market, coin, confidence, signal_type,
                        entry_price, target_price, stop_loss_price, expected_return,
                        current_price, peak_price, exit_price,
                        reason, alert_message,
                        sent_at, status,
                        profit_loss, profit_loss_percent,
                        close_reason, closed_at,
                        auto_traded, trade_amount, order_id
                    ) VALUES (
                        :user_id, :market, :coin, :confidence, :signal_type,
                        :entry_price, :target_price, :stop_loss_price, :expected_return,
                        :current_price, :peak_price, :exit_price,
                        :reason, :alert_message,
                        :sent_at, :status,
                        :profit_loss, :profit_loss_percent,
                        :close_reason, :closed_at,
                        :auto_traded, :trade_amount, :order_id
                    )
                """)

                coin = market.replace('KRW-', '')

                session.execute(insert_query, {
                    'user_id': user_id,
                    'market': market,
                    'coin': coin,
                    'confidence': score,
                    'signal_type': 'surge',  # This is a surge signal
                    'entry_price': entry_price,
                    'target_price': target_price,
                    'stop_loss_price': stop_loss_price,
                    'expected_return': 10.0,
                    'current_price': exit_price if status in ['win', 'lose', 'closed'] else entry_price,
                    'peak_price': int(peak_price),
                    'exit_price': exit_price if status in ['win', 'lose', 'closed'] else None,
                    'reason': reason,
                    'alert_message': alert_message,
                    'sent_at': sent_at,
                    'status': status,
                    'profit_loss': profit_loss if status in ['win', 'lose', 'closed'] else None,
                    'profit_loss_percent': profit_loss_percent if status in ['win', 'lose', 'closed'] else None,
                    'close_reason': close_reason if status in ['win', 'lose', 'closed'] else None,
                    'closed_at': sent_at if status in ['win', 'lose', 'closed'] else None,
                    'auto_traded': False,  # Backtest data, not actually traded
                    'trade_amount': None,
                    'order_id': None
                })

                imported += 1

                if imported % 50 == 0:
                    print(f"Imported {imported} signals...")
                    session.commit()

            except Exception as e:
                print(f"Error importing {event.get('market', 'unknown')}: {str(e)}")
                continue

        # Final commit
        session.commit()

        print("\n" + "=" * 100)
        print(f"Import complete!")
        print(f"  Imported: {imported}")
        print(f"  Skipped (duplicates): {skipped}")
        print("=" * 100)

        # Show statistics
        stats_query = text("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'win' THEN 1 END) as wins,
                COUNT(CASE WHEN status = 'lose' THEN 1 END) as losses,
                COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed,
                AVG(confidence) as avg_score,
                AVG(CASE WHEN status IN ('win', 'lose', 'closed') THEN profit_loss_percent END) as avg_gain
            FROM surge_alerts
            WHERE user_id = :user_id
        """)

        stats = session.execute(stats_query, {'user_id': user_id}).fetchone()

        print("\nDatabase Statistics:")
        print("-" * 100)
        print(f"Total signals: {stats[0] or 0}")
        print(f"Wins: {stats[1] or 0}")
        print(f"Losses: {stats[2] or 0}")
        print(f"Closed: {stats[3] or 0}")

        wins = stats[1] or 0
        losses = stats[2] or 0
        total_closed = wins + losses

        print(f"Win rate: {(wins / total_closed * 100) if total_closed > 0 else 0:.1f}%")
        print(f"Average score: {stats[4]:.1f}" if stats[4] else "N/A")
        print(f"Average gain: {stats[5]:.1f}%" if stats[5] else "N/A")
        print("-" * 100)


if __name__ == '__main__':
    print("Backtest Data Import Tool")
    print("=" * 100)

    # Ask for confirmation
    print("\nThis will import backtest surge signals (score >= 60) to the database.")
    print("These are historical signals from 2025-10-01 onwards.")
    print("\nProceed? (y/n): ", end='')

    # For automated execution, skip confirmation
    # confirmation = input().strip().lower()
    # if confirmation != 'y':
    #     print("Import cancelled")
    #     exit(0)

    # Import with score >= 60
    import_backtest_data(min_score=60)

    print("\nImport completed successfully!")
