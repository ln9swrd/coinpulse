#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grant Admin Rights to User
관리자 권한 부여 스크립트
"""

import sys
from backend.database.connection import get_db_session
from backend.database.models import User


def grant_admin(email_or_id):
    """Grant admin rights to a user by email or ID"""
    session = get_db_session()
    try:
        # Try to find user by ID first
        try:
            user_id = int(email_or_id)
            user = session.query(User).filter(User.id == user_id).first()
        except ValueError:
            # Not an ID, search by email
            user = session.query(User).filter(User.email == email_or_id).first()

        if not user:
            print(f"❌ User not found: {email_or_id}")
            return False

        if user.is_admin:
            print(f"✅ User is already an admin: {user.email} (ID: {user.id})")
            return True

        # Grant admin rights
        user.is_admin = True
        session.commit()
        session.refresh(user)

        print(f"✅ Admin rights granted successfully!")
        print(f"   Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   ID: {user.id}")
        print(f"   Is Admin: {user.is_admin}")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def revoke_admin(email_or_id):
    """Revoke admin rights from a user by email or ID"""
    session = get_db_session()
    try:
        # Try to find user by ID first
        try:
            user_id = int(email_or_id)
            user = session.query(User).filter(User.id == user_id).first()
        except ValueError:
            # Not an ID, search by email
            user = session.query(User).filter(User.email == email_or_id).first()

        if not user:
            print(f"❌ User not found: {email_or_id}")
            return False

        if not user.is_admin:
            print(f"✅ User is already not an admin: {user.email} (ID: {user.id})")
            return True

        # Revoke admin rights
        user.is_admin = False
        session.commit()
        session.refresh(user)

        print(f"✅ Admin rights revoked successfully!")
        print(f"   Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   ID: {user.id}")
        print(f"   Is Admin: {user.is_admin}")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def list_users():
    """List all users with admin status"""
    session = get_db_session()
    try:
        users = session.query(User).order_by(User.id).all()

        print("\n" + "=" * 80)
        print("전체 사용자 목록")
        print("=" * 80)
        print(f"{'ID':<5} {'Email':<35} {'Username':<20} {'Admin':<10}")
        print("-" * 80)

        for user in users:
            admin_status = '✅ YES' if user.is_admin else '❌ NO'
            email = user.email[:32] + '...' if len(user.email) > 35 else user.email
            username = user.username[:17] + '...' if len(user.username) > 20 else user.username
            print(f"{user.id:<5} {email:<35} {username:<20} {admin_status:<10}")

        print("-" * 80)
        print(f"총 {len(users)}명의 사용자")

        admin_count = sum(1 for u in users if u.is_admin)
        print(f"관리자: {admin_count}명")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python grant_admin.py list                    # List all users")
        print("  python grant_admin.py grant <email_or_id>     # Grant admin rights")
        print("  python grant_admin.py revoke <email_or_id>    # Revoke admin rights")
        print("\nExamples:")
        print("  python grant_admin.py list")
        print("  python grant_admin.py grant test@example.com")
        print("  python grant_admin.py grant 5")
        print("  python grant_admin.py revoke test@example.com")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'list':
        list_users()
    elif command == 'grant':
        if len(sys.argv) < 3:
            print("❌ Error: Email or ID required")
            print("Usage: python grant_admin.py grant <email_or_id>")
            sys.exit(1)
        email_or_id = sys.argv[2]
        grant_admin(email_or_id)
    elif command == 'revoke':
        if len(sys.argv) < 3:
            print("❌ Error: Email or ID required")
            print("Usage: python grant_admin.py revoke <email_or_id>")
            sys.exit(1)
        email_or_id = sys.argv[2]
        revoke_admin(email_or_id)
    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: list, grant, revoke")
        sys.exit(1)
