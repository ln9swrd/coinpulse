#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Initialize Plan Configs with Email Notification Features
플랜 설정 초기 데이터 생성 (이메일 알림 기능 포함)
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.database.connection import get_db_session, init_database
from backend.models.plan_config import PlanConfig


def init_plan_configs():
    """Initialize plan configs with email notification features"""

    # Initialize database and create tables
    print("=" * 60)
    print("Initializing Plan Configs")
    print("=" * 60)

    engine = init_database(create_tables=True)
    session = get_db_session()

    # Check if plans already exist
    existing_count = session.query(PlanConfig).count()
    if existing_count > 0:
        print(f"\n[INFO] {existing_count} plans already exist in database")
        print("Do you want to recreate them? (y/n): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            print("[SKIP] Keeping existing plans")
            session.close()
            return
        else:
            # Delete existing plans
            session.query(PlanConfig).delete()
            session.commit()
            print("[OK] Deleted existing plans")

    print("\n[INFO] Creating initial plan configs...")

    # Plan configurations with email features
    plans = [
        {
            'plan_code': 'free',
            'plan_name': 'Free',
            'plan_name_ko': '무료',
            'description': '기본 기능을 체험해보세요',
            'display_order': 1,
            'monthly_price': 0,
            'annual_price': 0,
            'setup_fee': 0,
            'annual_discount_rate': 0,
            'trial_days': 0,

            # Limits
            'max_coins': 1,
            'max_watchlists': 5,
            'auto_trading_enabled': False,
            'max_auto_strategies': 0,
            'max_concurrent_trades': 0,

            # Features
            'advanced_indicators': False,
            'custom_indicators': False,
            'backtesting_enabled': False,
            'history_days': 7,
            'data_export': False,
            'api_access': False,

            # Email Notifications
            'email_notifications_enabled': False,
            'daily_email_limit': 0,
            'signal_notifications': False,
            'portfolio_notifications': False,
            'trade_notifications': False,
            'system_notifications': False,

            # Support
            'support_level': 'community',
            'response_time_hours': 72,

            # Other
            'white_labeling': False,
            'sla_guarantee': False,
            'custom_development': False,

            # Display
            'is_active': True,
            'is_featured': False,
            'is_visible': True,
            'badge_text': None,
            'cta_text': 'Start Free',
        },
        {
            'plan_code': 'basic',
            'plan_name': 'Basic',
            'plan_name_ko': '베이직',
            'description': '개인 투자자를 위한 기본 플랜',
            'display_order': 2,
            'monthly_price': 29000,
            'annual_price': 290000,
            'setup_fee': 0,
            'annual_discount_rate': 15,
            'trial_days': 7,

            # Limits
            'max_coins': 5,
            'max_watchlists': 20,
            'auto_trading_enabled': True,
            'max_auto_strategies': 2,
            'max_concurrent_trades': 3,

            # Features
            'advanced_indicators': True,
            'custom_indicators': False,
            'backtesting_enabled': False,
            'history_days': 30,
            'data_export': False,
            'api_access': False,

            # Email Notifications
            'email_notifications_enabled': True,
            'daily_email_limit': 10,
            'signal_notifications': True,
            'portfolio_notifications': False,
            'trade_notifications': False,
            'system_notifications': True,

            # Support
            'support_level': 'email',
            'response_time_hours': 48,

            # Other
            'white_labeling': False,
            'sla_guarantee': False,
            'custom_development': False,

            # Display
            'is_active': True,
            'is_featured': False,
            'is_visible': True,
            'badge_text': 'Popular',
            'cta_text': 'Start 7-Day Trial',
        },
        {
            'plan_code': 'pro',
            'plan_name': 'Pro',
            'plan_name_ko': '프로',
            'description': '전문 투자자를 위한 고급 플랜',
            'display_order': 3,
            'monthly_price': 99000,
            'annual_price': 990000,
            'setup_fee': 0,
            'annual_discount_rate': 15,
            'trial_days': 14,

            # Limits
            'max_coins': 0,  # unlimited
            'max_watchlists': 100,
            'auto_trading_enabled': True,
            'max_auto_strategies': 0,  # unlimited
            'max_concurrent_trades': 0,  # unlimited

            # Features
            'advanced_indicators': True,
            'custom_indicators': True,
            'backtesting_enabled': True,
            'history_days': 0,  # unlimited
            'data_export': True,
            'api_access': True,

            # Email Notifications
            'email_notifications_enabled': True,
            'daily_email_limit': 50,
            'signal_notifications': True,
            'portfolio_notifications': True,
            'trade_notifications': True,
            'system_notifications': True,

            # Support
            'support_level': 'priority',
            'response_time_hours': 24,

            # Other
            'white_labeling': False,
            'sla_guarantee': False,
            'custom_development': False,

            # Display
            'is_active': True,
            'is_featured': True,
            'is_visible': True,
            'badge_text': 'Best Value',
            'cta_text': 'Start 14-Day Trial',
        },
        {
            'plan_code': 'enterprise',
            'plan_name': 'Enterprise',
            'plan_name_ko': '엔터프라이즈',
            'description': '기업 및 기관 투자자를 위한 맞춤형 플랜',
            'display_order': 4,
            'monthly_price': 0,  # Custom pricing
            'annual_price': 0,   # Custom pricing
            'setup_fee': 0,
            'annual_discount_rate': 0,
            'trial_days': 30,

            # Limits - all unlimited
            'max_coins': 0,
            'max_watchlists': 0,
            'auto_trading_enabled': True,
            'max_auto_strategies': 0,
            'max_concurrent_trades': 0,

            # Features - all enabled
            'advanced_indicators': True,
            'custom_indicators': True,
            'backtesting_enabled': True,
            'history_days': 0,
            'data_export': True,
            'api_access': True,

            # Email Notifications - unlimited
            'email_notifications_enabled': True,
            'daily_email_limit': 0,  # unlimited
            'signal_notifications': True,
            'portfolio_notifications': True,
            'trade_notifications': True,
            'system_notifications': True,

            # Support - dedicated
            'support_level': 'dedicated',
            'response_time_hours': 4,

            # Other - all enabled
            'white_labeling': True,
            'sla_guarantee': True,
            'custom_development': True,

            # Display
            'is_active': True,
            'is_featured': False,
            'is_visible': True,
            'badge_text': 'Custom',
            'cta_text': 'Contact Sales',
        },
    ]

    # Create plan configs
    created_count = 0
    for plan_data in plans:
        plan = PlanConfig(**plan_data)
        session.add(plan)
        created_count += 1
        print(f"[OK] Created plan: {plan_data['plan_code']}")

    session.commit()

    print("\n" + "=" * 60)
    print(f"[SUCCESS] Created {created_count} plan configs")
    print("=" * 60)

    # Display summary
    print("\n" + "=" * 80)
    print("Plan Summary")
    print("=" * 80 + "\n")

    plans = session.query(PlanConfig).order_by(PlanConfig.display_order).all()

    print(f"{'Plan':<15} {'Price':<15} {'Email':<8} {'Limit':<12} {'Features':<20}")
    print("-" * 80)

    for plan in plans:
        price = f"{plan.monthly_price:,}원/월" if plan.monthly_price > 0 else "무료"
        email = "[YES]" if plan.email_notifications_enabled else "[NO]"
        limit = f"{plan.daily_email_limit}/day" if plan.daily_email_limit > 0 else ("Unlimited" if plan.email_notifications_enabled else "-")

        features = []
        if plan.auto_trading_enabled:
            features.append("Auto")
        if plan.api_access:
            features.append("API")
        if plan.backtesting_enabled:
            features.append("Backtest")
        features_str = ", ".join(features) if features else "Basic"

        print(f"{plan.plan_code:<15} {price:<15} {email:<8} {limit:<12} {features_str:<20}")

    print("\n" + "=" * 80 + "\n")

    session.close()
    print("Initialization complete!")


if __name__ == '__main__':
    try:
        init_plan_configs()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Initialization interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAILED] Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
