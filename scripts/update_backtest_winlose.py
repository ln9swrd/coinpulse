"""
백테스트 데이터의 Win/Lose 상태 업데이트

발송 시간으로부터 3일 후 가격을 확인하여 실제 Win/Lose 상태를 업데이트합니다.
"""
from datetime import datetime, timedelta
from sqlalchemy import text
from backend.database.connection import get_db_session
from backend.common import UpbitAPI, load_api_keys
import time

def update_backtest_status():
    """백테스트 데이터의 Win/Lose 업데이트"""

    # Initialize Upbit API
    access_key, secret_key = load_api_keys()
    upbit_api = UpbitAPI(access_key, secret_key)

    with get_db_session() as session:
        # Get all backtest alerts
        result = session.execute(text("""
            SELECT
                id, market, sent_at,
                entry_price, target_price, stop_loss_price
            FROM surge_alerts
            WHERE status = 'backtest'
            ORDER BY sent_at
        """))

        alerts = [dict(row._mapping) for row in result]
        print(f"\n총 {len(alerts)}개의 백테스트 알림을 처리합니다.\n")

        updated = 0
        win_count = 0
        lose_count = 0

        for i, alert in enumerate(alerts, 1):
            try:
                market = alert['market']
                sent_at = alert['sent_at']
                check_date = sent_at + timedelta(days=3)

                entry_price = alert['entry_price']
                target_price = alert['target_price']
                stop_loss_price = alert['stop_loss_price']

                print(f"[{i}/{len(alerts)}] {market} (발송: {sent_at.date()}, 체크: {check_date.date()})")

                # Get historical candle data for the check date
                # We'll check the price 3 days after sent_at
                candles = upbit_api.get_candles_days(market=market, count=200, to=check_date.strftime('%Y-%m-%dT00:00:00'))

                if not candles or len(candles) < 4:
                    print(f"  ⚠️  가격 데이터 없음 (스킵)")
                    continue

                # Get price range during 3 days after prediction
                # candles[0] = check_date (3 days after)
                # candles[1] = check_date - 1
                # candles[2] = check_date - 2
                # candles[3] = check_date - 3 (sent_at)

                # Check highest and lowest during the 3-day period
                high_prices = [float(c['high_price']) for c in candles[:4]]
                low_prices = [float(c['low_price']) for c in candles[:4]]

                max_price = max(high_prices)
                min_price = min(low_prices)

                # Determine status
                new_status = None
                profit_loss = 0
                profit_loss_percent = 0.0

                if max_price >= target_price:
                    # Target reached - WIN
                    new_status = 'win'
                    profit_loss = int(target_price - entry_price)
                    profit_loss_percent = ((target_price - entry_price) / entry_price) * 100
                    win_count += 1
                    print(f"  ✅ WIN - 최고가 {max_price:,.0f}원 >= 목표가 {target_price:,}원 (P/L: {profit_loss:+,}원 {profit_loss_percent:+.2f}%)")

                elif min_price <= stop_loss_price:
                    # Stop loss hit - LOSE
                    new_status = 'lose'
                    profit_loss = int(stop_loss_price - entry_price)
                    profit_loss_percent = ((stop_loss_price - entry_price) / entry_price) * 100
                    lose_count += 1
                    print(f"  ❌ LOSE - 최저가 {min_price:,.0f}원 <= 손절가 {stop_loss_price:,}원 (P/L: {profit_loss:+,}원 {profit_loss_percent:+.2f}%)")

                else:
                    # Neither target nor stop loss hit - mark as neutral
                    new_status = 'neutral'
                    final_price = float(candles[0]['trade_price'])
                    profit_loss = int(final_price - entry_price)
                    profit_loss_percent = ((final_price - entry_price) / entry_price) * 100
                    print(f"  ⚪ NEUTRAL - 최고 {max_price:,.0f}원 / 최저 {min_price:,.0f}원 (목표 도달 못함, P/L: {profit_loss:+,}원 {profit_loss_percent:+.2f}%)")

                # Update database
                update_query = text("""
                    UPDATE surge_alerts
                    SET
                        status = :status,
                        profit_loss = :profit_loss,
                        profit_loss_percent = :profit_loss_percent,
                        closed_at = :closed_at
                    WHERE id = :alert_id
                """)

                session.execute(update_query, {
                    'alert_id': alert['id'],
                    'status': new_status,
                    'profit_loss': profit_loss,
                    'profit_loss_percent': profit_loss_percent,
                    'closed_at': check_date
                })

                updated += 1

                # Rate limit
                time.sleep(0.15)

            except Exception as e:
                print(f"  ❌ 오류: {e}")
                continue

        # Commit all changes
        session.commit()

        print("\n" + "="*70)
        print(f"업데이트 완료!")
        print(f"  총 처리: {len(alerts)}개")
        print(f"  업데이트: {updated}개")
        print(f"  Win: {win_count}개 ({win_count/updated*100:.1f}%)")
        print(f"  Lose: {lose_count}개 ({lose_count/updated*100:.1f}%)")
        print(f"  Neutral: {updated - win_count - lose_count}개")
        print("="*70)

if __name__ == "__main__":
    update_backtest_status()
