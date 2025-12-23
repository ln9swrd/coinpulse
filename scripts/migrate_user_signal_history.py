# -*- coding: utf-8 -*-
"""
Database Migration: Create user_signal_history Table
사용자 시그널 히스토리 테이블 생성

테이블: user_signal_history
- 사용자가 받은 시그널 내역
- 실행 여부 및 결과 추적
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db_session
from sqlalchemy import text
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def table_exists(session, table_name):
    """Check if table exists"""
    try:
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = :table_name
            )
        """)
        result = session.execute(query, {'table_name': table_name})
        return result.scalar()
    except Exception as e:
        logger.error(f"Error checking table existence: {e}")
        return False


def create_auto_trading_signals_table(session):
    """Create auto_trading_signals table (parent table)"""
    table_name = 'auto_trading_signals'

    if table_exists(session, table_name):
        logger.info(f"SKIP Table '{table_name}' already exists")
        return True

    logger.info(f"Creating parent table '{table_name}'...")

    session.execute(text("""
        CREATE TABLE auto_trading_signals (
            id SERIAL PRIMARY KEY,
            signal_id VARCHAR(50) UNIQUE NOT NULL,

            -- Market info
            market VARCHAR(20) NOT NULL,
            signal_type VARCHAR(10) NOT NULL,

            -- Price info
            entry_price BIGINT NOT NULL,
            target_price BIGINT NOT NULL,
            stop_loss BIGINT NOT NULL,

            -- Meta info
            confidence INTEGER NOT NULL,
            reason TEXT NULL,
            signals_data JSONB NULL,

            -- Time info
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            valid_until TIMESTAMP NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',

            -- Statistics
            distributed_to INTEGER DEFAULT 0,
            executed_count INTEGER DEFAULT 0
        )
    """))

    # Create indexes
    session.execute(text("""
        CREATE INDEX idx_auto_trading_signals_market
        ON auto_trading_signals(market)
    """))

    session.execute(text("""
        CREATE INDEX idx_auto_trading_signals_created_at
        ON auto_trading_signals(created_at)
    """))

    session.execute(text("""
        CREATE INDEX idx_auto_trading_signals_status
        ON auto_trading_signals(status)
    """))

    logger.info("✅ Parent table created successfully")
    return True


def create_user_signal_history_table():
    """Create user_signal_history table"""

    logger.info("=" * 60)
    logger.info("Trading Signal Tables Migration")
    logger.info("=" * 60)

    session = get_db_session()

    try:
        # Step 1: Create parent table first
        if not create_auto_trading_signals_table(session):
            return False

        # Step 2: Create child table
        table_name = 'user_signal_history'

        # Check if table already exists
        if table_exists(session, table_name):
            logger.info(f"SKIP Table '{table_name}' already exists")
            session.commit()
            return True

        logger.info(f"Creating child table '{table_name}'...")

        # Create table
        session.execute(text("""
            CREATE TABLE user_signal_history (
                id SERIAL PRIMARY KEY,

                -- Foreign keys
                user_id INTEGER NOT NULL,
                signal_id INTEGER NOT NULL REFERENCES auto_trading_signals(id),

                -- Receipt info
                received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_bonus BOOLEAN DEFAULT FALSE,

                -- Execution info
                execution_status VARCHAR(20) DEFAULT 'not_executed',
                executed_at TIMESTAMP NULL,
                order_id VARCHAR(50) NULL,
                execution_price BIGINT NULL,

                -- Result info
                result_status VARCHAR(20) NULL,
                profit_loss BIGINT NULL,
                profit_loss_ratio INTEGER NULL,

                -- Notes
                notes TEXT NULL
            )
        """))

        # Create indexes
        logger.info("Creating indexes...")

        session.execute(text("""
            CREATE INDEX idx_user_signal_history_user_id
            ON user_signal_history(user_id)
        """))

        session.execute(text("""
            CREATE INDEX idx_user_signal_history_signal_id
            ON user_signal_history(signal_id)
        """))

        session.execute(text("""
            CREATE INDEX idx_user_signal_history_received_at
            ON user_signal_history(received_at)
        """))

        session.execute(text("""
            CREATE INDEX idx_user_signal_history_execution
            ON user_signal_history(execution_status)
        """))

        session.commit()
        logger.info("✅ Table created successfully")
        logger.info("✅ Indexes created successfully")

        # Verify table exists
        if table_exists(session, table_name):
            logger.info("\n✅ Migration completed successfully!")
            logger.info(f"\nTable '{table_name}' structure:")
            logger.info("  - id: Primary key")
            logger.info("  - user_id: User reference")
            logger.info("  - signal_id: Signal reference")
            logger.info("  - received_at: When signal was received")
            logger.info("  - execution_status: not_executed/executed/failed/pending")
            logger.info("  - profit_loss: Profit/loss amount (KRW)")
            logger.info("  - profit_loss_ratio: Profit/loss percentage")
            return True
        else:
            logger.error("\n❌ ERROR Table creation verification failed!")
            return False

    except Exception as e:
        logger.error(f"\n❌ ERROR Migration failed: {e}")
        session.rollback()
        return False

    finally:
        session.close()


if __name__ == "__main__":
    logger.info("Starting user signal history migration...\n")

    success = create_user_signal_history_table()

    if success:
        logger.info("\n✅ Migration successful!")
        sys.exit(0)
    else:
        logger.error("\n❌ Migration failed!")
        sys.exit(1)
