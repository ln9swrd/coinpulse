# -*- coding: utf-8 -*-
"""
Initialize Enterprise Inquiries Table
Enterprise 상담 신청 테이블 초기화
"""

from backend.database.connection import engine, Base, init_database
from backend.models.enterprise_inquiry import EnterpriseInquiry

def init_enterprise_inquiries_table():
    """Enterprise Inquiries 테이블 생성"""
    try:
        # Initialize database connection first
        init_database(create_tables=False)

        # Create table
        Base.metadata.create_all(engine, tables=[EnterpriseInquiry.__table__])
        print("[OK] Enterprise inquiries table created successfully")

        # Verify table exists
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        if 'enterprise_inquiries' in tables:
            print(f"[OK] Table verified: enterprise_inquiries")

            # Show table schema
            columns = inspector.get_columns('enterprise_inquiries')
            print(f"[INFO] Columns: {', '.join([col['name'] for col in columns])}")
        else:
            print("[ERROR] Table not found: enterprise_inquiries")

    except Exception as e:
        print(f"[ERROR] Failed to create table: {str(e)}")
        raise

if __name__ == '__main__':
    print("=" * 60)
    print("Initialize Enterprise Inquiries Table")
    print("=" * 60)
    init_enterprise_inquiries_table()
    print("=" * 60)
    print("[DONE] Initialization complete")
    print("=" * 60)
