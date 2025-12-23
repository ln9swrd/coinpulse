"""
Add tracking columns to surge_alerts table

Adds columns needed for Win/Lose tracking and auto-trading status:
- entry_price: Price when signal was generated
- stop_loss_price: Stop loss price (-5%)
- auto_traded: Whether this signal was actually traded
- status: Current status (pending/win/lose/neutral/backtest)
- profit_loss: Actual profit/loss in KRW
- profit_loss_percent: Profit/loss percentage
- closed_at: When the position was closed
"""
import sys
import os

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.database.connection import get_db_session

def add_surge_tracking_columns():
    """Add tracking columns to surge_alerts table"""

    with get_db_session() as session:
        print("=== Adding tracking columns to surge_alerts ===\n")

        # Check if columns already exist
        check_query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'surge_alerts'
              AND column_name IN ('entry_price', 'stop_loss_price', 'auto_traded',
                                  'status', 'profit_loss', 'profit_loss_percent', 'closed_at')
        """)

        existing_columns = {row[0] for row in session.execute(check_query)}
        print(f"Existing columns: {existing_columns}\n")

        # Add missing columns
        columns_to_add = {
            'entry_price': 'BIGINT',
            'stop_loss_price': 'BIGINT',
            'auto_traded': 'BOOLEAN DEFAULT FALSE',
            'status': "VARCHAR(20) DEFAULT 'pending'",
            'profit_loss': 'BIGINT DEFAULT 0',
            'profit_loss_percent': 'DOUBLE PRECISION DEFAULT 0.0',
            'closed_at': 'TIMESTAMP'
        }

        for column, datatype in columns_to_add.items():
            if column not in existing_columns:
                try:
                    alter_query = text(f"""
                        ALTER TABLE surge_alerts
                        ADD COLUMN {column} {datatype}
                    """)
                    session.execute(alter_query)
                    session.commit()
                    print(f"[OK] Added column: {column} ({datatype})")
                except Exception as e:
                    print(f"[WARN] Could not add {column}: {e}")
                    session.rollback()
            else:
                print(f"[SKIP] Column already exists: {column}")

        # Update existing records with default values
        print("\n=== Updating existing records ===\n")

        # Set entry_price = current_price for existing records
        update_entry = text("""
            UPDATE surge_alerts
            SET entry_price = current_price
            WHERE entry_price IS NULL
        """)
        result = session.execute(update_entry)
        session.commit()
        print(f"[OK] Updated entry_price for {result.rowcount} records")

        # Set stop_loss_price = current_price * 0.95
        update_stop_loss = text("""
            UPDATE surge_alerts
            SET stop_loss_price = CAST(current_price * 0.95 AS BIGINT)
            WHERE stop_loss_price IS NULL
        """)
        result = session.execute(update_stop_loss)
        session.commit()
        print(f"[OK] Updated stop_loss_price for {result.rowcount} records")

        # Set auto_traded = false for existing records
        update_auto_traded = text("""
            UPDATE surge_alerts
            SET auto_traded = FALSE
            WHERE auto_traded IS NULL
        """)
        result = session.execute(update_auto_traded)
        session.commit()
        print(f"[OK] Updated auto_traded for {result.rowcount} records")

        # Set status = 'backtest' for old records (before 2024-12-01)
        update_status = text("""
            UPDATE surge_alerts
            SET status = 'backtest'
            WHERE status IS NULL
              AND sent_at < '2024-12-01'
        """)
        result = session.execute(update_status)
        session.commit()
        print(f"[OK] Updated status to 'backtest' for {result.rowcount} old records")

        # Set status = 'pending' for recent records
        update_pending = text("""
            UPDATE surge_alerts
            SET status = 'pending'
            WHERE status IS NULL
        """)
        result = session.execute(update_pending)
        session.commit()
        print(f"[OK] Updated status to 'pending' for {result.rowcount} recent records")

        print("\n=== Migration complete ===")

        # Show final column list
        final_query = text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'surge_alerts'
            ORDER BY ordinal_position
        """)

        print("\n=== Final surge_alerts schema ===\n")
        for row in session.execute(final_query):
            print(f"  {row.column_name}: {row.data_type}")

if __name__ == "__main__":
    add_surge_tracking_columns()
