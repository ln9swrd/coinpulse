"""
Create coin_price_history table for shared coin price data.

This table stores BTC/ETH/XRP daily prices that are shared across all users,
eliminating redundant API calls and improving backfill performance.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.connection import get_db_session
from sqlalchemy import text


def check_table_exists(db, table_name):
    """Check if table already exists."""
    query = text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = :table_name
        );
    """)
    result = db.execute(query, {'table_name': table_name})
    return result.scalar()


def create_coin_price_history_table():
    """Create coin_price_history table."""
    try:
        db = get_db_session()

        # Check if table already exists
        if check_table_exists(db, 'coin_price_history'):
            print("✓ coin_price_history table already exists")
            db.close()
            return True

        print("[Migration] Creating coin_price_history table...")

        # Create table
        create_table_sql = text("""
            CREATE TABLE coin_price_history (
                id SERIAL PRIMARY KEY,
                market VARCHAR(20) NOT NULL,
                date DATE NOT NULL,
                open_price NUMERIC(20, 2),
                high_price NUMERIC(20, 2),
                low_price NUMERIC(20, 2),
                close_price NUMERIC(20, 2) NOT NULL,
                volume NUMERIC(20, 8),
                created_at TIMESTAMP DEFAULT NOW(),
                CONSTRAINT unique_market_date UNIQUE(market, date)
            );
        """)

        db.execute(create_table_sql)

        # Create indexes
        create_index_sql = text("""
            CREATE INDEX idx_coin_price_date ON coin_price_history(market, date);
        """)

        db.execute(create_index_sql)

        db.commit()

        print("✓ coin_price_history table created successfully")
        print("✓ Indexes created: idx_coin_price_date")

        db.close()

        return True

    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False


def main():
    """Main function."""
    print("=" * 70)
    print("  Create coin_price_history Table")
    print("=" * 70)
    print()

    success = create_coin_price_history_table()

    print()
    if success:
        print("✓ Migration completed successfully")
        print()
        print("Next steps:")
        print("1. Run: python scripts/populate_coin_price_history.py")
        print("2. This will populate historical BTC/ETH/XRP prices")
    else:
        print("❌ Migration failed")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
