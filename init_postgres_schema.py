"""
PostgreSQL Schema Initialization Script

Creates database and all tables for CoinPulse project.
Safe to run multiple times (CREATE IF NOT EXISTS).
"""

import sys
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))


def create_database():
    """Create coinpulse database if it doesn't exist."""
    load_dotenv()

    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'postgres')
    db_name = os.getenv('DB_NAME', 'coinpulse')

    print("\n" + "="*70)
    print("COINPULSE POSTGRESQL SCHEMA INITIALIZATION")
    print("="*70 + "\n")

    print(f"[1/3] Connecting to PostgreSQL...")
    print(f"  - Host: {db_host}:{db_port}")
    print(f"  - User: {db_user}")
    print(f"  - Target DB: {db_name}")

    try:
        # Connect to postgres database (default)
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        print("[OK] Connected to PostgreSQL\n")

        # Check if database exists
        print(f"[2/3] Checking database '{db_name}'...")
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()

        if exists:
            print(f"[OK] Database '{db_name}' already exists\n")
        else:
            print(f"[*] Creating database '{db_name}'...")
            cursor.execute(f'CREATE DATABASE {db_name}')
            print(f"[OK] Database '{db_name}' created\n")

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        print(f"\n[ERROR] PostgreSQL connection failed:")
        print(f"  - {e}")
        print("\nPlease check:")
        print("  1. PostgreSQL is running")
        print("  2. Connection settings in .env file")
        print("  3. User has CREATE DATABASE permission")
        return False


def create_tables():
    """Create all tables using SQLAlchemy models."""
    print("[3/3] Creating tables...")

    try:
        from backend.database.connection import init_database

        # Initialize database with table creation
        engine = init_database(create_tables=True)

        print("\n[SUCCESS] All tables created successfully!")

        # Show created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        print(f"\nCreated {len(table_names)} tables:")
        for i, table in enumerate(sorted(table_names), 1):
            print(f"  {i:2d}. {table}")

        return True

    except Exception as e:
        print(f"\n[ERROR] Failed to create tables:")
        print(f"  - {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_schema():
    """Verify schema by checking table structure."""
    print("\n" + "="*70)
    print("SCHEMA VERIFICATION")
    print("="*70 + "\n")

    try:
        from backend.database.connection import get_db_session
        session = get_db_session()

        # Test query
        from sqlalchemy import text
        result = session.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))

        tables = [row[0] for row in result]

        print(f"[OK] Found {len(tables)} tables in schema:")
        for table in tables:
            # Get row count
            count_result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = count_result.scalar()
            print(f"  - {table:30s} ({count:,} rows)")

        session.close()
        print("\n[OK] Schema verification complete")
        return True

    except Exception as e:
        print(f"\n[ERROR] Schema verification failed:")
        print(f"  - {e}")
        return False


def main():
    """Main execution function."""

    # Step 1: Create database
    if not create_database():
        print("\n[FAILED] Database creation failed")
        return 1

    # Step 2: Create tables
    if not create_tables():
        print("\n[FAILED] Table creation failed")
        return 1

    # Step 3: Verify schema
    if not verify_schema():
        print("\n[WARNING] Schema verification failed, but tables may be created")

    print("\n" + "="*70)
    print("INITIALIZATION COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("  1. Run: python init_order_sync.py  (sync trading history)")
    print("  2. Start servers: python simple_dual_server.py")
    print("\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
