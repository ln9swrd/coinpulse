# -*- coding: utf-8 -*-
"""
Initialize surge_system_settings table in database
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import init_database, get_db_session
from backend.models.surge_system_settings import SurgeSystemSettings
from sqlalchemy import text

def init_surge_settings_table():
    """Create table and insert default settings"""
    print("\n" + "="*60)
    print("Initializing surge_system_settings Table")
    print("="*60 + "\n")

    try:
        # Initialize database first
        print("[INFO] Initializing database connection...")
        engine = init_database(create_tables=False)

        # Create table using SQLAlchemy ORM
        print("[INFO] Creating table from model...")
        SurgeSystemSettings.__table__.create(engine, checkfirst=True)
        print("[OK] Table created (or already exists)")

        # Check if default settings exist
        with get_db_session() as session:
            existing = session.query(SurgeSystemSettings).filter_by(id=1).first()

            if existing:
                print("[OK] Default settings already exist:")
                print(f"  - base_min_score: {existing.base_min_score}")
                print(f"  - telegram_min_score: {existing.telegram_min_score}")
                print(f"  - db_save_threshold: {existing.db_save_threshold}")
                print(f"  - check_interval: {existing.check_interval}s")
                print(f"  - monitor_coins_count: {existing.monitor_coins_count}")
                print(f"  - duplicate_alert_hours: {existing.duplicate_alert_hours}h")
            else:
                # Create default settings
                print("[INFO] Creating default settings...")
                settings = SurgeSystemSettings(
                    id=1,
                    base_min_score=60,
                    telegram_min_score=70,
                    db_save_threshold=60,
                    check_interval=300,
                    monitor_coins_count=50,
                    duplicate_alert_hours=24,
                    worker_enabled=True,
                    scheduler_enabled=True,
                    updated_by='system',
                    notes='Initial system settings'
                )
                settings.set_analysis_config(SurgeSystemSettings.get_default_analysis_config())

                session.add(settings)
                session.commit()

                print("[OK] Default settings created:")
                print(f"  - base_min_score: {settings.base_min_score}")
                print(f"  - telegram_min_score: {settings.telegram_min_score}")
                print(f"  - db_save_threshold: {settings.db_save_threshold}")
                print(f"  - check_interval: {settings.check_interval}s")
                print(f"  - monitor_coins_count: {settings.monitor_coins_count}")
                print(f"  - duplicate_alert_hours: {settings.duplicate_alert_hours}h")
                print(f"\n  Analysis config:")
                config = settings.get_analysis_config()
                for key, value in config.items():
                    print(f"    - {key}: {value}")

        print("\n" + "="*60)
        print("Initialization Complete!")
        print("="*60 + "\n")

        return True

    except Exception as e:
        print(f"[ERROR] Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = init_surge_settings_table()
    sys.exit(0 if success else 1)
