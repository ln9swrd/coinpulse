# -*- coding: utf-8 -*-
"""
Trading Signals Database Initialization
trading_signals, user_signal_history 테이블 생성
"""

import os
import sys
from sqlalchemy import create_engine, inspect

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.models.trading_signal import Base, TradingSignal, UserSignalHistory
from backend.database.connection import get_database_url


def check_tables_exist(engine):
    """
    테이블 존재 여부 확인

    Args:
        engine: SQLAlchemy engine

    Returns:
        dict: {'auto_trading_signals': bool, 'user_signal_history': bool}
    """
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    return {
        'auto_trading_signals': 'auto_trading_signals' in existing_tables,
        'user_signal_history': 'user_signal_history' in existing_tables
    }


def init_trading_signals_db():
    """
    Trading signals 데이터베이스 초기화

    작업:
    1. 테이블 존재 여부 확인
    2. 없으면 생성
    3. 있으면 스킵
    """
    print("=" * 80)
    print("Trading Signals Database Initialization")
    print("=" * 80)

    # Get database URL
    database_url = get_database_url()
    print(f"\n[DB] Connecting to: {database_url.split('@')[-1] if '@' in database_url else database_url}")

    # Create engine
    engine = create_engine(database_url, echo=False)

    # Check existing tables
    print("\n[Check] Checking existing tables...")
    existing = check_tables_exist(engine)

    for table_name, exists in existing.items():
        status = "[OK] EXISTS" if exists else "[X] NOT FOUND"
        print(f"  - {table_name}: {status}")

    # Determine what to do
    if all(existing.values()):
        print("\n[Info] All tables already exist. Nothing to do.")
        print("\nIf you want to recreate tables:")
        print("  1. Drop tables manually in database")
        print("  2. Run this script again")
        return

    # Create missing tables
    print("\n[Create] Creating missing tables...")
    try:
        Base.metadata.create_all(engine)
        print("[OK] Tables created successfully!")

        # Verify creation
        print("\n[Verify] Verifying table creation...")
        existing = check_tables_exist(engine)
        for table_name, exists in existing.items():
            status = "[OK] CREATED" if exists else "[FAIL] FAILED"
            print(f"  - {table_name}: {status}")

        # Show table structure
        print("\n[Structure] Table columns:")
        inspector = inspect(engine)

        for table_name in ['auto_trading_signals', 'user_signal_history']:
            if table_name in inspector.get_table_names():
                print(f"\n  {table_name}:")
                columns = inspector.get_columns(table_name)
                for col in columns:
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    print(f"    - {col['name']}: {col['type']} {nullable}")

                # Show indexes
                indexes = inspector.get_indexes(table_name)
                if indexes:
                    print(f"\n  Indexes for {table_name}:")
                    for idx in indexes:
                        print(f"    - {idx['name']}: {idx['column_names']}")

    except Exception as e:
        print(f"\n[ERROR] Error creating tables: {e}")
        return

    print("\n" + "=" * 80)
    print("Database Initialization Complete!")
    print("=" * 80)

    # Next steps
    print("\n[Next Steps]")
    print("  1. Create Signal Generation Service")
    print("  2. Implement signal distribution logic")
    print("  3. Test signal creation and retrieval")
    print("  4. Integrate with Surge Prediction")
    print("  5. Add Telegram notifications")


def drop_tables_if_needed():
    """
    테이블 삭제 (개발 용도)

    주의: 프로덕션에서는 절대 사용 금지!
    """
    print("\n[WARNING] This will DROP all trading signal tables!")
    print("All data will be LOST!")
    confirm = input("Type 'yes' to confirm: ")

    if confirm.lower() != 'yes':
        print("Cancelled.")
        return

    database_url = get_database_url()
    engine = create_engine(database_url, echo=False)

    print("\n[Drop] Dropping tables...")
    try:
        Base.metadata.drop_all(engine)
        print("[OK] Tables dropped successfully!")
    except Exception as e:
        print(f"[ERROR] Error dropping tables: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Trading Signals Database Initialization')
    parser.add_argument('--drop', action='store_true', help='Drop existing tables (DANGEROUS!)')
    args = parser.parse_args()

    if args.drop:
        drop_tables_if_needed()
    else:
        init_trading_signals_db()
