# -*- coding: utf-8 -*-
"""
Add surge_candidates_cache table migration script
급등 후보 캐시 테이블 생성 마이그레이션
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database.connection import get_db_session, init_database
from backend.models.surge_candidates_cache_models import SurgeCandidatesCache
from sqlalchemy import inspect


def check_table_exists(db_engine):
    """Check if surge_candidates_cache table already exists"""
    inspector = inspect(db_engine)
    return 'surge_candidates_cache' in inspector.get_table_names()


def create_surge_candidates_cache_table():
    """Create surge_candidates_cache table"""
    print("=" * 60)
    print("Surge Candidates Cache Table Migration")
    print("=" * 60)

    # Initialize database connection
    print("\n[0/3] Initializing database connection...")
    init_database(create_tables=False)

    # Get engine reference
    from backend.database import connection
    db_engine = connection.engine

    if db_engine is None:
        print("[ERROR] Failed to initialize database engine")
        return

    print("[OK] Database connection initialized")

    # Check if table already exists
    if check_table_exists(db_engine):
        print("\n[OK] Table 'surge_candidates_cache' already exists. Skipping creation.")
        return

    print("\n[1/3] Creating table 'surge_candidates_cache'...")
    try:
        # Create only the SurgeCandidatesCache table
        SurgeCandidatesCache.__table__.create(db_engine, checkfirst=True)
        print("[OK] Table 'surge_candidates_cache' created successfully")
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
    print("  - market: Market code (UNIQUE, e.g., 'KRW-BTC')")
    print("  - coin: Coin symbol (e.g., 'BTC')")
    print("  - score: Confidence score (0-100)")
    print("  - current_price: Price in KRW")
    print("  - recommendation: 'strong_buy', 'buy', 'hold', 'pass'")
    print("  - signals: JSON field (detailed signals)")
    print("  - analysis_result: JSON field (full analysis)")
    print("  - analyzed_at: Analysis timestamp (UTC)")
    print("  - updated_at: Last update timestamp (UTC)")

    print("\nPurpose:")
    print("  - Stores surge_alert_scheduler analysis results")
    print("  - Updated every 5 minutes by background worker")
    print("  - Read by /api/surge-candidates (0 API calls)")
    print("  - Cache-first architecture for rate limit optimization")


if __name__ == "__main__":
    create_surge_candidates_cache_table()
