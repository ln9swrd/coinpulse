"""
Initialize Authentication Database (PostgreSQL) - Migration Version
Integrates with existing users table and creates auth tables
"""

import os
from datetime import datetime

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("[ERROR] psycopg2 not installed!")
    print("Install with: pip install psycopg2-binary")
    exit(1)


DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'database': os.environ.get('DB_NAME', 'coinpulse'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'postgres')
}


def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def migrate_users_table(cursor, conn):
    """Add authentication columns to existing users table"""
    print("\n[*] Migrating users table...")

    columns_to_add = [
        ("password_hash", "VARCHAR(255)"),
        ("is_verified", "BOOLEAN DEFAULT FALSE"),
        ("email_verified_at", "TIMESTAMP"),
        ("last_login_at", "TIMESTAMP"),
        ("full_name", "VARCHAR(255)"),
        ("phone", "VARCHAR(50)")
    ]

    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS {col_name} {col_type}
            """)
            conn.commit()
            print(f"   [OK] Column '{col_name}' added")
        except Exception as e:
            print(f"   [WARNING] Column '{col_name}': {e}")
            conn.rollback()

    return True


def create_auth_tables(cursor, conn):
    """Create authentication-related tables"""
    print("\n[*] Creating authentication tables...")

    # Table 1: Sessions (using user_id to match existing schema)
    print("   [*] Creating table: sessions")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            token_jti VARCHAR(255) UNIQUE NOT NULL,
            token_type VARCHAR(20) DEFAULT 'access',
            expires_at TIMESTAMP NOT NULL,
            revoked BOOLEAN DEFAULT FALSE,
            revoked_at TIMESTAMP,
            ip_address VARCHAR(50),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("   [OK] Table 'sessions' created")

    # Table 2: Email Verifications
    print("   [*] Creating table: email_verifications")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_verifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            token VARCHAR(255) UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            verified BOOLEAN DEFAULT FALSE,
            verified_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("   [OK] Table 'email_verifications' created")

    # Table 3: Password Resets
    print("   [*] Creating table: password_resets")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            token VARCHAR(255) UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT FALSE,
            used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("   [OK] Table 'password_resets' created")

    # Table 4: User API Keys (rename to avoid conflict with existing api_key column)
    print("   [*] Creating table: user_api_keys")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_api_keys (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            key_name VARCHAR(100) NOT NULL,
            api_key VARCHAR(255) UNIQUE NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            last_used_at TIMESTAMP,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_user_key_name UNIQUE (user_id, key_name)
        )
    """)
    conn.commit()
    print("   [OK] Table 'user_api_keys' created")

    return True


def create_indexes(cursor, conn):
    """Create indexes for performance"""
    print("\n[*] Creating indexes...")

    indexes = [
        ("idx_users_email_auth", "users(email)"),
        ("idx_users_username_auth", "users(username)"),
        ("idx_sessions_user_id", "sessions(user_id)"),
        ("idx_sessions_token_jti", "sessions(token_jti)"),
        ("idx_sessions_expires_at", "sessions(expires_at)"),
        ("idx_email_verifications_token", "email_verifications(token)"),
        ("idx_password_resets_token", "password_resets(token)"),
        ("idx_user_api_keys_api_key", "user_api_keys(api_key)")
    ]

    for idx_name, idx_on in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_on}")
            conn.commit()
            print(f"   [OK] Index '{idx_name}' created")
        except Exception as e:
            print(f"   [SKIP] Index '{idx_name}': already exists")
            conn.rollback()

    return True


def create_triggers(cursor, conn):
    """Create triggers for auto-update"""
    print("\n[*] Creating triggers...")

    try:
        # Create function
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        """)
        conn.commit()
        print("   [OK] Function 'update_updated_at_column' created")

        # Create trigger
        cursor.execute("""
            DROP TRIGGER IF EXISTS update_users_updated_at ON users
        """)
        cursor.execute("""
            CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """)
        conn.commit()
        print("   [OK] Trigger 'update_users_updated_at' created")

        return True

    except Exception as e:
        print(f"   [WARNING] Trigger creation failed: {e}")
        conn.rollback()
        return False


def verify_schema(cursor):
    """Verify that all required tables and columns exist"""
    print("\n[*] Verifying schema...")

    # Check users table columns
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'users'
    """)
    user_columns = [row[0] for row in cursor.fetchall()]

    required_columns = ['user_id', 'username', 'email', 'password_hash', 'is_verified']
    missing_columns = [col for col in required_columns if col not in user_columns]

    if missing_columns:
        print(f"   [WARNING] Users table missing columns: {missing_columns}")
    else:
        print(f"   [OK] Users table has all required columns")

    # Check auth tables
    expected_tables = ['sessions', 'email_verifications', 'password_resets', 'user_api_keys']
    existing_tables = []

    for table in expected_tables:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            )
        """, (table,))

        exists = cursor.fetchone()[0]

        if exists:
            existing_tables.append(table)
            print(f"   [OK] Table exists: {table}")

            cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                sql.Identifier(table)
            ))
            count = cursor.fetchone()[0]
            print(f"     Rows: {count}")
        else:
            print(f"   [ERROR] Table missing: {table}")

    success = len(existing_tables) == len(expected_tables) and not missing_columns

    if success:
        print(f"\n[OK] All authentication tables and columns created successfully!")
    else:
        print(f"\n[WARNING] Schema verification completed with warnings")

    return success


def main():
    """Main migration function"""
    print_header("CoinPulse Authentication Database Migration (PostgreSQL)")
    print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"User: {DB_CONFIG['user']}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Connect to PostgreSQL
    print(f"\n[*] Connecting to PostgreSQL...")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("[OK] Connected successfully")

    except psycopg2.OperationalError as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

    try:
        # Migrate existing users table
        migrate_users_table(cursor, conn)

        # Create authentication tables
        create_auth_tables(cursor, conn)

        # Create indexes
        create_indexes(cursor, conn)

        # Create triggers
        create_triggers(cursor, conn)

        # Verify schema
        success = verify_schema(cursor)

        # Print summary
        print_header("Summary")

        if success:
            print("[OK] Database migration SUCCESSFUL")
            print("\nNext steps:")
            print("  1. DATABASE_URL already set in .env")
            print("  2. Update auth_routes.py to use 'user_id' instead of 'id'")
            print("  3. Run: python test_auth_server.py")
            print("  4. Run: python test_auth_quick.py")
        else:
            print("[WARNING] Database migration COMPLETED WITH WARNINGS")

        return success

    except Exception as e:
        print(f"\n[ERROR] Error during migration: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()
        print("\n[*] Connection closed")


if __name__ == '__main__':
    try:
        success = main()

        if success:
            print("\n" + "="*60)
            print("  [OK] MIGRATION COMPLETE")
            print("="*60)
            exit(0)
        else:
            print("\n" + "="*60)
            print("  [WARNING] MIGRATION COMPLETED WITH WARNINGS")
            print("="*60)
            exit(1)

    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user")
        exit(1)

    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
