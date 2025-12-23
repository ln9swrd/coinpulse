# -*- coding: utf-8 -*-
"""
Add user_agreements table migration script
사용자 동의 기록 테이블 생성 마이그레이션
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database.connection import get_db_session, init_database, engine
from backend.models.user_agreement_models import UserAgreement, init_db


def check_table_exists(db_engine):
    """Check if user_agreements table already exists"""
    from sqlalchemy import inspect
    inspector = inspect(db_engine)
    return 'user_agreements' in inspector.get_table_names()


def create_user_agreements_table():
    """Create user_agreements table"""
    print("=" * 60)
    print("User Agreements Table Migration")
    print("=" * 60)

    # Initialize database connection
    print("\n[0/3] Initializing database connection...")
    init_database(create_tables=False)  # Don't create all tables, just initialize connection

    # Get engine reference from connection module
    from backend.database import connection
    db_engine = connection.engine

    if db_engine is None:
        print("[ERROR] Failed to initialize database engine")
        return

    print("[OK] Database connection initialized")

    # Check if table already exists
    if check_table_exists(db_engine):
        print("\n[OK] Table 'user_agreements' already exists. Skipping creation.")
        return

    print("\n[1/3] Creating table 'user_agreements'...")
    try:
        # Create only the UserAgreement table
        UserAgreement.__table__.create(db_engine, checkfirst=True)
        print("[OK] Table 'user_agreements' created successfully")
    except Exception as e:
        print(f"[ERROR] Error creating table: {e}")
        return

    print("\n[2/3] Verifying table structure...")
    if check_table_exists(db_engine):
        print("[OK] Table verification passed")
    else:
        print("[ERROR] Table verification failed")
        return

    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("=" * 60)

    print("\nTable Schema:")
    print("  - id: Primary key (autoincrement)")
    print("  - user_id: User reference (indexed)")
    print("  - agreement_type: Type of agreement (indexed)")
    print("  - version: Agreement version (e.g., '1.0')")
    print("  - agreed: Boolean (True/False)")
    print("  - ip_address: IP for legal proof")
    print("  - user_agent: Device tracking")
    print("  - agreed_at: Timestamp (UTC)")
    print("  - updated_at: Timestamp (UTC)")


if __name__ == "__main__":
    create_user_agreements_table()
