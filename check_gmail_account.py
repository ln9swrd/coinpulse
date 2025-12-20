#!/usr/bin/env python
# -*- coding: utf-8 -*-
import psycopg2

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/coinpulse')
cur = conn.cursor()

# Check if ln9swrd@gmail.com exists
cur.execute("SELECT email, username, is_active, created_at FROM users WHERE email = 'ln9swrd@gmail.com'")
row = cur.fetchone()

print("="*60)
print("Checking ln9swrd@gmail.com account")
print("="*60)
print(f"Account exists: {row is not None}")

if row:
    print(f"Email: {row[0]}")
    print(f"Username: {row[1]}")
    print(f"Active: {row[2]}")
    print(f"Created: {row[3]}")
else:
    print("\nAccount NOT found in database!")
    print("\nYou need to create this account first:")
    print("1. Go to http://localhost:8080/signup.html")
    print("2. Register with ln9swrd@gmail.com")

cur.close()
conn.close()
print("="*60)
