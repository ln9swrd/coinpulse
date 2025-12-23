# -*- coding: utf-8 -*-
"""
Backtest Results Migration Script
백테스트 JSON 데이터를 데이터베이스로 마이그레이션
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.models.backtest_models import BacktestResult, BacktestSummary, init_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def load_json_backtest():
    """Load backtest results from JSON file"""
    json_path = project_root / 'docs' / 'backtest_results' / 'multi_date_backtest.json'

    print(f"[Migration] Loading JSON from: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"[Migration] Loaded JSON with {len(data.get('all_results', []))} results")
    return data


def migrate_backtest_results(session, json_data):
    """Migrate backtest results to database"""
    all_results = json_data.get('all_results', [])

    print(f"[Migration] Migrating {len(all_results)} backtest results...")

    migrated_count = 0
    skipped_count = 0

    for result in all_results:
        try:
            # Parse date
            date_str = result.get('date')
            if not date_str:
                print(f"[Migration] Skipping result without date: {result}")
                skipped_count += 1
                continue

            trade_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Extract market and coin
            market = result.get('market', '')
            coin = market.replace('KRW-', '') if market else ''

            # Check if already exists
            existing = session.query(BacktestResult).filter(
                BacktestResult.market == market,
                BacktestResult.trade_date == trade_date
            ).first()

            if existing:
                print(f"[Migration] Skipping duplicate: {market} on {date_str}")
                skipped_count += 1
                continue

            # Create backtest result
            backtest_result = BacktestResult(
                market=market,
                coin=coin,
                trade_date=trade_date,
                confidence_score=result.get('confidence', 0),
                entry_price=result.get('entry_price', 0),
                target_price=result.get('target_price'),
                stop_loss_price=result.get('stop_loss_price'),
                actual_high=result.get('actual_high'),
                actual_low=result.get('actual_low'),
                exit_price=result.get('exit_price'),
                return_pct=result.get('return_pct', 0),
                hold_days=result.get('hold_days'),
                success=result.get('success', False),
                reason=result.get('reason'),
                notes=result.get('notes')
            )

            session.add(backtest_result)
            migrated_count += 1

            # Commit in batches
            if migrated_count % 50 == 0:
                session.commit()
                print(f"[Migration] Committed {migrated_count} results...")

        except Exception as e:
            print(f"[Migration] Error migrating result {result}: {e}")
            skipped_count += 1
            continue

    # Final commit
    session.commit()

    print(f"[Migration] OK Migrated {migrated_count} results, skipped {skipped_count}")
    return migrated_count, skipped_count


def migrate_backtest_summary(session, json_data):
    """Migrate backtest summary to database"""
    summary = json_data.get('summary', {})

    if not summary:
        print("[Migration] No summary data found")
        return

    print("[Migration] Migrating backtest summary...")

    # Parse period
    period = summary.get('period', '')
    if '~' in period:
        start_str, end_str = period.split('~')
        start_date = datetime.strptime(start_str.strip(), '%Y-%m-%d').date()
        end_date = datetime.strptime(end_str.strip(), '%Y-%m-%d').date()
    else:
        print(f"[Migration] Invalid period format: {period}")
        return

    # Check if already exists
    existing = session.query(BacktestSummary).filter(
        BacktestSummary.start_date == start_date,
        BacktestSummary.end_date == end_date
    ).first()

    if existing:
        print(f"[Migration] Summary already exists for period {period}")
        return

    # Create summary
    backtest_summary = BacktestSummary(
        start_date=start_date,
        end_date=end_date,
        total_trades=summary.get('total_trades', 0),
        winning_trades=summary.get('winning_trades', 0),
        losing_trades=summary.get('losing_trades', 0),
        win_rate=summary.get('win_rate', 0),
        avg_return=summary.get('avg_return', 0),
        avg_win=summary.get('avg_win', 0),
        avg_loss=summary.get('avg_loss', 0),
        best_trade=summary.get('best_trade'),
        worst_trade=summary.get('worst_trade'),
        version='1.0',
        description='Multi-date backtest (2024-11-13 ~ 2024-12-07)'
    )

    session.add(backtest_summary)
    session.commit()

    print(f"[Migration] OK Summary migrated: {period}")


def main():
    """Main migration function"""
    print("\n" + "=" * 70)
    print("CoinPulse Backtest Results Migration")
    print("=" * 70 + "\n")

    # Get database URL
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        database_url = 'sqlite:///data/coinpulse.db'
        print(f"[Migration] Using default database: {database_url}")
    else:
        print(f"[Migration] Using database: {database_url}")

    # Convert postgres:// to postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    # Create engine
    if database_url.startswith('sqlite'):
        engine = create_engine(database_url, echo=False)
    else:
        engine = create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False
        )

    # Create tables
    print("[Migration] Creating database tables...")
    init_db(engine)

    # Create session from engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        # Load JSON data
        json_data = load_json_backtest()

        # Migrate results
        migrated, skipped = migrate_backtest_results(session, json_data)

        # Migrate summary
        migrate_backtest_summary(session, json_data)

        print("\n" + "=" * 70)
        print("Migration Complete!")
        print("=" * 70)
        print(f"OK Migrated: {migrated} results")
        print(f">> Skipped: {skipped} results")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\nERROR Migration failed: {e}")
        session.rollback()
        raise

    finally:
        session.close()


if __name__ == "__main__":
    main()
