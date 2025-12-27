#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fix ALL missing columns in surge_alerts table at once"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_db_session
from sqlalchemy import text

# All columns that might be missing based on the model
MISSING_COLUMNS = [
    ("trade_amount", "BIGINT"),
    ("trade_quantity", "FLOAT"),
    ("order_id", "VARCHAR(50)"),
    ("exit_price", "BIGINT"),
]

print("[Migration] Adding ALL potentially missing columns to surge_alerts...")

with get_db_session() as session:
    for column_name, column_type in MISSING_COLUMNS:
        try:
            query = text(f"ALTER TABLE surge_alerts ADD COLUMN {column_name} {column_type}")
            session.execute(query)
            print(f"  SUCCESS: Added '{column_name}' ({column_type})")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                print(f"  SKIP: '{column_name}' already exists")
            else:
                print(f"  ERROR: {column_name} - {e}")

    session.commit()
    print("[Migration] DONE! All columns checked/added.")
