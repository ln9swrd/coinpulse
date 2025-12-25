# -*- coding: utf-8 -*-
"""
기존 surge_alerts 데이터에 exit_price 업데이트 스크립트

종료된 신호들(closed_at이 있는 경우)의 exit_price를 업데이트합니다.
exit_price가 없는 경우 현재가 또는 target_price를 사용합니다.
"""

import os
import sys
import requests
import time
from datetime import datetime

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from backend.database.connection import get_db_session


def get_current_price(market):
    """
    Upbit API에서 현재가 조회

    Args:
        market (str): 마켓 코드 (예: KRW-BTC)

    Returns:
        int: 현재가 (원), 실패 시 None
    """
    try:
        response = requests.get(
            'https://api.upbit.com/v1/ticker',
            params={'markets': market},
            timeout=5
        )
        if response.status_code == 200:
            ticker_data = response.json()
            if ticker_data and len(ticker_data) > 0:
                return int(ticker_data[0]['trade_price'])
    except Exception as e:
        print(f"[ERROR] Failed to get price for {market}: {e}")
    return None


def update_exit_prices_for_closed_signals():
    """
    종료된 신호들의 exit_price 업데이트
    """
    print("=" * 80)
    print("기존 Surge Alerts 데이터 Exit Price 업데이트")
    print("=" * 80)
    print()

    try:
        with get_db_session() as session:
            # 1. 종료된 신호 중 exit_price가 없는 신호 조회
            query = text("""
                SELECT id, market, entry_price, target_price, closed_at, status
                FROM surge_alerts
                WHERE (closed_at IS NOT NULL OR status = 'closed')
                  AND exit_price IS NULL
                ORDER BY closed_at DESC
            """)

            result = session.execute(query)
            alerts = result.fetchall()

            total_count = len(alerts)
            print(f"[INFO] Closed signals without exit_price: {total_count} items")
            print()

            if total_count == 0:
                print("[OK] No data to update.")
                return

            # 2. 각 신호의 exit_price 업데이트
            updated_count = 0
            failed_count = 0

            for idx, alert in enumerate(alerts, 1):
                alert_id = alert[0]
                market = alert[1]
                entry_price = alert[2]
                target_price = alert[3]
                closed_at = alert[4]
                status = alert[5]

                print(f"[{idx}/{total_count}] Alert #{alert_id} ({market})")

                # exit_price 결정 우선순위:
                # 1. 현재가 (Upbit API)
                # 2. target_price
                # 3. entry_price

                exit_price = None

                # 1. 현재가 조회 시도
                if market:
                    exit_price = get_current_price(market)
                    if exit_price:
                        print(f"   → 현재가 사용: {exit_price:,}원")
                    time.sleep(0.1)  # API rate limit 고려

                # 2. target_price 사용
                if exit_price is None and target_price:
                    exit_price = target_price
                    print(f"   → Target Price 사용: {exit_price:,}원")

                # 3. entry_price 사용
                if exit_price is None and entry_price:
                    exit_price = entry_price
                    print(f"   → Entry Price 사용: {exit_price:,}원")

                # 4. 여전히 없으면 스킵
                if exit_price is None:
                    print(f"   [SKIP] Cannot determine exit price")
                    failed_count += 1
                    continue

                # DB 업데이트
                try:
                    update_query = text("""
                        UPDATE surge_alerts
                        SET exit_price = :exit_price
                        WHERE id = :alert_id
                    """)

                    session.execute(update_query, {
                        'alert_id': alert_id,
                        'exit_price': exit_price
                    })

                    updated_count += 1
                    print(f"   [OK] Updated")

                except Exception as update_error:
                    print(f"   [ERROR] Update failed: {update_error}")
                    failed_count += 1

                print()

            # 3. 변경사항 커밋
            session.commit()

            print("=" * 80)
            print(f"[COMPLETE] Update finished")
            print(f"   - Total: {total_count} items")
            print(f"   - Success: {updated_count} items")
            print(f"   - Failed: {failed_count} items")
            print("=" * 80)

    except Exception as e:
        print(f"\n[ERROR] Exception occurred: {e}")
        import traceback
        traceback.print_exc()


def update_exit_prices_for_all_with_target():
    """
    모든 신호 중 exit_price가 없고 target_price가 있는 경우 target_price를 exit_price로 설정
    """
    print()
    print("=" * 80)
    print("Backfill Exit Price with Target Price (All signals)")
    print("=" * 80)
    print()

    try:
        with get_db_session() as session:
            query = text("""
                UPDATE surge_alerts
                SET exit_price = target_price
                WHERE exit_price IS NULL
                  AND target_price IS NOT NULL
            """)

            result = session.execute(query)
            session.commit()

            updated_count = result.rowcount
            print(f"[OK] Updated exit_price with target_price for {updated_count} signals.")
            print("=" * 80)

    except Exception as e:
        print(f"[ERROR] Exception occurred: {e}")


if __name__ == "__main__":
    print("\n[START] Exit Price Update Script")
    print(f"[TIME] Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Update exit_price for closed signals (prioritize current price)
    update_exit_prices_for_closed_signals()

    # 2. Backfill exit_price with target_price for remaining signals
    update_exit_prices_for_all_with_target()

    print()
    print(f"[TIME] End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("[DONE] Script completed")
