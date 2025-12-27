#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Migrate .env API keys to user-specific keys

Takes UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY from .env
and registers them for a specific user in upbit_api_keys table.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from backend.database.connection import get_db_session
from backend.models.user_api_key import UpbitAPIKey
from backend.utils.crypto import encrypt_api_credentials
from backend.common import UpbitAPI
from datetime import datetime

def migrate_env_keys_to_user(user_id, key_name="Migrated from .env"):
    """
    Migrate .env API keys to user-specific keys

    Args:
        user_id: User ID to register keys for
        key_name: Name for the API key
    """
    print("=" * 60)
    print("Migrate .env API Keys to User-Specific Keys")
    print("=" * 60)
    print()

    # Load .env
    load_dotenv()

    access_key = os.getenv('UPBIT_ACCESS_KEY')
    secret_key = os.getenv('UPBIT_SECRET_KEY')

    if not access_key or not secret_key:
        print("❌ Error: UPBIT_ACCESS_KEY or UPBIT_SECRET_KEY not found in .env")
        return False

    print(f"✅ Found API keys in .env:")
    print(f"   Access Key (first 10 chars): {access_key[:10]}...")
    print(f"   Secret Key (first 10 chars): {secret_key[:10]}...")
    print()

    # Verify keys with Upbit API
    print(f"Step 1: Verifying keys with Upbit API...")
    try:
        api = UpbitAPI(access_key, secret_key)
        accounts = api.get_accounts()

        if not accounts:
            print("❌ API key verification failed: No accounts returned")
            return False

        print(f"✅ Verification successful!")
        print(f"   Account count: {len(accounts)}")
        for acc in accounts[:5]:
            currency = acc.get('currency', 'Unknown')
            balance = float(acc.get('balance', 0))
            if balance > 0:
                print(f"   - {currency}: {balance:,.4f}")
        print()

    except Exception as e:
        print(f"❌ API verification error: {e}")
        return False

    # Encrypt keys
    print(f"Step 2: Encrypting API keys...")
    try:
        encrypted_access, encrypted_secret = encrypt_api_credentials(access_key, secret_key)
        print(f"✅ Encryption successful")
        print(f"   Encrypted access (first 50 chars): {encrypted_access[:50]}...")
        print()
    except Exception as e:
        print(f"❌ Encryption error: {e}")
        return False

    # Save to database
    print(f"Step 3: Saving to database for user {user_id}...")
    session = get_db_session()

    try:
        # Check if user already has keys
        existing_key = session.query(UpbitAPIKey).filter(
            UpbitAPIKey.user_id == user_id
        ).first()

        if existing_key:
            print(f"⚠️  User {user_id} already has API keys registered")
            print(f"   Updating existing keys...")

            existing_key.access_key_encrypted = encrypted_access
            existing_key.secret_key_encrypted = encrypted_secret
            existing_key.key_name = key_name
            existing_key.is_active = True
            existing_key.is_verified = True
            existing_key.updated_at = datetime.utcnow()

            session.commit()

            print(f"✅ Updated existing API keys for user {user_id}")
            print(f"   Key ID: {existing_key.id}")
            print(f"   Key Name: {existing_key.key_name}")
            print(f"   Created: {existing_key.created_at}")
            print(f"   Updated: {existing_key.updated_at}")

        else:
            print(f"📝 Creating new API key record...")

            new_key = UpbitAPIKey(
                user_id=user_id,
                access_key_encrypted=encrypted_access,
                secret_key_encrypted=encrypted_secret,
                key_name=key_name,
                is_active=True,
                is_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            session.add(new_key)
            session.commit()

            print(f"✅ Created new API keys for user {user_id}")
            print(f"   Key ID: {new_key.id}")
            print(f"   Key Name: {new_key.key_name}")
            print(f"   Created: {new_key.created_at}")

        print()

        # Verify database record
        print(f"Step 4: Verifying database record...")
        saved_key = session.query(UpbitAPIKey).filter(
            UpbitAPIKey.user_id == user_id
        ).first()

        if saved_key:
            print(f"✅ Database record confirmed:")
            print(f"   User ID: {saved_key.user_id}")
            print(f"   Active: {saved_key.is_active}")
            print(f"   Verified: {saved_key.is_verified}")
            print(f"   Error Count: {saved_key.error_count}")
        else:
            print(f"❌ Database record not found!")
            return False

        print()
        print("=" * 60)
        print("Migration Complete!")
        print("=" * 60)
        print()
        print(f"✅ User {user_id} now has personal API keys registered")
        print(f"✅ Auto-trading will use user-specific keys (not global .env)")
        print(f"✅ Next surge signal will execute orders with user's Upbit account")
        print()

        session.close()
        return True

    except Exception as e:
        print(f"❌ Database error: {e}")
        session.rollback()
        session.close()
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Migrate .env API keys to user')
    parser.add_argument('--user-id', type=int, required=True, help='User ID to register keys for')
    parser.add_argument('--key-name', type=str, default='Migrated from .env', help='Name for the API key')

    args = parser.parse_args()

    success = migrate_env_keys_to_user(args.user_id, args.key_name)

    if success:
        print("✅ Run test script to verify:")
        print(f"   ./venv/bin/python scripts/test_api_key_flow.py --user-id {args.user_id} --real")
        sys.exit(0)
    else:
        print("❌ Migration failed")
        sys.exit(1)
