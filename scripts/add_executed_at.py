#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Add executed_at column to surge_alerts table"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import init_database
from sqlalchemy import text

print("[Migration] Adding executed_at column to surge_alerts...")

# Initialize database to get engine
engine = init_database(create_tables=False)

try:
    with engine.connect() as conn:
        with conn.begin():
            query = text("ALTER TABLE surge_alerts ADD COLUMN executed_at TIMESTAMP")
            conn.execute(query)
            print("  SUCCESS: Added 'executed_at' (TIMESTAMP)")
except Exception as e:
    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
        print("  SKIP: 'executed_at' already exists")
    else:
        print(f"  ERROR: {e}")

print("[Migration] DONE!")
