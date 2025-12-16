"""
PostgreSQL Database Check Script
Checks if coinpulse database is properly set up
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_postgresql():
    """Check PostgreSQL database status"""

    print("=" * 60)
    print("PostgreSQL Database Check")
    print("=" * 60)
    print()

    # Get connection info from .env
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_user = os.getenv('DB_USER', 'coinpulse')
    db_password = os.getenv('DB_PASSWORD', 'coinpulse2024')
    db_name = os.getenv('DB_NAME', 'coinpulse')

    print(f"Connection Info:")
    print(f"  Host: {db_host}")
    print(f"  Port: {db_port}")
    print(f"  User: {db_user}")
    print(f"  Database: {db_name}")
    print()

    try:
        import psycopg2
        from psycopg2 import sql

        # Try to connect to coinpulse database
        print("[1/4] Testing connection to coinpulse database...")
        try:
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                database=db_name
            )
            print("  [OK] SUCCESS: Connected to coinpulse database")

            # Check tables
            print()
            print("[2/4] Checking tables...")
            cur = conn.cursor()
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cur.fetchall()

            if tables:
                print(f"  [OK] Found {len(tables)} tables:")
                for table in tables:
                    print(f"    - {table[0]}")
            else:
                print("  [WARNING] No tables found")

            # Check data in orders table
            print()
            print("[3/4] Checking data in orders table...")
            try:
                cur.execute("SELECT COUNT(*) FROM orders")
                count = cur.fetchone()[0]
                print(f"  [OK] Orders table has {count} records")

                if count > 0:
                    cur.execute("SELECT market, COUNT(*) as cnt FROM orders GROUP BY market ORDER BY cnt DESC LIMIT 5")
                    markets = cur.fetchall()
                    print(f"  Top markets:")
                    for market, cnt in markets:
                        print(f"    - {market}: {cnt} orders")
            except Exception as e:
                print(f"  [WARNING] Cannot read orders table: {e}")

            # Check database size
            print()
            print("[4/4] Checking database size...")
            cur.execute("""
                SELECT pg_size_pretty(pg_database_size(%s))
            """, (db_name,))
            size = cur.fetchone()[0]
            print(f"  Database size: {size}")

            cur.close()
            conn.close()

            print()
            print("=" * 60)
            print("[OK] PostgreSQL database is properly configured!")
            print("=" * 60)
            return True

        except psycopg2.OperationalError as e:
            if "does not exist" in str(e):
                print("  [ERROR] Database 'coinpulse' does not exist")
                print()
                print("To create the database, run:")
                print("  coinpulse_manager_v2.bat")
                print("  -> [8] Database Management Menu")
                print("  -> [7] Create PostgreSQL Database")
            else:
                print(f"  [ERROR] Connection failed")
                print(f"  Details: {str(e)}")
            return False

    except ImportError:
        print("[ERROR] psycopg2 module not installed")
        print()
        print("To install:")
        print("  pip install psycopg2-binary")
        return False

    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    check_postgresql()
