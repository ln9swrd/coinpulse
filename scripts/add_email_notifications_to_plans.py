#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add Email Notification Features to Plan Configs
데이터베이스에 이메일 알림 컬럼 추가 및 플랜별 설정
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db_session, init_database
from backend.models.plan_config import PlanConfig
from sqlalchemy import text

def add_email_notification_columns():
    """Add email notification columns to plan_configs table"""
    # Initialize database and create tables if they don't exist
    engine = init_database(create_tables=True)

    print("=" * 60)
    print("Adding Email Notification Columns to plan_configs")
    print("=" * 60)

    # SQL to add new columns
    columns_to_add = [
        ("email_notifications_enabled", "BOOLEAN DEFAULT FALSE NOT NULL"),
        ("daily_email_limit", "INTEGER DEFAULT 0 NOT NULL"),
        ("signal_notifications", "BOOLEAN DEFAULT FALSE NOT NULL"),
        ("portfolio_notifications", "BOOLEAN DEFAULT FALSE NOT NULL"),
        ("trade_notifications", "BOOLEAN DEFAULT FALSE NOT NULL"),
        ("system_notifications", "BOOLEAN DEFAULT FALSE NOT NULL"),
    ]

    with engine.connect() as conn:
        for column_name, column_def in columns_to_add:
            try:
                # Check if column exists
                result = conn.execute(text(f"""
                    SELECT COUNT(*)
                    FROM pragma_table_info('plan_configs')
                    WHERE name = '{column_name}'
                """))

                exists = result.scalar() > 0

                if not exists:
                    # Add column
                    conn.execute(text(f"""
                        ALTER TABLE plan_configs
                        ADD COLUMN {column_name} {column_def}
                    """))
                    conn.commit()
                    print(f"[OK] Added column: {column_name}")
                else:
                    print(f"[SKIP] Column already exists: {column_name}")

            except Exception as e:
                print(f"[ERROR] Error adding column {column_name}: {e}")

    print("\n" + "=" * 60)
    print("Column addition complete!")
    print("=" * 60 + "\n")


def update_plan_email_features():
    """Update existing plans with email notification features"""
    session = get_db_session()

    print("=" * 60)
    print("Updating Plan Email Notification Features")
    print("=" * 60 + "\n")

    # Plan configurations
    plan_configs = {
        'free': {
            'email_notifications_enabled': False,
            'daily_email_limit': 0,
            'signal_notifications': False,
            'portfolio_notifications': False,
            'trade_notifications': False,
            'system_notifications': False,
        },
        'basic': {
            'email_notifications_enabled': True,
            'daily_email_limit': 10,  # 일일 10건
            'signal_notifications': True,
            'portfolio_notifications': False,
            'trade_notifications': False,
            'system_notifications': True,
        },
        'pro': {
            'email_notifications_enabled': True,
            'daily_email_limit': 50,  # 일일 50건
            'signal_notifications': True,
            'portfolio_notifications': True,
            'trade_notifications': True,
            'system_notifications': True,
        },
        'premium': {  # Alias for pro
            'email_notifications_enabled': True,
            'daily_email_limit': 50,
            'signal_notifications': True,
            'portfolio_notifications': True,
            'trade_notifications': True,
            'system_notifications': True,
        },
        'enterprise': {
            'email_notifications_enabled': True,
            'daily_email_limit': 0,  # 무제한
            'signal_notifications': True,
            'portfolio_notifications': True,
            'trade_notifications': True,
            'system_notifications': True,
        }
    }

    try:
        for plan_code, features in plan_configs.items():
            # Find plan
            plan = session.query(PlanConfig).filter(
                PlanConfig.plan_code == plan_code
            ).first()

            if plan:
                # Update features
                for key, value in features.items():
                    setattr(plan, key, value)

                print(f"[OK] Updated plan: {plan_code}")
                print(f"   - Email enabled: {features['email_notifications_enabled']}")
                print(f"   - Daily limit: {features['daily_email_limit']} (0 = unlimited)")
                print(f"   - Signal: {features['signal_notifications']}")
                print(f"   - Portfolio: {features['portfolio_notifications']}")
                print(f"   - Trade: {features['trade_notifications']}")
                print(f"   - System: {features['system_notifications']}")
                print()
            else:
                print(f"[WARNING] Plan not found: {plan_code}")

        session.commit()
        print("\n" + "=" * 60)
        print("[SUCCESS] All plans updated successfully!")
        print("=" * 60)

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Error updating plans: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


def display_plan_comparison():
    """Display plan comparison table"""
    session = get_db_session()

    print("\n" + "=" * 80)
    print("Plan Email Notification Features Comparison")
    print("=" * 80 + "\n")

    plans = session.query(PlanConfig).order_by(PlanConfig.display_order).all()

    # Header
    print(f"{'Plan':<15} {'Email':<8} {'Daily Limit':<12} {'Signal':<8} {'Portfolio':<10} {'Trade':<8} {'System':<8}")
    print("-" * 80)

    for plan in plans:
        email_status = "[YES]" if plan.email_notifications_enabled else "[NO]"
        limit = "Unlimited" if plan.daily_email_limit == 0 else str(plan.daily_email_limit)
        signal = "[YES]" if plan.signal_notifications else "[NO]"
        portfolio = "[YES]" if plan.portfolio_notifications else "[NO]"
        trade = "[YES]" if plan.trade_notifications else "[NO]"
        system = "[YES]" if plan.system_notifications else "[NO]"

        print(f"{plan.plan_code:<15} {email_status:<8} {limit:<12} {signal:<8} {portfolio:<10} {trade:<8} {system:<8}")

    print("\n" + "=" * 80 + "\n")

    session.close()


def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("CoinPulse Email Notification Features Setup")
    print("=" * 60 + "\n")

    # Step 1: Add columns to database
    add_email_notification_columns()

    # Step 2: Update plan features
    update_plan_email_features()

    # Step 3: Display comparison
    display_plan_comparison()

    print("Setup complete! Email notification features are now available.")
    print("\nBenefits per plan:")
    print("   - Free: No email notifications")
    print("   - Basic: 10 emails/day (Signal + System only)")
    print("   - Pro/Premium: 50 emails/day (All notifications)")
    print("   - Enterprise: Unlimited emails (All notifications)")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAILED] Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
