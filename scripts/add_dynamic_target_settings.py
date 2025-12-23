"""
자동매매 설정에 동적 목표가 필드 추가

새로운 필드:
- use_dynamic_target: 동적 목표가 사용 여부
- min_target_percent: 최소 목표 수익률
- max_target_percent: 최대 목표 수익률
- target_calculation_mode: 목표가 계산 모드 (fixed/dynamic/hybrid)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.database.connection import get_db_session


def add_dynamic_target_columns():
    """Add dynamic target price columns to surge_auto_trading_settings"""

    with get_db_session() as session:
        print("\n=== 동적 목표가 설정 필드 추가 ===\n")

        # Check existing columns
        check_query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'surge_auto_trading_settings'
        """)
        existing_columns = [row[0] for row in session.execute(check_query).fetchall()]
        print(f"기존 컬럼 수: {len(existing_columns)}개\n")

        # Define new columns
        new_columns = {
            'use_dynamic_target': 'BOOLEAN DEFAULT TRUE',
            'min_target_percent': 'DOUBLE PRECISION DEFAULT 5.0',
            'max_target_percent': 'DOUBLE PRECISION DEFAULT 18.0',
            'target_calculation_mode': "VARCHAR(20) DEFAULT 'dynamic'",
        }

        # Add columns if they don't exist
        added_count = 0
        for column, datatype in new_columns.items():
            if column not in existing_columns:
                try:
                    alter_query = text(f"""
                        ALTER TABLE surge_auto_trading_settings
                        ADD COLUMN {column} {datatype}
                    """)
                    session.execute(alter_query)
                    session.commit()
                    print(f"[OK] 컬럼 추가: {column} ({datatype})")
                    added_count += 1
                except Exception as e:
                    print(f"[ERROR] {column} 추가 실패: {e}")
                    session.rollback()
            else:
                print(f"[SKIP] 이미 존재: {column}")

        print(f"\n총 {added_count}개 컬럼 추가 완료\n")

        # Verify additions
        check_query = text("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'surge_auto_trading_settings'
            AND column_name IN ('use_dynamic_target', 'min_target_percent',
                               'max_target_percent', 'target_calculation_mode')
            ORDER BY column_name
        """)

        results = session.execute(check_query).fetchall()

        if results:
            print("=== 새로 추가된 컬럼 확인 ===\n")
            for row in results:
                print(f"  {row[0]:25s} | {row[1]:20s} | {row[2]}")
            print()

        # Show example usage
        print("=== 설정 예시 ===\n")
        print("1. 동적 목표가 사용 (기본값):")
        print("   use_dynamic_target = TRUE")
        print("   target_calculation_mode = 'dynamic'")
        print("   min_target_percent = 5.0")
        print("   max_target_percent = 18.0")
        print("   → 신호 강도에 따라 5~18% 범위에서 자동 계산\n")

        print("2. 고정 목표가 사용:")
        print("   use_dynamic_target = FALSE")
        print("   target_calculation_mode = 'fixed'")
        print("   take_profit_percent = 10.0")
        print("   → 항상 10% 고정\n")

        print("3. 하이브리드 모드:")
        print("   use_dynamic_target = TRUE")
        print("   target_calculation_mode = 'hybrid'")
        print("   take_profit_percent = 8.0 (기준값)")
        print("   min_target_percent = 5.0")
        print("   max_target_percent = 15.0")
        print("   → 기준값 8%에서 신호 강도에 따라 5~15% 조정\n")

        print("완료!")


if __name__ == "__main__":
    add_dynamic_target_columns()
