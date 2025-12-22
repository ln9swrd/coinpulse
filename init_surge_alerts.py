# -*- coding: utf-8 -*-
"""
Initialize Surge Alert System Database Tables

Creates:
- surge_alerts table
- user_favorite_coins table
"""

import os
import sys
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database.connection import init_database, Base, engine as db_engine
from backend.models.surge_alert_models import SurgeAlert, UserFavoriteCoin

def init_surge_alert_tables():
    """Initialize surge alert system tables"""
    print("=" * 60)
    print("Surge Alert System - Database Initialization")
    print("=" * 60)

    try:
        # Initialize database
        engine = init_database(create_tables=False)
        if engine is None:
            engine = db_engine
        inspector = inspect(engine)

        print(f"\nDatabase: {engine.url}")

        # Check existing tables
        existing_tables = inspector.get_table_names()
        print(f"\nExisting tables: {len(existing_tables)}")
        for table in existing_tables:
            print(f"  - {table}")

        # Create tables
        print("\n" + "=" * 60)
        print("Creating surge alert tables...")
        print("=" * 60)

        # Create tables from models
        Base.metadata.create_all(engine, tables=[
            SurgeAlert.__table__,
            UserFavoriteCoin.__table__
        ])

        # Verify creation
        existing_tables = inspector.get_table_names()

        if 'surge_alerts' in existing_tables:
            print("\n[OK] surge_alerts table created successfully")

            # Show columns
            columns = inspector.get_columns('surge_alerts')
            print("\nColumns:")
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"  - {col['name']}: {col['type']} {nullable}")

            # Show indexes
            indexes = inspector.get_indexes('surge_alerts')
            print("\nIndexes:")
            for idx in indexes:
                print(f"  - {idx['name']}: {idx['column_names']}")
        else:
            print("\n Failed to create surge_alerts table")

        if 'user_favorite_coins' in existing_tables:
            print("\n user_favorite_coins table created successfully")

            # Show columns
            columns = inspector.get_columns('user_favorite_coins')
            print("\nColumns:")
            for col in columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"  - {col['name']}: {col['type']} {nullable}")

            # Show indexes
            indexes = inspector.get_indexes('user_favorite_coins')
            print("\nIndexes:")
            for idx in indexes:
                print(f"  - {idx['name']}: {idx['column_names']}")
        else:
            print("\n Failed to create user_favorite_coins table")

        print("\n" + "=" * 60)
        print(" Database initialization complete")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n Error initializing database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_surge_alert_service():
    """Test surge alert service functionality"""
    print("\n" + "=" * 60)
    print("Testing Surge Alert Service")
    print("=" * 60)

    try:
        from backend.services.surge_alert_service import get_surge_alert_service
        from backend.database.connection import get_db_session

        session = get_db_session()
        service = get_surge_alert_service(session)

        # Test 1: Check weekly count for non-existent user
        print("\n1. Testing weekly count for user ID 1:")
        count = service.get_weekly_alert_count(user_id=1)
        print(f"   Alert count: {count}")

        # Test 2: Check confidence thresholds
        print("\n2. Testing confidence thresholds:")
        for plan in ['free', 'basic', 'pro']:
            threshold_fav = service.get_confidence_threshold(plan, is_favorite=True)
            threshold_reg = service.get_confidence_threshold(plan, is_favorite=False)
            print(f"   {plan.upper()}: favorite={threshold_fav}%, regular={threshold_reg}%")

        # Test 3: Check max alerts for plans
        print("\n3. Testing max alerts per plan:")
        for plan in ['free', 'basic', 'pro']:
            max_alerts = service.get_max_alerts_for_plan(plan)
            print(f"   {plan.upper()}: {max_alerts} alerts/week")

        # Test 4: Format alert message
        print("\n4. Testing alert message formatting:")
        message = service.format_alert_message(
            coin='BTC',
            market='KRW-BTC',
            confidence=85.5,
            current_price=52000000,
            target_price=54000000,
            expected_return=3.8,
            signal_type='favorite'
        )
        print(f"   Message preview (first 100 chars):\n   {message[:100]}...")

        print("\n All tests passed")
        return True

    except Exception as e:
        print(f"\n Error testing service: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main initialization function"""
    print("\nStarting Surge Alert System Initialization\n")

    # Step 1: Initialize database tables
    if not init_surge_alert_tables():
        print("\n Database initialization failed. Exiting.")
        sys.exit(1)

    # Step 2: Test surge alert service
    if not test_surge_alert_service():
        print("\n Service tests failed, but database is initialized.")

    print("\n" + "=" * 60)
    print(" Initialization Complete")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the server: python app.py")
    print("2. Test API endpoints:")
    print("   - GET  /api/user/favorite-coins")
    print("   - POST /api/user/favorite-coins")
    print("   - GET  /api/surge/alerts")
    print("   - GET  /api/surge/alerts/weekly-count")
    print("3. Check documentation: docs/features/SURGE_ALERT_SYSTEM.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
