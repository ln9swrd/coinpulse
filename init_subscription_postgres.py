"""
PostgreSQL 구독 테이블 직접 생성 스크립트
"""
import os
from sqlalchemy import create_engine, text

# PostgreSQL 연결 (직접 지정)
DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/coinpulse'

print("=" * 70)
print("PostgreSQL 구독 테이블 생성")
print("=" * 70)
print(f"Database: {DATABASE_URL}")

# Engine 생성
engine = create_engine(DATABASE_URL, echo=True)

# SQL 쿼리
create_subscriptions_table = """
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    billing_period VARCHAR(50) NOT NULL DEFAULT 'monthly',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    amount INTEGER NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'KRW',
    started_at TIMESTAMP,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    trial_ends_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
"""

create_transactions_table = """
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL,
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    amount INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'KRW',
    payment_method VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    payment_key VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transactions_subscription_id ON transactions(subscription_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_transaction_id ON transactions(transaction_id);
"""

try:
    with engine.connect() as conn:
        # 구독 테이블 생성
        print("\n[1/2] Creating subscriptions table...")
        conn.execute(text(create_subscriptions_table))
        conn.commit()
        print("[OK] Subscriptions table created")
        
        # 트랜잭션 테이블 생성
        print("\n[2/2] Creating transactions table...")
        conn.execute(text(create_transactions_table))
        conn.commit()
        print("[OK] Transactions table created")
        
        # 확인
        print("\n[3/3] Verifying tables...")
        result = conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' "
            "AND tablename IN ('subscriptions', 'transactions')"
        ))
        tables = [row[0] for row in result]
        print(f"[OK] Found tables: {', '.join(tables)}")
        
        print("\n" + "=" * 70)
        print("PostgreSQL 구독 테이블 생성 완료!")
        print("=" * 70)
        
except Exception as e:
    print(f"\n[ERROR] Failed to create tables: {e}")
    raise
