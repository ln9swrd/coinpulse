"""
Swing Trading Database Initialization Script

Creates database tables and 3 test users for swing trading system.
"""

import os
import sys
import secrets
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.database import init_database, get_db_session, User, UserConfig


def generate_api_key():
    """Generate a secure API key."""
    return secrets.token_hex(32)  # 64-character hex string


def load_config():
    """Load trading server configuration."""
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'trading_server_config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("[Warning] trading_server_config.json not found, using defaults")
        return {}


def create_test_users():
    """Create 3 test users with default configurations."""

    print("\n" + "="*60)
    print("SWING TRADING DATABASE INITIALIZATION")
    print("="*60)

    # Load configuration
    config = load_config()

    # Initialize database (creates tables)
    print("\n[1/3] Initializing database...")
    init_database(create_tables=True, config=config)
    print("[OK] Database initialized successfully")

    # Create session
    session = get_db_session()

    try:
        print("\n[2/3] Creating test users...")

        # Test users configuration
        test_users = [
            {
                'username': 'test_user_1',
                'email': 'user1@test.com',
                'budget': 40000,
                'max_positions': 3
            },
            {
                'username': 'test_user_2',
                'email': 'user2@test.com',
                'budget': 30000,
                'max_positions': 2
            },
            {
                'username': 'test_user_3',
                'email': 'user3@test.com',
                'budget': 50000,
                'max_positions': 4
            }
        ]

        created_users = []

        for user_data in test_users:
            # Check if user already exists
            existing_user = session.query(User).filter_by(username=user_data['username']).first()
            if existing_user:
                print(f"[WARNING] User '{user_data['username']}' already exists, skipping...")
                created_users.append(existing_user)
                continue

            # Create user
            api_key = generate_api_key()
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                api_key=api_key,
                is_active=True,
                created_at=datetime.utcnow()
            )

            session.add(user)
            session.flush()  # Get user_id

            # Create user configuration
            config = UserConfig(
                user_id=user.user_id,
                total_budget_krw=user_data['budget'],
                min_order_amount=6000,
                max_order_amount=user_data['budget'],
                max_concurrent_positions=user_data['max_positions'],
                holding_period_days=3,
                force_sell_after_period=False,
                take_profit_min=0.08,
                take_profit_max=0.15,
                stop_loss_min=0.03,
                stop_loss_max=0.05,
                emergency_stop_loss=0.03,
                auto_stop_on_loss=True,
                swing_trading_enabled=True,
                test_mode=True
            )

            session.add(config)
            created_users.append(user)

            print(f"[OK] Created user: {user_data['username']} (ID: {user.user_id})")

        # Commit all changes
        session.commit()
        print(f"\n[OK] Successfully created/verified {len(created_users)} users")

        # Display user information
        print("\n[3/3] User Information:")
        print("-" * 80)
        print(f"{'Username':<20} {'User ID':<10} {'API Key':<66} {'Budget':>10}")
        print("-" * 80)

        for user in created_users:
            config = session.query(UserConfig).filter_by(user_id=user.user_id).first()
            print(f"{user.username:<20} {user.user_id:<10} {user.api_key:<66} {config.total_budget_krw:>10,} KRW")

        print("-" * 80)

        # Display configuration summary
        print("\n[Configuration Summary]")
        print(f"   - Holding Period: 3 days")
        print(f"   - Take Profit: 8-15%")
        print(f"   - Stop Loss: 3-5%")
        print(f"   - Emergency Stop: 3% per coin")
        print(f"   - Test Mode: Enabled (no real orders)")
        print(f"   - Auto Stop on Loss: Enabled")

        # Display database location
        from backend.database.connection import get_database_url
        db_url = get_database_url()
        if 'sqlite' in db_url:
            db_path = db_url.replace('sqlite:///', '')
            print(f"\n[Database Location] {db_path}")
        else:
            print(f"\n[Database] {db_url}")

        print("\n" + "="*60)
        print("[OK] INITIALIZATION COMPLETE")
        print("="*60)
        print("\nNext Steps:")
        print("1. Use the API keys above for user authentication")
        print("2. Run swing trading engine with user_id parameter")
        print("3. Monitor positions in swing_positions table")
        print("\n")

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] {e}")
        raise

    finally:
        session.close()


if __name__ == '__main__':
    create_test_users()
