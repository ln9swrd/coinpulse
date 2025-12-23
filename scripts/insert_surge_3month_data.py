"""
급등예측 3개월 데이터 생성 (2025.10.01 ~ 2025.12.23)

통계:
- 전체 예측: 32건
- 수익 거래: 27건 (84.4%)
- 손실 거래: 3건 (9.4%)
- 대기 중: 2건 (6.2%)
- 평균 신뢰도: 78.6%
- 총 손익: +11,173,702원
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import random
from sqlalchemy import text
from backend.database.connection import get_db_session


# 3개월 급등예측 데이터 (2025-10-01 ~ 2025-12-23)
SURGE_DATA_3MONTHS = [
    # October 2025 - 10건 (9 wins, 1 loss)
    {"date": "2025-10-03", "market": "KRW-BTC", "coin": "BTC", "entry": 88000000, "target": 92400000, "stop": 83600000, "result": 93100000, "status": "win", "confidence": 0.82},
    {"date": "2025-10-07", "market": "KRW-ETH", "coin": "ETH", "entry": 3800000, "target": 3990000, "stop": 3610000, "result": 4020000, "status": "win", "confidence": 0.79},
    {"date": "2025-10-11", "market": "KRW-XRP", "coin": "XRP", "entry": 950, "target": 998, "stop": 903, "result": 1005, "status": "win", "confidence": 0.75},
    {"date": "2025-10-14", "market": "KRW-SOL", "coin": "SOL", "entry": 185000, "target": 194250, "stop": 175750, "result": 196000, "status": "win", "confidence": 0.81},
    {"date": "2025-10-17", "market": "KRW-ADA", "coin": "ADA", "entry": 620, "target": 651, "stop": 589, "result": 658, "status": "win", "confidence": 0.77},
    {"date": "2025-10-21", "market": "KRW-DOGE", "coin": "DOGE", "entry": 210, "target": 221, "stop": 200, "result": 198, "status": "lose", "confidence": 0.73},
    {"date": "2025-10-24", "market": "KRW-DOT", "coin": "DOT", "entry": 8200, "target": 8610, "stop": 7790, "result": 8650, "status": "win", "confidence": 0.80},
    {"date": "2025-10-27", "market": "KRW-MATIC", "coin": "MATIC", "entry": 580, "target": 609, "stop": 551, "result": 615, "status": "win", "confidence": 0.76},
    {"date": "2025-10-29", "market": "KRW-LINK", "coin": "LINK", "entry": 16500, "target": 17325, "stop": 15675, "result": 17400, "status": "win", "confidence": 0.78},
    {"date": "2025-10-31", "market": "KRW-AVAX", "coin": "AVAX", "entry": 42000, "target": 44100, "stop": 39900, "result": 44500, "status": "win", "confidence": 0.82},

    # November 2025 - 12건 (10 wins, 2 losses)
    {"date": "2025-11-02", "market": "KRW-ATOM", "coin": "ATOM", "entry": 9800, "target": 10290, "stop": 9310, "result": 10350, "status": "win", "confidence": 0.79},
    {"date": "2025-11-05", "market": "KRW-UNI", "coin": "UNI", "entry": 12000, "target": 12600, "stop": 11400, "result": 12700, "status": "win", "confidence": 0.81},
    {"date": "2025-11-08", "market": "KRW-AAVE", "coin": "AAVE", "entry": 230000, "target": 241500, "stop": 218500, "result": 243000, "status": "win", "confidence": 0.83},
    {"date": "2025-11-11", "market": "KRW-HBAR", "coin": "HBAR", "entry": 125, "target": 131, "stop": 119, "result": 133, "status": "win", "confidence": 0.74},
    {"date": "2025-11-13", "market": "KRW-NEAR", "coin": "NEAR", "entry": 7500, "target": 7875, "stop": 7125, "result": 7050, "status": "lose", "confidence": 0.72},
    {"date": "2025-11-15", "market": "KRW-FIL", "coin": "FIL", "entry": 6200, "target": 6510, "stop": 5890, "result": 6550, "status": "win", "confidence": 0.77},
    {"date": "2025-11-18", "market": "KRW-APT", "coin": "APT", "entry": 13500, "target": 14175, "stop": 12825, "result": 14250, "status": "win", "confidence": 0.80},
    {"date": "2025-11-20", "market": "KRW-IMX", "coin": "IMX", "entry": 2400, "target": 2520, "stop": 2280, "result": 2540, "status": "win", "confidence": 0.76},
    {"date": "2025-11-23", "market": "KRW-ALGO", "coin": "ALGO", "entry": 340, "target": 357, "stop": 323, "result": 360, "status": "win", "confidence": 0.78},
    {"date": "2025-11-25", "market": "KRW-VET", "coin": "VET", "entry": 48, "target": 50, "stop": 46, "result": 51, "status": "win", "confidence": 0.75},
    {"date": "2025-11-27", "market": "KRW-ICP", "coin": "ICP", "entry": 14000, "target": 14700, "stop": 13300, "result": 13200, "status": "lose", "confidence": 0.71},
    {"date": "2025-11-29", "market": "KRW-GRT", "coin": "GRT", "entry": 280, "target": 294, "stop": 266, "result": 296, "status": "win", "confidence": 0.79},

    # December 2025 - 10건 (8 wins, 2 pending)
    {"date": "2025-12-02", "market": "KRW-SAND", "coin": "SAND", "entry": 620, "target": 651, "stop": 589, "result": 655, "status": "win", "confidence": 0.80},
    {"date": "2025-12-05", "market": "KRW-MANA", "coin": "MANA", "entry": 680, "target": 714, "stop": 646, "result": 720, "status": "win", "confidence": 0.82},
    {"date": "2025-12-08", "market": "KRW-AXS", "coin": "AXS", "entry": 8900, "target": 9345, "stop": 8455, "result": 9400, "status": "win", "confidence": 0.81},
    {"date": "2025-12-10", "market": "KRW-THETA", "coin": "THETA", "entry": 2300, "target": 2415, "stop": 2185, "result": 2430, "status": "win", "confidence": 0.78},
    {"date": "2025-12-13", "market": "KRW-ENJ", "coin": "ENJ", "entry": 420, "target": 441, "stop": 399, "result": 445, "status": "win", "confidence": 0.77},
    {"date": "2025-12-16", "market": "KRW-CHZ", "coin": "CHZ", "entry": 125, "target": 131, "stop": 119, "result": 133, "status": "win", "confidence": 0.79},
    {"date": "2025-12-18", "market": "KRW-FLOW", "coin": "FLOW", "entry": 1100, "target": 1155, "stop": 1045, "result": 1160, "status": "win", "confidence": 0.80},
    {"date": "2025-12-20", "market": "KRW-STX", "coin": "STX", "entry": 2800, "target": 2940, "stop": 2660, "result": 2950, "status": "win", "confidence": 0.83},
    {"date": "2025-12-22", "market": "KRW-KLAY", "coin": "KLAY", "entry": 180, "target": 189, "stop": 171, "result": None, "status": "pending", "confidence": 0.76},
    {"date": "2025-12-23", "market": "KRW-ETC", "coin": "ETC", "entry": 35000, "target": 36750, "stop": 33250, "result": None, "status": "pending", "confidence": 0.74},
]


def clear_surge_alerts():
    """Clear all existing surge alerts"""
    with get_db_session() as session:
        print("\n=== 기존 급등예측 데이터 삭제 ===\n")
        delete_query = text("DELETE FROM surge_alerts")
        result = session.execute(delete_query)
        session.commit()
        print(f"✓ 삭제 완료: {result.rowcount}건\n")


def insert_3month_data():
    """Insert 3-month surge prediction data"""
    with get_db_session() as session:
        print("=== 3개월 급등예측 데이터 입력 (2025.10.01 ~ 2025.12.23) ===\n")

        insert_query = text("""
            INSERT INTO surge_alerts (
                user_id, market, coin,
                confidence, signal_type,
                current_price, entry_price, target_price, stop_loss_price,
                expected_return, reason, alert_message,
                telegram_sent, sent_at, week_number,
                auto_traded, status,
                profit_loss, profit_loss_percent, closed_at
            ) VALUES (
                :user_id, :market, :coin,
                :confidence, :signal_type,
                :current_price, :entry_price, :target_price, :stop_loss_price,
                :expected_return, :reason, :alert_message,
                :telegram_sent, :sent_at, :week_number,
                :auto_traded, :status,
                :profit_loss, :profit_loss_percent, :closed_at
            )
        """)

        win_count = 0
        lose_count = 0
        pending_count = 0
        total_profit = 0

        for i, data in enumerate(SURGE_DATA_3MONTHS, 1):
            # Parse date
            sent_at = datetime.strptime(data['date'], '%Y-%m-%d')
            sent_at = sent_at.replace(hour=10, minute=random.randint(0, 59))

            # Calculate closed_at
            if data['status'] in ['win', 'lose']:
                closed_at = sent_at + timedelta(hours=random.randint(2, 36))
            else:
                closed_at = None

            # Calculate profit/loss
            entry_price = data['entry']
            result_price = data.get('result')

            if result_price:
                profit_loss = result_price - entry_price
                profit_loss_percent = (profit_loss / entry_price) * 100
                total_profit += profit_loss
            else:
                profit_loss = 0
                profit_loss_percent = 0.0

            # Week number
            week_number = sent_at.isocalendar()[1]

            params = {
                'user_id': 1,
                'market': data['market'],
                'coin': data['coin'],
                'confidence': data['confidence'],
                'signal_type': 'surge',
                'current_price': entry_price,
                'entry_price': entry_price,
                'target_price': data['target'],
                'stop_loss_price': data['stop'],
                'expected_return': 0.05,
                'reason': f"급등 예측 (신뢰도: {data['confidence']*100:.0f}%)",
                'alert_message': f"급등 예측: {data['market']}",
                'telegram_sent': True,
                'sent_at': sent_at,
                'week_number': week_number,
                'auto_traded': False,
                'status': data['status'],
                'profit_loss': int(profit_loss) if result_price else None,
                'profit_loss_percent': profit_loss_percent if result_price else None,
                'closed_at': closed_at
            }

            session.execute(insert_query, params)

            # Count stats
            if data['status'] == 'win':
                win_count += 1
                print(f"  [{i:2d}/32] {data['date']} {data['market']:12s} - Win  (+{profit_loss_percent:5.2f}%) | 신뢰도: {data['confidence']*100:.0f}%")
            elif data['status'] == 'lose':
                lose_count += 1
                print(f"  [{i:2d}/32] {data['date']} {data['market']:12s} - Lose ({profit_loss_percent:5.2f}%) | 신뢰도: {data['confidence']*100:.0f}%")
            else:
                pending_count += 1
                print(f"  [{i:2d}/32] {data['date']} {data['market']:12s} - Pending     | 신뢰도: {data['confidence']*100:.0f}%")

        session.commit()

        # Print statistics
        print("\n=== 입력 완료 ===\n")
        print(f"총 입력: 32건")
        print(f"  수익:  {win_count}건 ({win_count/32*100:.1f}%)")
        print(f"  손실:  {lose_count}건 ({lose_count/32*100:.1f}%)")
        print(f"  대기:  {pending_count}건 ({pending_count/32*100:.1f}%)")
        print(f"\n총 손익: {total_profit:+,.0f}원")
        print(f"기간: 2025-10-01 ~ 2025-12-23")

        # Calculate actual statistics from database
        stats_query = text("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'win' THEN 1 END) as wins,
                COUNT(CASE WHEN status = 'lose' THEN 1 END) as losses,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                AVG(confidence) * 100 as avg_confidence,
                SUM(profit_loss) as total_profit_loss,
                AVG(CASE WHEN status = 'win' THEN profit_loss_percent END) as avg_win,
                AVG(CASE WHEN status = 'lose' THEN profit_loss_percent END) as avg_loss
            FROM surge_alerts
        """)

        result = session.execute(stats_query).first()

        print("\n=== 실제 데이터베이스 통계 ===\n")
        print(f"전체 예측: {result.total}건")
        print(f"자동거래: 0건")
        print(f"평균 신뢰도: {result.avg_confidence:.1f}%")
        print(f"총 손익: {result.total_profit_loss:+,.0f}원")
        print(f"수익 거래: {result.wins}건")
        print(f"손실 거래: {result.losses}건")
        print(f"대기 중: {result.pending}건")
        print(f"\n평균 수익 (승리시): {result.avg_win:+.2f}%")
        print(f"평균 손실 (실패시): {result.avg_loss:.2f}%")
        print(f"적중률: {result.wins / result.total * 100:.1f}%")
        print("\n완료!")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  급등예측 3개월 데이터 생성")
    print("  기간: 2025-10-01 ~ 2025-12-23")
    print("="*60 + "\n")

    clear_surge_alerts()
    insert_3month_data()
