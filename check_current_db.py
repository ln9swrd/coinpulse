"""Check Current Database Status"""
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Current Database Status Check")
print("=" * 60)
print()

# Check DB_TYPE from .env
db_type = os.getenv('DB_TYPE', 'sqlite')
print(f"Current DB_TYPE: {db_type}")
print()

if db_type == 'sqlite':
    print("[SQLite Database]")
    db_path = os.getenv('DB_SQLITE_PATH', 'data/coinpulse.db')
    print(f"Path: {db_path}")

    if os.path.exists(db_path):
        print("Status: EXISTS")

        # Get file size
        size = os.path.getsize(db_path)
        print(f"Size: {size:,} bytes ({size/1024:.2f} KB)")

        # Connect and check tables
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()

            # Get table list
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = cur.fetchall()

            print(f"\nTables: {len(tables)}")
            for table in tables:
                table_name = table[0]
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                print(f"  - {table_name}: {count:,} records")

            # Check orders specifically
            print("\n[Orders Detail]")
            try:
                cur.execute("SELECT market, COUNT(*) as cnt FROM orders GROUP BY market ORDER BY cnt DESC LIMIT 10")
                markets = cur.fetchall()
                for market, cnt in markets:
                    print(f"  {market}: {cnt:,} orders")
            except:
                print("  No orders table or empty")

            conn.close()

            print("\n[OK] SQLite database is working properly!")

        except Exception as e:
            print(f"\n[ERROR] Database error: {e}")
    else:
        print("Status: NOT FOUND")
        print("\nTo initialize:")
        print("  python init_database.py")

else:
    print("[PostgreSQL Database]")
    print("Configuration:")
    print(f"  Host: {os.getenv('DB_HOST')}")
    print(f"  Port: {os.getenv('DB_PORT')}")
    print(f"  User: {os.getenv('DB_USER')}")
    print(f"  Database: {os.getenv('DB_NAME')}")
    print("\nTo check PostgreSQL, run:")
    print("  coinpulse_manager_v2.bat -> [8] -> [1]")

print("\n" + "=" * 60)
