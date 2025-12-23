import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_db_session
from sqlalchemy import text

with get_db_session() as session:
    query = text("""
        SELECT
            COUNT(*) as total,
            MIN(sent_at) as first_date,
            MAX(sent_at) as last_date,
            COUNT(CASE WHEN status = 'win' THEN 1 END) as wins,
            COUNT(CASE WHEN status = 'lose' THEN 1 END) as losses
        FROM surge_alerts
    """)

    result = session.execute(query).first()

    print('=== surge_alerts 전체 데이터 ===')
    print(f'총 레코드: {result.total}건')
    print(f'첫 날짜: {result.first_date}')
    print(f'마지막 날짜: {result.last_date}')
    print(f'Win: {result.wins}건')
    print(f'Lose: {result.losses}건')
    if result.total > 0:
        print(f'적중률: {result.wins / result.total * 100:.1f}%')
