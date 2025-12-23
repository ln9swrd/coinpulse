"""
Add surge trading columns to swing_positions table

Adds columns needed for surge prediction auto-trading:
- surge_alert_id: FK to surge_alerts
- target_price: Take-profit price
- stop_loss_price: Stop-loss price
- position_type: 'swing' or 'surge'
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.database.connection import get_db_session


def add_surge_position_columns():
    """Add surge trading columns to swing_positions table"""

    with get_db_session() as session:
        print("=== Adding surge trading columns to swing_positions ===\n")

        # Check existing columns
        check_query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'swing_positions'
              AND column_name IN ('surge_alert_id', 'target_price', 'stop_loss_price', 'position_type')
        """)

        existing_columns = {row[0] for row in session.execute(check_query)}
        print(f"Existing columns: {existing_columns}\n")

        # Add missing columns
        columns_to_add = {
            'surge_alert_id': 'INTEGER',  # FK to surge_alerts
            'target_price': 'NUMERIC(20, 8)',  # Take-profit price
            'stop_loss_price': 'NUMERIC(20, 8)',  # Stop-loss price
            'position_type': "VARCHAR(20) DEFAULT 'swing'"  # 'swing' or 'surge'
        }

        for column, datatype in columns_to_add.items():
            if column not in existing_columns:
                try:
                    alter_query = text(f"""
                        ALTER TABLE swing_positions
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

        # Add foreign key constraint (if not exists)
        print("\n=== Adding foreign key constraint ===\n")
        try:
            fk_query = text("""
                ALTER TABLE swing_positions
                ADD CONSTRAINT fk_swing_positions_surge_alert
                FOREIGN KEY (surge_alert_id) REFERENCES surge_alerts(id)
                ON DELETE SET NULL
            """)
            session.execute(fk_query)
            session.commit()
            print("[OK] Added FK constraint: fk_swing_positions_surge_alert")
        except Exception as e:
            if 'already exists' in str(e).lower():
                print("[SKIP] FK constraint already exists")
                session.rollback()
            else:
                print(f"[WARN] Could not add FK constraint: {e}")
                session.rollback()

        # Update existing records to position_type = 'swing'
        print("\n=== Updating existing records ===\n")
        try:
            update_query = text("""
                UPDATE swing_positions
                SET position_type = 'swing'
                WHERE position_type IS NULL
            """)
            result = session.execute(update_query)
            session.commit()
            print(f"[OK] Updated position_type for {result.rowcount} records")
        except Exception as e:
            print(f"[WARN] Could not update records: {e}")
            session.rollback()

        print("\n=== Migration complete ===")

        # Show final schema
        final_query = text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'swing_positions'
            ORDER BY ordinal_position
        """)

        print("\n=== Final swing_positions schema ===\n")
        for row in session.execute(final_query):
            print(f"  {row.column_name}: {row.data_type}")


if __name__ == "__main__":
    add_surge_position_columns()
