#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reset plan_configs table
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.database.connection import init_database
from backend.models.plan_config import PlanConfig
from sqlalchemy import text

def reset_table():
    """Drop and recreate plan_configs table"""
    print("Initializing database...")
    engine = init_database(create_tables=False)

    print("Resetting plan_configs table...")

    try:
        # Drop table
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS plan_configs CASCADE"))
            conn.commit()
            print("Table dropped")

        # Recreate table
        PlanConfig.__table__.create(engine)
        print("Table recreated with latest schema")

        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if reset_table():
        print("\nSuccess! Now run: python scripts/init_plan_configs.py")
        sys.exit(0)
    else:
        print("\nFailed")
        sys.exit(1)
