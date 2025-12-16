"""
로컬 PostgreSQL 데이터베이스 설정

개발 환경용 PostgreSQL 데이터베이스를 생성하고 초기화합니다.
"""
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

# PostgreSQL 연결 정보
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "postgres"  # 기본 비밀번호 (변경 필요시 수정)
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
DATABASE_NAME = "coinpulse"

def create_database():
    """coinpulse 데이터베이스 생성"""
    try:
        # postgres 데이터베이스에 연결 (기본 DB)
        print(f"[1/4] Connecting to PostgreSQL server...")
        conn = psycopg2.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # 데이터베이스 존재 확인
        print(f"[2/4] Checking if database '{DATABASE_NAME}' exists...")
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DATABASE_NAME,)
        )
        exists = cursor.fetchone()

        if exists:
            print(f"[INFO] Database '{DATABASE_NAME}' already exists")
        else:
            # 데이터베이스 생성
            print(f"[3/4] Creating database '{DATABASE_NAME}'...")
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(DATABASE_NAME)
                )
            )
            print(f"[SUCCESS] Database '{DATABASE_NAME}' created successfully")

        cursor.close()
        conn.close()

        # DATABASE_URL 생성
        database_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{DATABASE_NAME}"

        print(f"\n[4/4] Database setup complete!")
        print(f"\n{'='*60}")
        print(f"DATABASE_URL:")
        print(f"  {database_url}")
        print(f"{'='*60}")
        print(f"\n다음 단계:")
        print(f"1. .env 파일에 다음 내용 추가:")
        print(f"   DATABASE_URL={database_url}")
        print(f"\n2. 또는 환경 변수로 설정:")
        print(f"   set DATABASE_URL={database_url}")
        print(f"\n3. 서버 실행:")
        print(f"   python simple_dual_server.py")
        print(f"{'='*60}\n")

        return database_url

    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] PostgreSQL 연결 실패:")
        print(f"  {e}")
        print(f"\n해결 방법:")
        print(f"1. PostgreSQL 서비스가 실행 중인지 확인:")
        print(f"   sc query postgresql-x64-16")
        print(f"\n2. 비밀번호가 '{POSTGRES_PASSWORD}'가 아니라면:")
        print(f"   이 스크립트의 POSTGRES_PASSWORD 변수 수정")
        print(f"\n3. PostgreSQL 서비스 시작:")
        print(f"   net start postgresql-x64-16")
        return None

    except Exception as e:
        print(f"\n[ERROR] 예상치 못한 오류:")
        print(f"  {e}")
        return None


def test_connection(database_url):
    """데이터베이스 연결 테스트"""
    try:
        print(f"\n[TEST] Testing database connection...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"[SUCCESS] PostgreSQL version: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Connection test failed: {e}")
        return False


def main():
    print("\n" + "="*60)
    print("CoinPulse 로컬 PostgreSQL 설정")
    print("="*60 + "\n")

    # 데이터베이스 생성
    database_url = create_database()

    if database_url:
        # 연결 테스트
        if test_connection(database_url):
            print(f"\n[SUCCESS] 로컬 PostgreSQL 설정 완료!")
            print(f"\n이제 서버를 실행할 수 있습니다:")
            print(f"  set DATABASE_URL={database_url} && python simple_dual_server.py")
        else:
            print(f"\n[WARNING] 데이터베이스는 생성되었지만 연결 테스트 실패")
    else:
        print(f"\n[FAILED] 데이터베이스 설정 실패")


if __name__ == "__main__":
    main()
