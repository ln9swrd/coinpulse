"""
Migration Script: Add user_id column to holdings_history table

This script adds the user_id column to the holdings_history table
for multi-user support.

Usage:
    python scripts/migrate_holdings_history.py
"""

import os
import sys
from sqlalchemy import text, inspect

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.connection import get_db_session


def check_column_exists(db, table_name, column_name):
    """Check if column exists in table"""
    try:
        result = db.execute(text(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='{table_name}' AND column_name='{column_name}'
        """))
        return result.fetchone() is not None
    except:
        # Fallback for SQLite
        result = db.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result.fetchall()]
        return column_name in columns


def migrate():
    """Run the migration"""
    print("[Migration] Starting holdings_history migration...")

    db = get_db_session()

    try:
        # Check if user_id column already exists
        if check_column_exists(db, 'holdings_history', 'user_id'):
            print("[Migration] ✓ user_id column already exists, skipping migration")
            return

        print("[Migration] Adding user_id column to holdings_history table...")

        # SQLite and PostgreSQL compatible
        db.execute(text("""
            ALTER TABLE holdings_history
            ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
        """))

        print("[Migration] Creating index on user_id and snapshot_time...")
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_snapshot_time
            ON holdings_history(user_id, snapshot_time)
        """))

        db.commit()
        print("[Migration] ✓ Migration completed successfully")

    except Exception as e:
        print(f"[Migration] ✗ Error: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == '__main__':
    migrate()
