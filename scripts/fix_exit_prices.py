# -*- coding: utf-8 -*-
"""
Fix exit prices for signals with missing data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_db_session
from backend.common import UpbitAPI, load_api_keys
from sqlalchemy import text
import time

# Initialize Upbit API
access_key, secret_key = load_api_keys()
upbit_api = UpbitAPI(access_key, secret_key)

with get_db_session() as session:
    print('=== Exit Price 수정 작업 ===\n')

    # 1. exit_price가 0이거나 NULL인 closed/lose/expired 신호들 찾기
    query = text("""
        SELECT id, market, coin, entry_price, exit_price, peak_price, status
        FROM surge_alerts
        WHERE sent_at >= '2025-10-01'
            AND status IN ('lose', 'closed', 'expired')
            AND (exit_price = 0 OR exit_price IS NULL OR peak_price = 0 OR peak_price IS NULL)
        ORDER BY sent_at DESC
    """)

    signals = session.execute(query).fetchall()

    print(f'수정 필요한 신호: {len(signals)}개\n')

    if len(signals) == 0:
        print('수정할 신호가 없습니다.')
        exit(0)

    # 2. 현재 가격으로 업데이트
    updated_count = 0
    for signal in signals:
        signal_id = signal[0]
        market = signal[1]
        coin = signal[2]
        entry_price = signal[3]
        exit_price = signal[4] or 0
        peak_price = signal[5] or 0
        status = signal[6]

        try:
            # Get current price
            current_price = upbit_api.get_current_price(market)
            if not current_price or current_price == 0:
                print(f'  ⚠️  {coin}: 현재 가격을 가져올 수 없음')
                continue

            # Update to current price if exit_price is 0
            if exit_price == 0:
                exit_price = current_price

            # Update peak_price if it's 0 (assume it reached at least entry price)
            if peak_price == 0:
                peak_price = max(entry_price, exit_price)

            # Calculate profit
            profit_pct = ((exit_price - entry_price) / entry_price * 100)

            # Determine correct status
            new_status = 'win' if profit_pct > 0 else 'lose'

            # Update signal
            update_query = text("""
                UPDATE surge_alerts
                SET exit_price = :exit_price,
                    peak_price = :peak_price,
                    status = :status
                WHERE id = :id
            """)

            session.execute(update_query, {
                'exit_price': exit_price,
                'peak_price': peak_price,
                'status': new_status,
                'id': signal_id
            })

            print(f'  ✅ {coin}: exit={exit_price:,}원, peak={peak_price:,}원, 수익={profit_pct:+.2f}%, status={new_status}')
            updated_count += 1

            # Rate limit
            time.sleep(0.1)

        except Exception as e:
            print(f'  ❌ {coin}: 오류 - {e}')
            continue

    # Commit changes
    session.commit()

    print(f'\n총 {updated_count}개 신호 수정 완료')

print('\n=== 작업 완료 ===')
