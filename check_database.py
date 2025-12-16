"""
Check PostgreSQL Database Schema
"""

import os
import psycopg2
from psycopg2 import sql

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'database': os.environ.get('DB_NAME', 'coinpulse'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'postgres')
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("\n[*] Checking existing tables...")

    # List all tables
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)

    tables = cursor.fetchall()
    print(f"\nFound {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")

    # Check users table schema
    if any(t[0] == 'users' for t in tables):
        print("\n[*] Checking 'users' table schema...")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)

        columns = cursor.fetchall()
        print("\nColumns in 'users' table:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (NULL: {col[2]})")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"[ERROR] {e}")
