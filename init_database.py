"""
Database Initialization Script

Creates all database tables and performs initial setup.

Usage:
    python init_database.py [--drop]

Options:
    --drop    Drop existing tables before creating (DANGEROUS!)
"""

import sys
import os
import json
from backend.database import init_database, Base, engine

def load_config():
    """Load trading server configuration."""
    try:
        with open('trading_server_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("[Warning] trading_server_config.json not found, using defaults")
        return {}

def main():
    """Initialize database tables."""
    print("=" * 60)
    print("CoinPulse Database Initialization")
    print("=" * 60)

    # Check for --drop flag
    drop_tables = '--drop' in sys.argv

    # Load configuration
    config = load_config()

    # Initialize database connection first
    print("\n[Database] Initializing database connection...")
    db_engine = init_database(create_tables=False)

    if drop_tables:
        print("\n[WARNING] --drop flag detected!")
        print("This will DELETE ALL EXISTING DATA!")
        response = input("Are you sure? Type 'YES' to confirm: ")
        if response != 'YES':
            print("Aborted.")
            return

        print("\n[Database] Dropping all existing tables...")
        Base.metadata.drop_all(bind=db_engine)
        print("[Database] All tables dropped")

    # Create tables
    print("\n[Database] Creating tables...")
    Base.metadata.create_all(bind=db_engine)
    print("[Database] Tables created successfully")

    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(db_engine)
    tables = inspector.get_table_names()

    print(f"\n[Database] Created {len(tables)} tables:")
    for table in sorted(tables):
        print(f"  [OK] {table}")

    print("\n" + "=" * 60)
    print("Database initialization complete!")
    print("=" * 60)

    # Print connection info
    db_url = os.getenv('DATABASE_URL', 'sqlite:///data/coinpulse.db')
    if db_url.startswith('sqlite'):
        print(f"\nDatabase location: data/coinpulse.db")
    else:
        print(f"\nDatabase: PostgreSQL")

    print("\nNext steps:")
    print("1. Run OrderSyncService to import Upbit data")
    print("2. Start the API servers")
    print("3. Access the trading chart frontend")


if __name__ == '__main__':
    main()
