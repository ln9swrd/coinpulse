#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Initialize upbit_api_keys table in database

Creates the upbit_api_keys table with the correct schema for encrypted API key storage.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.connection import get_db_session, engine
from backend.models.user_api_key import UpbitAPIKey, Base
from sqlalchemy import inspect

def init_upbit_api_keys_table():
    """
    Initialize upbit_api_keys table
    """
    print("=" * 60)
    print("User API Keys Table Initialization")
    print("=" * 60)

    # Check if table exists
    inspector = inspect(engine)
    table_exists = 'upbit_api_keys' in inspector.get_table_names()

    if table_exists:
        print("✅ Table 'upbit_api_keys' already exists")

        # Show current schema
        columns = inspector.get_columns('upbit_api_keys')
        print("\nCurrent columns:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
    else:
        print("❌ Table 'upbit_api_keys' does not exist")
        print("Creating table...")

        # Create table
        Base.metadata.create_all(engine, tables=[UpbitAPIKey.__table__])

        print("✅ Table 'upbit_api_keys' created successfully")

        # Show new schema
        inspector = inspect(engine)
        columns = inspector.get_columns('upbit_api_keys')
        print("\nCreated columns:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")

    print("\n" + "=" * 60)
    print("Initialization Complete")
    print("=" * 60)

if __name__ == '__main__':
    init_upbit_api_keys_table()
