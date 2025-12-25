# -*- coding: utf-8 -*-
"""
Close Pending Surge Signals

종료 조건을 확인하고 pending 상태인 신호들을 종료 처리합니다:
- 48시간 경과 시 종료
- 피크 대비 3% 이상 하락 시 종료
- 진입가 대비 2% 이상 하락 시 종료
"""

import os
import sys
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from sqlalchemy import text
from backend.database.connection import get_db_session


class PendingSignalCloser:
    """Pending 상태 신호 종료 처리"""

    def __init__(self):
        self.upbit_api_base = "https://api.upbit.com/v1"
        self.outcome_hours = 48  # 48시간 기준

    def get_pending_signals(self) -> List[Dict]:
        """pending 상태인 신호 조회"""
        with get_db_session() as session:
            query = text("""
                SELECT id, market, coin, entry_price, target_price, peak_price, sent_at
                FROM surge_alerts
                WHERE status = 'pending'
                ORDER BY sent_at DESC
            """)
            result = session.execute(query)
            return [dict(row._mapping) for row in result]

    def get_current_price(self, market: str) -> Optional[int]:
        """현재가 조회"""
        try:
            response = requests.get(
                f"{self.upbit_api_base}/ticker",
                params={'markets': market},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data:
                    return int(data[0].get('trade_price', 0))
            return None
        except Exception as e:
            print(f"[ERROR] {market}: Failed to get price - {e}")
            return None

    def fetch_candles_since(self, market: str, since_date: datetime) -> List[Dict]:
        """특정 시점 이후의 모든 캔들 데이터 조회"""
        all_candles = []
        current_time = datetime.now()

        # 필요한 캔들 수 계산 (분 단위)
        minutes_elapsed = int((current_time - since_date).total_seconds() / 60)
        chunks_needed = (minutes_elapsed // 200) + 1

        print(f"  [INFO] Fetching {minutes_elapsed} minutes of data ({chunks_needed} chunks)...")

        for chunk in range(min(chunks_needed, 22)):  # 최대 4400분 (약 3일)
            try:
                response = requests.get(
                    f"{self.upbit_api_base}/candles/minutes/1",
                    params={
                        'market': market,
                        'count': 200,
                        'to': (since_date + timedelta(minutes=(chunk + 1) * 200)).strftime('%Y-%m-%d %H:%M:%S')
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    candles = response.json()
                    if candles:
                        all_candles.extend(candles)

                time.sleep(0.1)  # Rate limit

            except Exception as e:
                print(f"  [ERROR] Chunk {chunk} failed: {e}")
                continue

        print(f"  [OK] Fetched {len(all_candles)} candles")
        return all_candles

    def find_peak_and_exit(self, market: str, entry_price: int, entry_time: datetime,
                          current_price: int) -> Dict:
        """피크가격과 종료가격 찾기"""

        # 진입 이후 캔들 데이터 조회
        candles = self.fetch_candles_since(market, entry_time)

        if not candles:
            return {
                'peak_price': max(entry_price, current_price),
                'exit_price': current_price,
                'close_reason': 'No candle data available'
            }

        # 피크 가격 찾기
        peak_price = entry_price
        for candle in candles:
            high = int(candle.get('high_price', 0))
            if high > peak_price:
                peak_price = high

        # 현재가도 고려
        peak_price = max(peak_price, current_price)

        # 종료 사유 판단
        hours_elapsed = (datetime.now() - entry_time).total_seconds() / 3600

        if hours_elapsed >= self.outcome_hours:
            close_reason = f'Expired ({self.outcome_hours}h)'
        elif peak_price > entry_price and current_price < peak_price * 0.97:
            close_reason = 'Drop from peak (>3%)'
        elif current_price < entry_price * 0.98:
            close_reason = 'Below entry price (>2%)'
        else:
            close_reason = f'Active ({hours_elapsed:.1f}h elapsed)'

        return {
            'peak_price': peak_price,
            'exit_price': current_price,
            'close_reason': close_reason
        }

    def update_signal(self, signal_id: int, peak_price: int, exit_price: int,
                     close_reason: str, entry_price: int):
        """신호 업데이트"""

        # 손익 계산
        profit_pct = ((exit_price - entry_price) / entry_price) * 100

        # 상태 결정
        if 'Expired' in close_reason or 'Drop' in close_reason or 'Below' in close_reason:
            if profit_pct > 0:
                status = 'win'
            else:
                status = 'lose'
        else:
            status = 'pending'  # 아직 종료 조건 미달
            return False  # 업데이트하지 않음

        with get_db_session() as session:
            query = text("""
                UPDATE surge_alerts
                SET peak_price = :peak_price,
                    exit_price = :exit_price,
                    close_reason = :close_reason,
                    status = :status,
                    closed_at = NOW()
                WHERE id = :signal_id
            """)

            session.execute(query, {
                'signal_id': signal_id,
                'peak_price': peak_price,
                'exit_price': exit_price,
                'close_reason': close_reason,
                'status': status
            })
            session.commit()

        return True

    def close_pending_signals(self):
        """Pending 신호 일괄 종료 처리"""
        print()
        print("=" * 80)
        print("Close Pending Surge Signals")
        print("=" * 80)
        print()

        # Pending 신호 조회
        signals = self.get_pending_signals()
        print(f"[INFO] Found {len(signals)} pending signals")
        print()

        if not signals:
            print("[INFO] No pending signals to process")
            return

        closed_count = 0
        active_count = 0

        for signal in signals:
            signal_id = signal['id']
            market = signal['market']
            coin = signal['coin']
            entry_price = signal['entry_price']
            entry_time = signal['sent_at']

            hours_elapsed = (datetime.now() - entry_time).total_seconds() / 3600

            print(f"[INFO] Processing {coin} (ID: {signal_id}, {hours_elapsed:.1f}h ago)...")

            # 현재가 조회
            current_price = self.get_current_price(market)
            if not current_price:
                print(f"  [SKIP] Failed to get current price")
                continue

            # 피크 및 종료가격 찾기
            outcome = self.find_peak_and_exit(market, entry_price, entry_time, current_price)

            peak_price = outcome['peak_price']
            exit_price = outcome['exit_price']
            close_reason = outcome['close_reason']

            # 손익 계산
            profit_pct = ((exit_price - entry_price) / entry_price) * 100
            peak_pct = ((peak_price - entry_price) / entry_price) * 100

            print(f"  Entry: {entry_price:,}")
            print(f"  Peak: {peak_price:,} (+{peak_pct:.1f}%)")
            print(f"  Exit: {exit_price:,} ({profit_pct:+.1f}%)")
            print(f"  Reason: {close_reason}")

            # 신호 업데이트
            updated = self.update_signal(signal_id, peak_price, exit_price,
                                        close_reason, entry_price)

            if updated:
                status = 'win' if profit_pct > 0 else 'lose'
                print(f"  [OK] Closed as '{status}'")
                closed_count += 1
            else:
                print(f"  [SKIP] Still active")
                active_count += 1

            print()
            time.sleep(0.3)  # Rate limit

        print("=" * 80)
        print("Summary")
        print("=" * 80)
        print(f"Total processed: {len(signals)}")
        print(f"Closed: {closed_count}")
        print(f"Still active: {active_count}")
        print()


def main():
    print()
    print("=" * 80)
    print("CoinPulse - Close Pending Surge Signals")
    print("=" * 80)
    print()

    closer = PendingSignalCloser()
    closer.close_pending_signals()


if __name__ == "__main__":
    print(f"[START] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    main()
    print()
    print(f"[DONE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
