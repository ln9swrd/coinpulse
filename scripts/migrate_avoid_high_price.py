# -*- coding: utf-8 -*-
"""
Database Migration: Add avoid_high_price_entry Field
고점 진입 방지 필드 추가 마이그레이션

새로운 컬럼:
- avoid_high_price_entry: BOOLEAN DEFAULT TRUE NOT NULL
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


def migrate_avoid_high_price_entry():
    """Add avoid_high_price_entry field to surge_auto_trading_settings table"""

    logger.info("=" * 60)
    logger.info("Avoid High Price Entry Migration")
    logger.info("=" * 60)

    session = get_db_session()

    try:
        table_name = 'surge_auto_trading_settings'

        # Check and add avoid_high_price_entry column
        if not check_column_exists(session, table_name, 'avoid_high_price_entry'):
            logger.info("Adding avoid_high_price_entry column...")
            session.execute(text("""
                ALTER TABLE surge_auto_trading_settings
                ADD COLUMN avoid_high_price_entry BOOLEAN DEFAULT TRUE NOT NULL
            """))
            session.commit()
            logger.info("✅ Added avoid_high_price_entry column")
        else:
            logger.info("SKIP avoid_high_price_entry column already exists")

        # Verify column exists
        logger.info("\nVerifying column...")
        exists = check_column_exists(session, table_name, 'avoid_high_price_entry')
        status = "✅ OK" if exists else "❌ MISSING"
        logger.info(f"  avoid_high_price_entry: {status}")

        if exists:
            logger.info("\n✅ Migration completed successfully!")
            logger.info("\nNew column added:")
            logger.info("  - avoid_high_price_entry: Prevent buying at peak prices")
            logger.info("    Checks: 24h price increase > 10%, RSI > 70, near recent high")
            return True
        else:
            logger.error("\n❌ ERROR Column is missing!")
            return False

    except Exception as e:
        logger.error(f"\n❌ ERROR Migration failed: {e}")
        session.rollback()
        return False

    finally:
        session.close()


if __name__ == "__main__":
    logger.info("Starting avoid high price entry migration...\n")

    success = migrate_avoid_high_price_entry()

    if success:
        logger.info("\n✅ Migration successful!")
        sys.exit(0)
    else:
        logger.error("\n❌ Migration failed!")
        sys.exit(1)
