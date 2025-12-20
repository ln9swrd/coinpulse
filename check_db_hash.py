#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check password hash in database
"""
import psycopg2
from backend.services.auth_service import auth_service

# Connect to database
conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/coinpulse')
cur = conn.cursor()

# Get demo user's password hash
cur.execute("SELECT email, password_hash FROM users WHERE email IN ('demo@coinpulse.com', 'simple@test.com')")
rows = cur.fetchall()

print("="*60)
print("Database Password Hash Verification")
print("="*60)

for email, pwd_hash in rows:
    print(f"\nEmail: {email}")
    print(f"Hash in DB: {pwd_hash[:50]}...")

    if email == 'demo@coinpulse.com':
        test_pwd = 'Demo1234!'
        print(f"Testing with: {test_pwd}")
        is_valid = auth_service.verify_password(test_pwd, pwd_hash)
        print(f"Verification result: {'SUCCESS' if is_valid else 'FAILED'}")

        # Test character by character
        print(f"\nPassword bytes: {test_pwd.encode('utf-8')}")
        print(f"Hash type: {type(pwd_hash)}")
        print(f"Hash starts with $2b$: {pwd_hash.startswith('$2b$')}")

    elif email == 'simple@test.com':
        test_pwd = 'Password123'
        print(f"Testing with: {test_pwd}")
        is_valid = auth_service.verify_password(test_pwd, pwd_hash)
        print(f"Verification result: {'SUCCESS' if is_valid else 'FAILED'}")

cur.close()
conn.close()

print("\n" + "="*60)
