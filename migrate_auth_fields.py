"""
Database Migration: Add Authentication Fields to User Table

Adds password_hash and email_verified columns for web authentication.
"""

import sys
import os
from sqlalchemy import text

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from backend.database import get_db_session, init_database


def migrate_auth_fields():
    """Add password_hash and email_verified columns to users table."""

    print("=" * 70)
    print("MIGRATING USERS TABLE - ADDING AUTHENTICATION FIELDS")
    print("=" * 70)

    # Initialize database connection
    init_database(create_tables=False)

    session = get_db_session()

    try:
        # Migration SQL for PostgreSQL
        migrations = [
            # 1. Add password_hash column
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='users'
                    AND column_name='password_hash'
                ) THEN
                    ALTER TABLE users
                    ADD COLUMN password_hash VARCHAR(255);
                    COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password';
                    RAISE NOTICE 'Added password_hash column';
                ELSE
                    RAISE NOTICE 'Column password_hash already exists';
                END IF;
            END $$;
            """,

            # 2. Add email_verified column
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='users'
                    AND column_name='email_verified'
                ) THEN
                    ALTER TABLE users
                    ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
                    COMMENT ON COLUMN users.email_verified IS 'Email verification status';
                    RAISE NOTICE 'Added email_verified column';
                ELSE
                    RAISE NOTICE 'Column email_verified already exists';
                END IF;
            END $$;
            """,

            # 3. Make email NOT NULL and add index (if not exists)
            """
            DO $$
            BEGIN
                -- Make email NOT NULL if it isn't already
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='users'
                    AND column_name='email'
                    AND is_nullable='YES'
                ) THEN
                    ALTER TABLE users
                    ALTER COLUMN email SET NOT NULL;
                    RAISE NOTICE 'Set email to NOT NULL';
                END IF;

                -- Add email index if it doesn't exist
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes
                    WHERE tablename='users'
                    AND indexname='idx_users_email'
                ) THEN
                    CREATE INDEX idx_users_email ON users(email);
                    RAISE NOTICE 'Created email index';
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
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            AND column_name IN ('password_hash', 'email_verified', 'email')
            ORDER BY column_name
        """))

        columns = result.fetchall()
        if len(columns) >= 2:
            print("[OK] Authentication columns verified:")
            for col in columns:
                print(f"     - {col[0]}: {col[1]} (nullable: {col[3]}, default: {col[2]})")
        else:
            print(f"[WARNING] Expected 3 columns, found {len(columns)}")

        print("\n" + "=" * 70)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Test signup: POST /api/auth/signup")
        print("  2. Test login: POST /api/auth/login")
        print("  3. Install required packages:")
        print("     pip install pyjwt bcrypt")
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
    success = migrate_auth_fields()
    sys.exit(0 if success else 1)
