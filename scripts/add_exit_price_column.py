# -*- coding: utf-8 -*-
"""
surge_alerts 테이블에 exit_price 컬럼 추가 마이그레이션

PostgreSQL에 exit_price 컬럼을 추가합니다.
"""

import os
import sys
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from backend.database.connection import get_db_session


def add_exit_price_column():
    """
    surge_alerts 테이블에 exit_price 컬럼 추가
    """
    print("=" * 80)
    print("Database Migration: Add exit_price column to surge_alerts")
    print("=" * 80)
    print()

    try:
        with get_db_session() as session:
            # Check if column already exists
            check_query = text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'surge_alerts'
                  AND column_name = 'exit_price'
            """)

            result = session.execute(check_query)
            existing = result.fetchone()

            if existing:
                print("[INFO] Column 'exit_price' already exists. Skipping.")
                return

            # Add column
            alter_query = text("""
                ALTER TABLE surge_alerts
                ADD COLUMN exit_price BIGINT NULL
            """)

            session.execute(alter_query)
            session.commit()

            print("[OK] Column 'exit_price' added successfully to surge_alerts table.")
            print("    Type: BIGINT")
            print("    Nullable: YES")
            print()
            print("[NEXT] Run update_exit_prices.py to populate the new column.")

    except Exception as e:
        print(f"[ERROR] Failed to add column: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print(f"\n[START] Migration Script")
    print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    add_exit_price_column()

    print()
    print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("[DONE] Migration completed")
