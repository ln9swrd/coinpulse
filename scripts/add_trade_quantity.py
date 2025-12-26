#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Quick fix: Add trade_quantity column"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_db_session
from sqlalchemy import text

try:
    with get_db_session() as session:
        # PostgreSQL에서는 IF NOT EXISTS를 지원하지 않으므로 try-except 사용
        session.execute(text("ALTER TABLE surge_alerts ADD COLUMN trade_quantity FLOAT"))
        session.commit()
        print("SUCCESS: trade_quantity column added!")
except Exception as e:
    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
        print("Column already exists - OK")
    else:
        print(f"ERROR: {e}")
        sys.exit(1)
