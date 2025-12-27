#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Migrate Upbit API keys from users table to upbit_api_keys table

Old structure: users.upbit_access_key, users.upbit_secret_key (plaintext)
New structure: upbit_api_keys table (encrypted with Fernet)
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text
from backend.database.connection import get_db_session
from backend.models.user_api_key import UpbitAPIKey
from backend.utils.crypto import encrypt_api_credentials
from backend.common import UpbitAPI
from datetime import datetime

def migrate_user_keys(user_id=None, verify_with_upbit=True):
    """
    Migrate Upbit API keys from users table to upbit_api_keys table

    Args:
        user_id: Specific user ID to migrate (None = all users)
        verify_with_upbit: Whether to verify keys with Upbit API
    """
    print("=" * 60)
    print("Migrate Upbit API Keys from users table")
    print("=" * 60)
    print()

    session = get_db_session()

    try:
        # Query users with Upbit keys
        if user_id:
            query = text("""
                SELECT id, email, username, upbit_access_key, upbit_secret_key
                FROM users
                WHERE id = :user_id
                AND upbit_access_key IS NOT NULL
                AND upbit_secret_key IS NOT NULL
                AND upbit_access_key != ''
                AND upbit_secret_key != ''
            """)
            result = session.execute(query, {"user_id": user_id})
        else:
            query = text("""
                SELECT id, email, username, upbit_access_key, upbit_secret_key
                FROM users
                WHERE upbit_access_key IS NOT NULL
                AND upbit_secret_key IS NOT NULL
                AND upbit_access_key != ''
                AND upbit_secret_key != ''
            """)
            result = session.execute(query)

        users_with_keys = result.fetchall()

        if not users_with_keys:
            print(f"❌ No users found with Upbit keys")
            if user_id:
                print(f"   User {user_id} has no keys in users table")
            return False

        print(f"✅ Found {len(users_with_keys)} user(s) with Upbit keys in users table")
        print()

        success_count = 0
        failed_count = 0

        for user_row in users_with_keys:
            uid = user_row[0]
            email = user_row[1]
            username = user_row[2]
            access_key = user_row[3]
            secret_key = user_row[4]

            print(f"Processing user {uid} ({email})...")

            # Check if already exists in upbit_api_keys
            existing_key = session.query(UpbitAPIKey).filter(
                UpbitAPIKey.user_id == uid
            ).first()

            if existing_key:
                print(f"  ⚠️  Already has keys in upbit_api_keys table (skipping)")
                print()
                continue

            # Verify with Upbit API (optional)
            is_verified = False
            if verify_with_upbit:
                try:
                    print(f"  🔍 Verifying with Upbit API...")
                    api = UpbitAPI(access_key, secret_key)
                    accounts = api.get_accounts()

                    if accounts:
                        is_verified = True
                        print(f"     ✅ Verified! Account count: {len(accounts)}")
                    else:
                        print(f"     ⚠️  Verification returned no accounts")
                except Exception as e:
                    print(f"     ❌ Verification failed: {e}")
                    print(f"     → Will still migrate (marked as unverified)")

            # Encrypt keys
            try:
                print(f"  🔐 Encrypting keys...")
                encrypted_access, encrypted_secret = encrypt_api_credentials(access_key, secret_key)
                print(f"     ✅ Encryption successful")
            except Exception as e:
                print(f"     ❌ Encryption failed: {e}")
                failed_count += 1
                print()
                continue

            # Save to upbit_api_keys table
            try:
                print(f"  💾 Saving to upbit_api_keys table...")

                new_key = UpbitAPIKey(
                    user_id=uid,
                    access_key_encrypted=encrypted_access,
                    secret_key_encrypted=encrypted_secret,
                    key_name=f"{username or email} (migrated from users table)",
                    is_active=True,
                    is_verified=is_verified,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                session.add(new_key)
                session.commit()

                print(f"     ✅ Saved! Key ID: {new_key.id}")
                success_count += 1

            except Exception as e:
                print(f"     ❌ Save failed: {e}")
                session.rollback()
                failed_count += 1

            print()

        # Summary
        print("=" * 60)
        print("Migration Summary")
        print("=" * 60)
        print(f"✅ Success: {success_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📊 Total: {len(users_with_keys)}")
        print()

        if success_count > 0:
            print("✅ Migrated users can now use user-specific API keys")
            print("✅ Auto-trading will use encrypted keys from upbit_api_keys table")
            print()
            print("⚠️  Note: Original keys in users table are NOT deleted")
            print("   Consider removing them manually after confirming migration")

        session.close()
        return success_count > 0

    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        session.close()
        return False


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Migrate Upbit keys from users table')
    parser.add_argument('--user-id', type=int, help='Specific user ID to migrate (optional)')
    parser.add_argument('--no-verify', action='store_true', help='Skip Upbit API verification')

    args = parser.parse_args()

    success = migrate_user_keys(
        user_id=args.user_id,
        verify_with_upbit=not args.no_verify
    )

    if success:
        print("✅ Run test script to verify:")
        if args.user_id:
            print(f"   ./venv/bin/python scripts/test_api_key_flow.py --user-id {args.user_id} --real")
        sys.exit(0)
    else:
        sys.exit(1)
