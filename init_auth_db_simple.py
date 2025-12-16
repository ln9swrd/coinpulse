"""
Initialize Authentication Database (PostgreSQL) - Simple Version
Uses psql command to execute SQL schema directly
"""

import os
import subprocess
from datetime import datetime

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("[ERROR] psycopg2 not installed!")
    print("Install with: pip install psycopg2-binary")
    exit(1)


# Configuration
SQL_FILE = 'backend/database/auth_schema.sql'

# PostgreSQL connection settings (from environment or defaults)
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'database': os.environ.get('DB_NAME', 'coinpulse'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'postgres')
}


def print_header(title):
    """Print section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def execute_with_psql():
    """Execute SQL file using psql command"""
    print("\n[*] Executing SQL schema using psql...")

    # Build psql command
    env = os.environ.copy()
    env['PGPASSWORD'] = DB_CONFIG['password']

    cmd = [
        'psql',
        '-h', DB_CONFIG['host'],
        '-p', DB_CONFIG['port'],
        '-U', DB_CONFIG['user'],
        '-d', DB_CONFIG['database'],
        '-f', SQL_FILE,
        '-v', 'ON_ERROR_STOP=0'  # Continue on errors
    ]

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        print("\n[*] psql output:")
        print(result.stdout)

        if result.stderr:
            print("\n[*] psql errors:")
            print(result.stderr)

        return result.returncode == 0

    except FileNotFoundError:
        print("[ERROR] psql command not found!")
        print("Make sure PostgreSQL bin directory is in your PATH")
        print("Run: add_postgres_to_path.bat")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to execute psql: {e}")
        return False


def verify_tables(cursor):
    """Verify that tables were created"""
    print("\n[*] Verifying tables...")

    expected_tables = ['users', 'sessions', 'email_verifications', 'password_resets', 'user_api_keys']
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

            # Count rows
            cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                sql.Identifier(table)
            ))
            count = cursor.fetchone()[0]
            print(f"     Rows: {count}")
        else:
            print(f"   [ERROR] Table missing: {table}")

    success = len(existing_tables) == len(expected_tables)

    if success:
        print(f"\n[OK] All {len(expected_tables)} tables created successfully!")
    else:
        print(f"\n[WARNING] Only {len(existing_tables)}/{len(expected_tables)} tables created")

    return success


def main():
    """Main initialization function"""
    print_header("CoinPulse Authentication Database Initialization (PostgreSQL)")
    print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"Database: {DB_CONFIG['database']}")
    print(f"User: {DB_CONFIG['user']}")
    print(f"Schema: {SQL_FILE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check SQL file exists
    if not os.path.exists(SQL_FILE):
        print(f"\n[ERROR] SQL file not found: {SQL_FILE}")
        return False

    # Execute SQL file with psql
    success = execute_with_psql()

    if not success:
        print("\n[WARNING] psql execution completed with errors")
        print("Continuing to verify tables...")

    # Connect to PostgreSQL to verify
    print(f"\n[*] Connecting to PostgreSQL to verify...")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("[OK] Connected successfully")

        # Verify tables
        success = verify_tables(cursor)

        # Print summary
        print_header("Summary")

        if success:
            print("[OK] Database initialization SUCCESSFUL")
            print("\nNext steps:")
            print("  1. DATABASE_URL already set in .env")
            print("  2. Run: python test_auth_server.py")
            print("  3. Run: python test_auth_quick.py")
        else:
            print("[WARNING] Database initialization COMPLETED WITH WARNINGS")
            print("\nSome tables may not have been created.")

        cursor.close()
        conn.close()
        return success

    except psycopg2.OperationalError as e:
        print(f"[ERROR] Connection failed: {e}")
        return False


if __name__ == '__main__':
    try:
        success = main()

        if success:
            print("\n" + "="*60)
            print("  [OK] INITIALIZATION COMPLETE")
            print("="*60)
            exit(0)
        else:
            print("\n" + "="*60)
            print("  [ERROR] INITIALIZATION FAILED")
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
