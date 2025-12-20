#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reverse test - try different password variations
"""
import psycopg2
from backend.services.auth_service import auth_service

# Get the hash from database
conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/coinpulse')
cur = conn.cursor()
cur.execute("SELECT password_hash FROM users WHERE email = 'demo@coinpulse.com'")
stored_hash = cur.fetchone()[0]
cur.close()
conn.close()

print("="*60)
print("Trying different password variations")
print("="*60)
print(f"Stored hash: {stored_hash[:50]}...\n")

# Try different variations
test_passwords = [
    'Demo1234!',
    'Demo1234\\!',
    'Demo1234\!',
    '"Demo1234!"',
    '\'Demo1234!\'',
    'Demo1234',
    'demo1234!',
    'Demo1234! ',   # with space
    ' Demo1234!',   # with space
]

for pwd in test_passwords:
    is_valid = auth_service.verify_password(pwd, stored_hash)
    status = "SUCCESS" if is_valid else "FAILED"
    print(f"{status:8} | {repr(pwd):25} | bytes: {pwd.encode('utf-8')}")

print("\n" + "="*60)
