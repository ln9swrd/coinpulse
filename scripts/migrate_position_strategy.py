# -*- coding: utf-8 -*-
"""
Database Migration: Add Position Strategy Fields
포지션 전략 필드 추가 마이그레이션

새로운 컬럼:
- position_strategy: VARCHAR(20) DEFAULT 'single'
- max_amount_per_coin: BIGINT NULL
- allow_duplicate_positions: BOOLEAN DEFAULT FALSE
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db_session, engine
from sqlalchemy import text
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_column_exists(session, table_name, column_name):
    """Check if column exists in table"""
    try:
        # PostgreSQL query to check column existence
        query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = :table_name
            AND column_name = :column_name
        """)

        result = session.execute(query, {'table_name': table_name, 'column_name': column_name})
        return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking column existence: {e}")
        return False


def migrate_position_strategy_fields():
    """Add position strategy fields to surge_auto_trading_settings table"""

    logger.info("=" * 60)
    logger.info("Position Strategy Migration")
    logger.info("=" * 60)

    session = get_db_session()

    try:
        table_name = 'surge_auto_trading_settings'

        # 1. Check and add position_strategy column
        if not check_column_exists(session, table_name, 'position_strategy'):
            logger.info("Adding position_strategy column...")
            session.execute(text("""
                ALTER TABLE surge_auto_trading_settings
                ADD COLUMN position_strategy VARCHAR(20) DEFAULT 'single' NOT NULL
            """))
            session.commit()
            logger.info("OK Added position_strategy column")
        else:
            logger.info("SKIP position_strategy column already exists")

        # 2. Check and add max_amount_per_coin column
        if not check_column_exists(session, table_name, 'max_amount_per_coin'):
            logger.info("Adding max_amount_per_coin column...")
            session.execute(text("""
                ALTER TABLE surge_auto_trading_settings
                ADD COLUMN max_amount_per_coin BIGINT NULL
            """))
            session.commit()
            logger.info("OK Added max_amount_per_coin column")
        else:
            logger.info("SKIP max_amount_per_coin column already exists")

        # 3. Check and add allow_duplicate_positions column
        if not check_column_exists(session, table_name, 'allow_duplicate_positions'):
            logger.info("Adding allow_duplicate_positions column...")
            session.execute(text("""
                ALTER TABLE surge_auto_trading_settings
                ADD COLUMN allow_duplicate_positions BOOLEAN DEFAULT FALSE NOT NULL
            """))
            session.commit()
            logger.info("OK Added allow_duplicate_positions column")
        else:
            logger.info("SKIP allow_duplicate_positions column already exists")

        # 4. Verify all columns exist
        logger.info("\nVerifying columns...")
        columns_to_check = [
            'position_strategy',
            'max_amount_per_coin',
            'allow_duplicate_positions'
        ]

        all_exist = True
        for col in columns_to_check:
            exists = check_column_exists(session, table_name, col)
            status = "OK" if exists else "MISSING"
            logger.info(f"  {col}: {status}")
            if not exists:
                all_exist = False

        if all_exist:
            logger.info("\nOK Migration completed successfully!")
            logger.info("\nNew columns added:")
            logger.info("  - position_strategy: Choose 'single' or 'multiple' strategy")
            logger.info("  - max_amount_per_coin: Maximum total investment per coin")
            logger.info("  - allow_duplicate_positions: Allow multiple positions in same coin")
            return True
        else:
            logger.error("\nERROR Some columns are missing!")
            return False

    except Exception as e:
        logger.error(f"\nERROR Migration failed: {e}")
        session.rollback()
        return False

    finally:
        session.close()


if __name__ == "__main__":
    logger.info("Starting position strategy migration...\n")

    success = migrate_position_strategy_fields()

    if success:
        logger.info("\nOK Migration successful!")
        sys.exit(0)
    else:
        logger.error("\nERROR Migration failed!")
        sys.exit(1)
