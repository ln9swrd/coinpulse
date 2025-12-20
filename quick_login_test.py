#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick login test
"""
import requests

print("="*60)
print("Quick Login Tests")
print("="*60)

# Test accounts
accounts = [
    ('simple@test.com', 'Password123'),
    ('ln9swrd@gmail.com', 'password'),
    ('ln9swrd@gmail.com', 'Password123'),
]

for email, pwd in accounts:
    print(f"\nTesting: {email} / {pwd}")

    try:
        response = requests.post(
            'http://localhost:8080/api/auth/login',
            json={'email': email, 'password': pwd},
            timeout=5
        )

        print(f"Status: {response.status_code}")
        result = response.json()

        if result.get('success'):
            print(f"SUCCESS - User: {result['user']['username']}")
        else:
            print(f"FAILED - {result.get('error')} ({result.get('code')})")

    except Exception as e:
        print(f"ERROR: {e}")

print("\n" + "="*60)
