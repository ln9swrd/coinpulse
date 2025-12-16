"""
Database Migration: Add Auto-Trading Fields to UserConfig

Adds 3 new columns to user_configs table:
- budget_per_position_krw (integer)
- monitored_coins (jsonb)
- auto_trading_enabled (boolean)
"""

import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.database import get_db_session, init_database


def migrate_user_config():
    """Add new columns to user_configs table."""

    print("=" * 70)
    print("MIGRATING USER_CONFIGS TABLE")
    print("=" * 70)

    # Initialize database connection
    init_database(create_tables=False)

    session = get_db_session()

    try:
        # Migration SQL for PostgreSQL
        migrations = [
            # 1. Add budget_per_position_krw column
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='user_configs'
                    AND column_name='budget_per_position_krw'
                ) THEN
                    ALTER TABLE user_configs
                    ADD COLUMN budget_per_position_krw INTEGER DEFAULT 10000;
                    COMMENT ON COLUMN user_configs.budget_per_position_krw IS 'Budget per position in KRW';
                    RAISE NOTICE 'Added budget_per_position_krw column';
                ELSE
                    RAISE NOTICE 'Column budget_per_position_krw already exists';
                END IF;
            END $$;
            """,

            # 2. Add monitored_coins column
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='user_configs'
                    AND column_name='monitored_coins'
                ) THEN
                    ALTER TABLE user_configs
                    ADD COLUMN monitored_coins JSONB DEFAULT '[]'::jsonb;
                    COMMENT ON COLUMN user_configs.monitored_coins IS 'List of monitored coin symbols';
                    RAISE NOTICE 'Added monitored_coins column';
                ELSE
                    RAISE NOTICE 'Column monitored_coins already exists';
                END IF;
            END $$;
            """,

            # 3. Add auto_trading_enabled column
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='user_configs'
                    AND column_name='auto_trading_enabled'
                ) THEN
                    ALTER TABLE user_configs
                    ADD COLUMN auto_trading_enabled BOOLEAN DEFAULT FALSE;
                    COMMENT ON COLUMN user_configs.auto_trading_enabled IS 'Auto trading enabled';
                    RAISE NOTICE 'Added auto_trading_enabled column';
                ELSE
                    RAISE NOTICE 'Column auto_trading_enabled already exists';
                END IF;
            END $$;
            """
        ]

        # Execute migrations
        for i, sql in enumerate(migrations, 1):
            print(f"\n[Migration {i}/{len(migrations)}] Executing...")
            session.execute(text(sql))
            session.commit()
            print(f"[OK] Migration {i} completed")

        # Verify columns
        print("\n[Verify] Checking new columns...")
        result = session.execute(text("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'user_configs'
            AND column_name IN ('budget_per_position_krw', 'monitored_coins', 'auto_trading_enabled')
            ORDER BY column_name
        """))

        columns = result.fetchall()
        if len(columns) == 3:
            print("[OK] All 3 columns exist:")
            for col in columns:
                print(f"     - {col[0]}: {col[1]} (default: {col[2]})")
        else:
            print(f"[WARNING] Expected 3 columns, found {len(columns)}")

        print("\n" + "=" * 70)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 70)
        return True

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        session.close()


if __name__ == '__main__':
    success = migrate_user_config()
    sys.exit(0 if success else 1)
