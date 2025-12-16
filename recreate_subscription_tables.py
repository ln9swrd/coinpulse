"""
PostgreSQL Enum 타입 확인 및 테스트
"""
from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/coinpulse'
engine = create_engine(DATABASE_URL)

print("=" * 70)
print("Enum 타입 확인")
print("=" * 70)

with engine.connect() as conn:
    # Enum 타입 확인
    result = conn.execute(text("""
        SELECT t.typname, e.enumlabel
        FROM pg_type t 
        JOIN pg_enum e ON t.oid = e.enumtypid
        WHERE t.typname LIKE '%subscription%' OR t.typname LIKE '%payment%'
        ORDER BY t.typname, e.enumsortorder
    """))
    
    enums = {}
    for row in result:
        if row[0] not in enums:
            enums[row[0]] = []
        enums[row[0]].append(row[1])
    
    if enums:
        for enum_name, values in enums.items():
            print(f"\n{enum_name}:")
            for v in values:
                print(f"  - {v}")
    else:
        print("\n[INFO] Enum 타입이 없습니다.")

print("\n" + "=" * 70)
print("테이블 삭제 및 재생성 (VARCHAR 사용)")
print("=" * 70)

with engine.connect() as conn:
    # 기존 테이블 삭제
    print("\n[1] 기존 테이블 삭제...")
    conn.execute(text("DROP TABLE IF EXISTS transactions CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS subscriptions CASCADE"))
    
    # Enum 타입 삭제
    print("[2] Enum 타입 삭제...")
    conn.execute(text("DROP TYPE IF EXISTS subscriptionplan CASCADE"))
    conn.execute(text("DROP TYPE IF EXISTS billingperiod CASCADE"))
    conn.execute(text("DROP TYPE IF EXISTS subscriptionstatus CASCADE"))
    conn.execute(text("DROP TYPE IF EXISTS paymentstatus CASCADE"))
    conn.execute(text("DROP TYPE IF EXISTS paymentmethod CASCADE"))
    
    conn.commit()
    print("[OK] 기존 데이터 삭제 완료")
    
    # 테이블 재생성 (VARCHAR 사용)
    print("\n[3] subscriptions 테이블 생성...")
    conn.execute(text("""
        CREATE TABLE subscriptions (
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
        )
    """))
    
    conn.execute(text("CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id)"))
    print("[OK] subscriptions 테이블 생성 완료")
    
    print("\n[4] transactions 테이블 생성...")
    conn.execute(text("""
        CREATE TABLE transactions (
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
        )
    """))
    
    conn.execute(text("CREATE INDEX idx_transactions_subscription_id ON transactions(subscription_id)"))
    conn.execute(text("CREATE INDEX idx_transactions_user_id ON transactions(user_id)"))
    conn.execute(text("CREATE INDEX idx_transactions_transaction_id ON transactions(transaction_id)"))
    conn.commit()
    print("[OK] transactions 테이블 생성 완료")

print("\n" + "=" * 70)
print("완료!")
print("=" * 70)
