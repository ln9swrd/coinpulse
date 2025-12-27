# -*- coding: utf-8 -*-
"""
Fix Surge Alerts Data
기존 surge_alerts 데이터의 profit_loss와 profit_loss_percent를 계산하여 업데이트
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_db_session
from sqlalchemy import text

def fix_surge_alerts():
    """Fix existing surge_alerts data"""

    print("=" * 100)
    print("FIXING SURGE ALERTS DATA")
    print("=" * 100)

    with get_db_session() as session:
        # Step 1: Update profit_loss and profit_loss_percent for closed signals
        print("\n[Step 1] Calculating profit/loss for closed signals...")

        update_query = text("""
            UPDATE surge_alerts
            SET
                profit_loss = exit_price - entry_price,
                profit_loss_percent = ROUND(((exit_price::FLOAT - entry_price::FLOAT) / entry_price::FLOAT * 100)::numeric, 2)
            WHERE
                status IN ('win', 'lose', 'closed')
                AND exit_price IS NOT NULL
                AND entry_price IS NOT NULL
                AND (profit_loss IS NULL OR profit_loss = 0 OR exit_price != entry_price + profit_loss)
        """)

        result = session.execute(update_query)
        session.commit()

        print(f"[OK] Updated {result.rowcount} records with profit/loss calculations")

        # Step 2: Update status based on profit_loss_percent
        print("\n[Step 2] Updating status based on profit/loss...")

        # Update 'closed' to 'win' if profit >= 5%
        win_query = text("""
            UPDATE surge_alerts
            SET status = 'win', close_reason = 'target_reached'
            WHERE status = 'closed'
              AND profit_loss_percent >= 5.0
        """)

        win_result = session.execute(win_query)
        print(f"[OK] Updated {win_result.rowcount} 'closed' -> 'win' (profit >= 5%)")

        # Update 'closed' to 'lose' if profit < 0
        lose_query = text("""
            UPDATE surge_alerts
            SET status = 'lose', close_reason = 'stop_loss'
            WHERE status = 'closed'
              AND profit_loss_percent < 0
        """)

        lose_result = session.execute(lose_query)
        print(f"[OK] Updated {lose_result.rowcount} 'closed' -> 'lose' (profit < 0%)")

        # Keep rest as 'closed' (0-5% profit) with manual_close
        manual_query = text("""
            UPDATE surge_alerts
            SET close_reason = 'manual_close'
            WHERE status = 'closed'
              AND close_reason IS NULL
        """)

        manual_result = session.execute(manual_query)
        print(f"[OK] Updated {manual_result.rowcount} 'closed' with 'manual_close' reason")

        session.commit()

        # Step 3: Verify results
        print("\n[Step 3] Verifying results...")

        verify_query = text("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'win' THEN 1 END) as wins,
                COUNT(CASE WHEN status = 'lose' THEN 1 END) as losses,
                COUNT(CASE WHEN status = 'closed' THEN 1 END) as closed,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                AVG(CASE WHEN status = 'win' THEN profit_loss_percent END) as avg_win_percent,
                AVG(CASE WHEN status = 'lose' THEN profit_loss_percent END) as avg_lose_percent,
                SUM(CASE WHEN status IN ('win', 'lose', 'closed') THEN profit_loss ELSE 0 END) as total_profit_loss
            FROM surge_alerts
            WHERE user_id = 1
        """)

        result = session.execute(verify_query).fetchone()

        total = result[0] or 0
        wins = result[1] or 0
        losses = result[2] or 0
        closed = result[3] or 0
        pending = result[4] or 0
        avg_win = result[5] or 0
        avg_lose = result[6] or 0
        total_pl = result[7] or 0

        print("\n" + "=" * 100)
        print("VERIFICATION RESULTS")
        print("=" * 100)
        print(f"Total Signals:     {total}")
        print(f"  - Wins:          {wins}")
        print(f"  - Losses:        {losses}")
        print(f"  - Closed (0-5%): {closed}")
        print(f"  - Pending:       {pending}")
        print(f"")
        print(f"Win Rate:          {(wins / (wins + losses) * 100) if (wins + losses) > 0 else 0:.1f}%")
        print(f"Avg Win:           {avg_win:.2f}%")
        print(f"Avg Loss:          {avg_lose:.2f}%")
        print(f"Total P/L:         {total_pl:,} KRW")
        print("=" * 100)

        # Step 4: Show sample data
        print("\n[Step 4] Sample data (top 10)...")
        sample_query = text("""
            SELECT id, market, confidence, status, entry_price, exit_price, profit_loss, profit_loss_percent
            FROM surge_alerts
            WHERE user_id = 1
            ORDER BY id DESC
            LIMIT 10
        """)

        sample_result = session.execute(sample_query)
        print("\nID  | Market     | Conf | Status  | Entry      | Exit       | P/L        | P/L%")
        print("-" * 95)
        for row in sample_result:
            entry = row[4] if row[4] else 0
            exit_price = row[5] if row[5] else 0
            pl = row[6] if row[6] else 0
            pl_pct = row[7] if row[7] else 0
            print(f"{row[0]:3} | {row[1]:10} | {row[2]:4.0f} | {row[3]:7} | {entry:10,} | "
                  f"{exit_price:10,} | {pl:+10,} | {pl_pct:+6.2f}%")

    print("\n" + "=" * 100)
    print("FIX COMPLETE")
    print("=" * 100)


if __name__ == '__main__':
    fix_surge_alerts()
