# -*- coding: utf-8 -*-
"""
Initialize Auto-Trading Tables
Create surge_auto_trading_settings table and insert test settings
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_db_session
from backend.models.surge_alert_models import SurgeAutoTradingSettings
from sqlalchemy import text

def init_auto_trading():
    """Initialize auto-trading tables"""

    print("=" * 100)
    print("INITIALIZING AUTO-TRADING TABLES")
    print("=" * 100)

    # Create tables
    print("\n[Step 1] Creating tables...")
    try:
        from backend.database.connection import Base, engine
        Base.metadata.create_all(engine)
        print("[OK] Tables created successfully")
    except Exception as e:
        print(f"[WARNING] Table creation: {str(e)}")

    # Insert default settings for user_id=1 (test user)
    print("\n[Step 2] Creating default settings for user_id=1...")

    with get_db_session() as session:
        try:
            # Check if settings already exist
            check_query = text("""
                SELECT id FROM surge_auto_trading_settings WHERE user_id = 1
            """)
            existing = session.execute(check_query).fetchone()

            if existing:
                print(f"[WARNING] Settings already exist for user_id=1 (id={existing[0]})")
                print("   Skipping insert...")
            else:
                # Insert default settings
                insert_query = text("""
                    INSERT INTO surge_auto_trading_settings (
                        user_id, enabled, total_budget, amount_per_trade,
                        risk_level, stop_loss_enabled, stop_loss_percent,
                        take_profit_enabled, take_profit_percent,
                        min_confidence, max_positions, telegram_enabled,
                        use_dynamic_target, min_target_percent, max_target_percent
                    ) VALUES (
                        :user_id, :enabled, :total_budget, :amount_per_trade,
                        :risk_level, :stop_loss_enabled, :stop_loss_percent,
                        :take_profit_enabled, :take_profit_percent,
                        :min_confidence, :max_positions, :telegram_enabled,
                        :use_dynamic_target, :min_target_percent, :max_target_percent
                    )
                """)

                session.execute(insert_query, {
                    'user_id': 1,
                    'enabled': True,
                    'total_budget': 1000000,       # 100만원
                    'amount_per_trade': 100000,    # 10만원
                    'risk_level': 'moderate',
                    'stop_loss_enabled': True,
                    'stop_loss_percent': -5.0,
                    'take_profit_enabled': True,
                    'take_profit_percent': 10.0,
                    'min_confidence': 70.0,        # 70% 이상만
                    'max_positions': 5,
                    'telegram_enabled': True,
                    'use_dynamic_target': True,
                    'min_target_percent': 3.0,
                    'max_target_percent': 10.0
                })

                session.commit()
                print("[OK] Default settings created for user_id=1")

        except Exception as e:
            print(f"[ERROR] Error creating settings: {str(e)}")
            return

    # Verify
    print("\n[Step 3] Verifying settings...")
    with get_db_session() as session:
        try:
            verify_query = text("""
                SELECT
                    user_id, enabled, total_budget, amount_per_trade,
                    min_confidence, max_positions
                FROM surge_auto_trading_settings
                WHERE user_id = 1
            """)

            result = session.execute(verify_query).fetchone()

            if result:
                print("[OK] Settings verified:")
                print(f"   User ID: {result[0]}")
                print(f"   Enabled: {result[1]}")
                print(f"   Total Budget: {result[2]:,} KRW")
                print(f"   Amount per Trade: {result[3]:,} KRW")
                print(f"   Min Confidence: {result[4]}%")
                print(f"   Max Positions: {result[5]}")
            else:
                print("[ERROR] Settings not found!")

        except Exception as e:
            print(f"[ERROR] Verification failed: {str(e)}")

    print("\n" + "=" * 100)
    print("INITIALIZATION COMPLETE")
    print("=" * 100)


if __name__ == '__main__':
    init_auto_trading()
