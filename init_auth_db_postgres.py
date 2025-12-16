"""
Initialize Authentication Database (PostgreSQL)
Creates authentication tables in PostgreSQL database
"""

import os
from datetime import datetime

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("❌ psycopg2 not installed!")
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


def read_sql_schema():
    """Read SQL schema file"""
    print(f"\n[*] Reading SQL schema from: {SQL_FILE}")

    if not os.path.exists(SQL_FILE):
        print(f"[ERROR] SQL file not found: {SQL_FILE}")
        return None

    try:
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            sql_schema = f.read()

        print(f"[OK] SQL schema loaded ({len(sql_schema)} characters)")
        return sql_schema

    except Exception as e:
        print(f"[ERROR] Error reading SQL file: {e}")
        return None


def execute_sql_schema(cursor, conn, sql_schema):
    """Execute SQL schema (PostgreSQL native)"""
    print("\n[*] Executing SQL schema...")

    # Split schema into individual statements
    statements = []
    current_statement = []
    in_function = False

    for line in sql_schema.split('\n'):
        stripped = line.strip()

        # Track if we're inside a function definition
        if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
            in_function = True

        # Skip comments
        if stripped.startswith('--') or stripped.startswith('COMMENT'):
            continue

        current_statement.append(line)

        # Check for statement end
        if stripped.endswith(';'):
            # If in function, check for end of function
            if in_function and '$$' in stripped and 'language' in stripped.lower():
                in_function = False

            # Complete statement
            if not in_function:
                stmt = '\n'.join(current_statement).strip()
                if stmt and not stmt.startswith('COMMENT'):
                    statements.append(stmt)
                current_statement = []

    # Execute statements one by one with immediate commits
    executed = 0
    skipped = 0
    errors = []

    for i, statement in enumerate(statements, 1):
        # Skip COMMENT statements
        if statement.upper().startswith('COMMENT'):
            skipped += 1
            continue

        # Skip ALTER TABLE orders if orders table doesn't exist
        if 'ALTER TABLE orders' in statement:
            try:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = 'orders'
                    )
                """)
                if not cursor.fetchone()[0]:
                    print(f"   [SKIP] ALTER TABLE orders (table doesn't exist)")
                    skipped += 1
                    continue
            except:
                skipped += 1
                continue

        try:
            cursor.execute(statement)
            # Commit immediately after each successful statement
            conn.commit()
            executed += 1

            # Log table/index creation
            if 'CREATE TABLE' in statement:
                table_name = statement.split('CREATE TABLE IF NOT EXISTS')[1].split('(')[0].strip()
                print(f"   [OK] Created table: {table_name}")
            elif 'CREATE INDEX' in statement:
                index_name = statement.split('CREATE INDEX IF NOT EXISTS')[1].split('ON')[0].strip()
                print(f"   [OK] Created index: {index_name}")
            elif 'CREATE FUNCTION' in statement or 'CREATE TRIGGER' in statement:
                print(f"   [OK] Created function/trigger")

        except Exception as e:
            error_msg = str(e)
            # Rollback failed transaction
            conn.rollback()

            # Ignore "already exists" errors
            if 'already exists' not in error_msg.lower() and 'already exists' not in error_msg:
                print(f"   [ERROR] Error in statement {i}: {error_msg}")
                errors.append((i, statement[:100], error_msg))
            else:
                skipped += 1

    print(f"\n   Executed: {executed}, Skipped: {skipped}, Errors: {len(errors)}")

    if errors:
        print("\n[WARNING] Errors encountered:")
        for i, stmt, err in errors[:5]:  # Show first 5 errors
            print(f"   Statement {i}: {err}")
        return False

    print("[OK] Schema executed successfully")
    return True


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

    # Read SQL schema
    sql_schema = read_sql_schema()

    if not sql_schema:
        print("\n[ERROR] Failed to read SQL schema. Exiting.")
        return False

    # Connect to PostgreSQL
    print(f"\n[*] Connecting to PostgreSQL...")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("[OK] Connected successfully")

    except psycopg2.OperationalError as e:
        print(f"[ERROR] Connection failed: {e}")
        print("\nPossible solutions:")
        print("  1. Check PostgreSQL is running: sudo systemctl status postgresql")
        print("  2. Check connection settings in .env file")
        print("  3. Create database: createdb coinpulse")
        print("  4. Check user permissions")
        return False

    try:
        # Execute SQL schema with connection for commits
        success = execute_sql_schema(cursor, conn, sql_schema)

        if not success:
            conn.rollback()
            print("[WARNING] Changes rolled back")
            return False

        # Final commit
        print("\n[*] Final commit...")
        conn.commit()
        print("[OK] All changes committed")

        # Verify tables
        success = verify_tables(cursor)

        # Print summary
        print_header("Summary")

        if success:
            print("[OK] Database initialization SUCCESSFUL")
            print("\nNext steps:")
            print("  1. Set DATABASE_URL in .env:")
            print(f"     DATABASE_URL=postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
            print("  2. Run: python test_auth_server.py")
            print("  3. Run: python test_auth_quick.py")
        else:
            print("[WARNING] Database initialization COMPLETED WITH WARNINGS")
            print("\nSome tables may not have been created.")
            print("Check the errors above for details.")

        return success

    except Exception as e:
        print(f"\n[ERROR] Error during execution: {e}")
        conn.rollback()
        print("[WARNING] Changes rolled back")
        return False

    finally:
        # Close connection
        print("\n[*] Closing database connection...")
        cursor.close()
        conn.close()
        print("[OK] Connection closed")


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
