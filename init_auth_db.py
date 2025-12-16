"""
Initialize Authentication Database
Creates authentication tables in SQLite database
"""

import sqlite3
import os
from datetime import datetime

# Configuration
DB_PATH = 'coinpulse.db'
SQL_FILE = 'backend/database/auth_schema.sql'


def print_header(title):
    """Print section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def read_sql_schema():
    """Read SQL schema file"""
    print(f"\n🔹 Reading SQL schema from: {SQL_FILE}")

    if not os.path.exists(SQL_FILE):
        print(f"❌ Error: SQL file not found: {SQL_FILE}")
        return None

    try:
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            sql_schema = f.read()

        print(f"✅ SQL schema loaded ({len(sql_schema)} characters)")
        return sql_schema

    except Exception as e:
        print(f"❌ Error reading SQL file: {e}")
        return None


def convert_postgresql_to_sqlite(sql_schema):
    """Convert PostgreSQL syntax to SQLite syntax"""
    print("\n🔹 Converting PostgreSQL syntax to SQLite...")

    # Remove PostgreSQL-specific sections
    lines = sql_schema.split('\n')
    filtered_lines = []
    skip_until_semicolon = False
    skip_function = False

    for line in lines:
        # Skip CREATE FUNCTION blocks
        if 'CREATE OR REPLACE FUNCTION' in line or 'CREATE FUNCTION' in line:
            skip_function = True
            continue

        if skip_function:
            if line.strip().startswith('$$') and 'language' in line.lower():
                skip_function = False
            continue

        # Skip CREATE TRIGGER
        if 'CREATE TRIGGER' in line:
            skip_until_semicolon = True
            continue

        # Skip COMMENT statements
        if line.strip().startswith('COMMENT ON'):
            skip_until_semicolon = True
            continue

        # Skip ALTER TABLE orders (if orders table doesn't exist yet)
        if 'ALTER TABLE orders' in line:
            skip_until_semicolon = True
            continue

        if skip_until_semicolon:
            if ';' in line:
                skip_until_semicolon = False
            continue

        # Remove CHECK constraints with regex
        if 'CONSTRAINT' in line and '~*' in line:
            continue

        # Remove other complex CHECK constraints
        if 'CONSTRAINT' in line and 'CHECK' in line and 'IN (' in line:
            continue

        filtered_lines.append(line)

    converted = '\n'.join(filtered_lines)

    # Basic conversions
    conversions = {
        'SERIAL PRIMARY KEY': 'INTEGER PRIMARY KEY AUTOINCREMENT',
        'CURRENT_TIMESTAMP': "datetime('now')",
        'VARCHAR(255)': 'TEXT',
        'VARCHAR(100)': 'TEXT',
        'VARCHAR(50)': 'TEXT',
        'VARCHAR(20)': 'TEXT',
        'TIMESTAMP': 'TEXT',
        'BOOLEAN': 'INTEGER',
        ' TRUE': ' 1',
        ' FALSE': ' 0',
        'DEFAULT TRUE': 'DEFAULT 1',
        'DEFAULT FALSE': 'DEFAULT 0'
    }

    for pg_syntax, sqlite_syntax in conversions.items():
        if pg_syntax in converted:
            count = converted.count(pg_syntax)
            converted = converted.replace(pg_syntax, sqlite_syntax)
            print(f"   ✓ Replaced {count}x: {pg_syntax} → {sqlite_syntax}")

    # Remove foreign key constraints for now (SQLite handles them differently)
    print("   ✓ Removed PostgreSQL-specific features (FUNCTION, TRIGGER, COMMENT, CHECK)")

    print("✅ Conversion complete")
    return converted


def execute_sql_statements(cursor, sql_schema):
    """Execute SQL statements one by one"""
    print("\n🔹 Executing SQL statements...")

    statements = sql_schema.split(';')
    executed = 0
    skipped = 0
    errors = 0

    for statement in statements:
        statement = statement.strip()

        # Skip empty statements
        if not statement:
            continue

        # Skip comments
        if statement.startswith('--'):
            skipped += 1
            continue

        # Skip COMMENT statements (PostgreSQL specific)
        if 'COMMENT ON' in statement.upper():
            skipped += 1
            continue

        # Skip CREATE FUNCTION/TRIGGER (PostgreSQL specific)
        if 'CREATE FUNCTION' in statement.upper() or 'CREATE TRIGGER' in statement.upper():
            skipped += 1
            continue

        try:
            cursor.execute(statement)
            executed += 1

            # Extract table name for logging
            if 'CREATE TABLE' in statement.upper():
                table_name = statement.split('CREATE TABLE IF NOT EXISTS')[1].split('(')[0].strip()
                print(f"   ✓ Created table: {table_name}")
            elif 'CREATE INDEX' in statement.upper():
                index_name = statement.split('CREATE INDEX IF NOT EXISTS')[1].split('ON')[0].strip()
                print(f"   ✓ Created index: {index_name}")

        except sqlite3.OperationalError as e:
            error_str = str(e).lower()

            # Ignore "already exists" errors
            if 'already exists' in error_str:
                skipped += 1
            else:
                print(f"   ⚠️  Warning: {e}")
                errors += 1

        except Exception as e:
            print(f"   ❌ Error: {e}")
            print(f"   Statement: {statement[:100]}...")
            errors += 1

    print(f"\n✅ Execution complete:")
    print(f"   - Executed: {executed}")
    print(f"   - Skipped: {skipped}")
    print(f"   - Errors: {errors}")

    return executed, skipped, errors


def verify_tables(cursor):
    """Verify that tables were created"""
    print("\n🔹 Verifying tables...")

    expected_tables = ['users', 'sessions', 'email_verifications', 'password_resets', 'user_api_keys']
    existing_tables = []

    for table in expected_tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        result = cursor.fetchone()

        if result:
            existing_tables.append(table)
            print(f"   ✓ Table exists: {table}")

            # Count rows
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"     Rows: {count}")
        else:
            print(f"   ❌ Table missing: {table}")

    success = len(existing_tables) == len(expected_tables)

    if success:
        print(f"\n✅ All {len(expected_tables)} tables created successfully!")
    else:
        print(f"\n⚠️  Only {len(existing_tables)}/{len(expected_tables)} tables created")

    return success


def main():
    """Main initialization function"""
    print_header("CoinPulse Authentication Database Initialization")
    print(f"Database: {DB_PATH}")
    print(f"Schema: {SQL_FILE}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if database exists
    db_exists = os.path.exists(DB_PATH)

    if db_exists:
        print(f"\n⚠️  Database already exists: {DB_PATH}")
        print("   Tables will be created if they don't exist")
    else:
        print(f"\n🔹 Creating new database: {DB_PATH}")

    # Read SQL schema
    sql_schema = read_sql_schema()

    if not sql_schema:
        print("\n❌ Failed to read SQL schema. Exiting.")
        return False

    # Convert to SQLite syntax
    sqlite_schema = convert_postgresql_to_sqlite(sql_schema)

    # Connect to database
    print(f"\n🔹 Connecting to database: {DB_PATH}")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print("✅ Connected successfully")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

    try:
        # Execute SQL statements
        executed, skipped, errors = execute_sql_statements(cursor, sqlite_schema)

        # Commit changes
        print("\n🔹 Committing changes...")
        conn.commit()
        print("✅ Changes committed")

        # Verify tables
        success = verify_tables(cursor)

        # Print summary
        print_header("Summary")

        if success and errors == 0:
            print("✅ Database initialization SUCCESSFUL")
            print("\nNext steps:")
            print("  1. Run: python test_auth_server.py")
            print("  2. Run: python test_auth_quick.py")
            print("  3. Test authentication in browser")
        else:
            print("⚠️  Database initialization COMPLETED WITH WARNINGS")
            print("\nSome tables may not have been created.")
            print("Check the errors above for details.")

        return success

    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        conn.rollback()
        print("⚠️  Changes rolled back")
        return False

    finally:
        # Close connection
        print("\n🔹 Closing database connection...")
        conn.close()
        print("✅ Connection closed")


if __name__ == '__main__':
    try:
        success = main()

        if success:
            print("\n" + "="*60)
            print("  ✅ INITIALIZATION COMPLETE")
            print("="*60)
            exit(0)
        else:
            print("\n" + "="*60)
            print("  ❌ INITIALIZATION FAILED")
            print("="*60)
            exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        exit(1)

    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
