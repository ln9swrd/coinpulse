#!/usr/bin/env python
# -*- coding: utf-8 -*-

from backend.database.connection import get_db_session
from backend.database.models import User
from backend.services.auth_service import auth_service

# User credentials
email = 'test@example.com'
new_password = 'Password123'

session = get_db_session()
try:
    user = session.query(User).filter_by(email=email).first()

    if not user:
        print(f'[ERROR] User not found: {email}')
        exit(1)

    print(f'[OK] User found: {user.email}')
    print(f'Username: {user.username}')
    print(f'Current password set: {user.password_hash is not None}')

    # Hash the new password
    password_hash = auth_service.hash_password(new_password)

    # Update the user's password
    user.password_hash = password_hash
    session.commit()

    print(f'\n[OK] Password successfully set to: "{new_password}"')
    print(f'Password hash: {password_hash[:50]}...')

    # Verify the password works
    if auth_service.verify_password(new_password, user.password_hash):
        print(f'\n[SUCCESS] Verification successful! You can now login with:')
        print(f'   Email: {email}')
        print(f'   Password: {new_password}')
    else:
        print(f'\n[ERROR] Verification failed!')

except Exception as e:
    print(f'[ERROR] {str(e)}')
    session.rollback()
finally:
    session.close()
