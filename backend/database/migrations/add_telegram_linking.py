# -*- coding: utf-8 -*-
"""
Database Migration: Add Telegram Linking Support
Adds telegram_chat_id, telegram_username, telegram_linked_at to users table
Creates telegram_link_codes table for temporary linking codes
"""

import sys
import os
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from backend.database.connection import get_db_session
from datetime import datetime


def run_migration():
    """
    Run database migration to add Telegram linking support
    """
    session = get_db_session()

    try:
        print("[Migration] Starting Telegram linking migration...")

        # Check database type
        db_url = os.getenv('DATABASE_URL', '')
        is_postgresql = db_url.startswith('postgresql')

        # Add columns to users table
        print("[Migration] Adding telegram columns to users table...")

        if is_postgresql:
            # PostgreSQL syntax
            session.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS telegram_chat_id VARCHAR(50) UNIQUE,
                ADD COLUMN IF NOT EXISTS telegram_username VARCHAR(100),
                ADD COLUMN IF NOT EXISTS telegram_linked_at TIMESTAMP;
            """))

            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_telegram_chat_id
                ON users(telegram_chat_id);
            """))
        else:
            # SQLite syntax - check if column exists first
            result = session.execute(text("""
                PRAGMA table_info(users);
            """))
            existing_columns = [row[1] for row in result]

            if 'telegram_chat_id' not in existing_columns:
                session.execute(text("""
                    ALTER TABLE users ADD COLUMN telegram_chat_id VARCHAR(50);
                """))
                print("  - Added telegram_chat_id column")

            if 'telegram_username' not in existing_columns:
                session.execute(text("""
                    ALTER TABLE users ADD COLUMN telegram_username VARCHAR(100);
                """))
                print("  - Added telegram_username column")

            if 'telegram_linked_at' not in existing_columns:
                session.execute(text("""
                    ALTER TABLE users ADD COLUMN telegram_linked_at DATETIME;
                """))
                print("  - Added telegram_linked_at column")

            # SQLite doesn't support adding unique constraint via ALTER
            # Will rely on application-level uniqueness check

        # Create telegram_link_codes table
        print("[Migration] Creating telegram_link_codes table...")

        if is_postgresql:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS telegram_link_codes (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    code VARCHAR(6) UNIQUE NOT NULL,
                    telegram_chat_id VARCHAR(50),
                    telegram_username VARCHAR(100),
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    used_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))

            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_user_id
                ON telegram_link_codes(user_id);
            """))

            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_code
                ON telegram_link_codes(code);
            """))
        else:
            # SQLite syntax
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS telegram_link_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    code VARCHAR(6) UNIQUE NOT NULL,
                    telegram_chat_id VARCHAR(50),
                    telegram_username VARCHAR(100),
                    expires_at DATETIME NOT NULL,
                    used INTEGER DEFAULT 0,
                    used_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """))

            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_user_id
                ON telegram_link_codes(user_id);
            """))

            session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_telegram_link_codes_code
                ON telegram_link_codes(code);
            """))

        session.commit()
        print("[Migration] Migration completed successfully!")
        print("[Migration] Added Telegram linking support to database")

        return True

    except Exception as e:
        session.rollback()
        print(f"[Migration] ERROR: {e}")
        return False

    finally:
        session.close()


if __name__ == '__main__':
    print("=" * 60)
    print("Telegram Linking Database Migration")
    print("=" * 60)
    success = run_migration()
    sys.exit(0 if success else 1)
