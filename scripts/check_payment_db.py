#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check payment tables in database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_db_session
from sqlalchemy import text

session = get_db_session()

# Check if transactions table exists
result = session.execute(text("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='public'
    AND table_name IN ('transactions', 'user_subscriptions', 'billing_keys')
    ORDER BY table_name
"""))
tables = [row[0] for row in result]

print('\n=== 결제 관련 테이블 ===')
for table in tables:
    print(f'✅ {table}')

if not tables:
    print('⚠️  결제 관련 테이블이 없습니다!')

# Check transactions count
if 'transactions' in tables:
    count = session.execute(text('SELECT COUNT(*) FROM transactions')).scalar()
    print(f'\n📊 거래 내역 (transactions): {count}개')

    # Get recent transactions
    if count > 0:
        result = session.execute(text("""
            SELECT id, user_id, transaction_id, amount, status, payment_method, created_at
            FROM transactions
            ORDER BY created_at DESC
            LIMIT 5
        """))
        print('\n최근 5개 거래:')
        for row in result:
            status_str = str(row[4]) if hasattr(row[4], 'value') else row[4]
            method_str = str(row[5]) if hasattr(row[5], 'value') else row[5]
            print(f'  ID:{row[0]} | User:{row[1]} | TxID:{row[2]} | Amount:{row[3]:,}원 | Status:{status_str} | Method:{method_str} | Date:{row[6]}')
    else:
        print('  ℹ️  거래 내역이 없습니다.')

# Check subscriptions count
if 'user_subscriptions' in tables:
    count = session.execute(text('SELECT COUNT(*) FROM user_subscriptions')).scalar()
    print(f'\n📊 구독 내역 (user_subscriptions): {count}개')

    # Get recent subscriptions
    if count > 0:
        result = session.execute(text("""
            SELECT id, user_id, plan, billing_period, status, amount, started_at
            FROM user_subscriptions
            ORDER BY created_at DESC
            LIMIT 5
        """))
        print('\n최근 5개 구독:')
        for row in result:
            print(f'  ID:{row[0]} | User:{row[1]} | Plan:{row[2]} | Period:{row[3]} | Status:{row[4]} | Amount:{row[5]:,}원 | Started:{row[6]}')
    else:
        print('  ℹ️  구독 내역이 없습니다.')

# Check billing_keys count
if 'billing_keys' in tables:
    count = session.execute(text('SELECT COUNT(*) FROM billing_keys')).scalar()
    print(f'\n📊 빌링키 (billing_keys): {count}개')

    if count > 0:
        result = session.execute(text("""
            SELECT id, user_id, card_company, card_number, status, created_at
            FROM billing_keys
            ORDER BY created_at DESC
            LIMIT 5
        """))
        print('\n최근 5개 빌링키:')
        for row in result:
            print(f'  ID:{row[0]} | User:{row[1]} | Card:{row[2]} {row[3]} | Status:{row[4]} | Date:{row[5]}')
    else:
        print('  ℹ️  빌링키가 없습니다.')

session.close()
