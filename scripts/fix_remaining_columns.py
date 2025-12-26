#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix remaining missing columns - each in separate transaction"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import init_database
from sqlalchemy import text

# Remaining columns that need to be added
REMAINING_COLUMNS = [
    ("order_id", "VARCHAR(50)"),
    ("exit_price", "BIGINT"),
]

print("[Migration] Adding remaining columns to surge_alerts...")
print("[Migration] Using separate transactions to avoid state errors")

# Initialize database to get engine
engine = init_database(create_tables=False)

for column_name, column_type in REMAINING_COLUMNS:
    # Each column gets its own connection/transaction
    try:
        with engine.connect() as conn:
            with conn.begin():
                query = text(f"ALTER TABLE surge_alerts ADD COLUMN {column_name} {column_type}")
                conn.execute(query)
                print(f"  SUCCESS: Added '{column_name}' ({column_type})")
    except Exception as e:
        if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
            print(f"  SKIP: '{column_name}' already exists")
        else:
            print(f"  ERROR adding '{column_name}': {e}")

print("[Migration] DONE! All remaining columns processed.")
