"""
Backfill Balance History Script

현재 잔고 기준으로 과거 잔고 이력을 역산하여 생성합니다.

Usage:
    python scripts/backfill_balance_history.py [user_id] [days]

    user_id: 사용자 ID (기본값: DB의 첫 번째 사용자)
    days: 역산할 일수 (기본값: 90, 0=전체 이력)

Examples:
    python scripts/backfill_balance_history.py 1 365  # 1년치
    python scripts/backfill_balance_history.py 1 0    # 전체 이력
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.common import UpbitAPI, load_api_keys
from backend.database.connection import get_db_session
from backend.database.models import HoldingsHistory
from sqlalchemy import text


def get_user_id(db):
    """Get first user ID from database"""
    result = db.execute(text("SELECT id FROM users LIMIT 1"))
    row = result.fetchone()
    if not row:
        raise Exception("No users found in database")
    return row[0]


def backfill_balance_history(user_id, days=90):
    """
    현재 잔고를 기준으로 과거 N일치 잔고 이력을 역산합니다.

    Args:
        user_id: 사용자 ID
        days: 역산할 일수 (기본: 90일)
    """
    print(f"\n[Backfill] Starting {days}-day balance history backfill for user {user_id}...")

    # Load API keys
    access_key, secret_key = load_api_keys()
    api = UpbitAPI(access_key, secret_key)

    # 1. 현재 잔고 가져오기
    print("[Backfill] Step 1/5: Fetching current accounts...")
    current_accounts = api.get_accounts()
    if not current_accounts:
        raise Exception("Failed to fetch current accounts")

    # KRW 잔고
    krw_account = next((acc for acc in current_accounts if acc['currency'] == 'KRW'), None)
    current_krw_balance = float(krw_account['balance']) if krw_account else 0
    current_krw_locked = float(krw_account['locked']) if krw_account else 0

    # 코인 보유 현황
    current_holdings = {}
    for acc in current_accounts:
        if acc['currency'] != 'KRW':
            currency = acc['currency']
            balance = float(acc['balance'])
            locked = float(acc['locked'])
            if balance > 0 or locked > 0:
                current_holdings[currency] = {
                    'balance': balance,
                    'locked': locked,
                    'amount': balance + locked,
                    'avg_buy_price': float(acc.get('avg_buy_price', 0))
                }

    print(f"  Current KRW: {current_krw_balance + current_krw_locked:,.0f}")
    print(f"  Current Holdings: {len(current_holdings)} coins")

    # 2. 과거 N일치 주문 이력 가져오기
    print(f"[Backfill] Step 2/5: Fetching {days}-day order history...")

    # 업비트 API는 한 번에 최대 100개씩만 조회 가능
    # 여러 번 호출하여 모든 이력 수집
    import time

    all_orders = []
    page = 1
    max_pages = 50  # 최대 5000개 주문 (100 * 50) - 더 많은 과거 데이터 확보

    while page <= max_pages:
        try:
            orders = api.get_orders_history(state='done', limit=100, page=page)
            if not orders or len(orders) == 0:
                break

            # days=0이면 모든 주문 가져오기 (날짜 제한 없음)
            if days == 0:
                filtered_orders = orders
            else:
                # 지정된 일수 이전 주문은 제외
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                filtered_orders = [
                    order for order in orders
                    if datetime.fromisoformat(order['created_at'].replace('Z', '+00:00')) > cutoff_date
                ]

            all_orders.extend(filtered_orders)

            if days == 0:
                print(f"  Page {page}: {len(orders)} orders (all history)")
            else:
                print(f"  Page {page}: {len(filtered_orders)}/{len(orders)} orders within {days} days")

            # days > 0이고 모든 주문이 cutoff 이전이면 중단
            if days > 0 and len(filtered_orders) < len(orders):
                print(f"  Reached cutoff date, stopping at page {page}")
                break

            page += 1

            # Rate limiting: 0.1초 대기 (초당 10회 제한 준수)
            time.sleep(0.1)

        except Exception as e:
            print(f"  Warning: Failed to fetch orders page {page}: {e}")
            break

    print(f"  Fetched {len(all_orders)} orders")

    # 3. 입출금 이력 가져오기
    print("[Backfill] Step 3/5: Fetching deposit/withdraw history...")

    try:
        deposits = api.get_deposits(limit=100)
        withdraws = api.get_withdraws(limit=100)

        # days=0이면 모든 입출금 내역 포함
        if days > 0:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            deposits = [
                d for d in deposits
                if datetime.fromisoformat(d['created_at'].replace('Z', '+00:00')) > cutoff_date
            ]
            withdraws = [
                w for w in withdraws
                if datetime.fromisoformat(w['created_at'].replace('Z', '+00:00')) > cutoff_date
            ]

        print(f"  Deposits: {len(deposits)}, Withdraws: {len(withdraws)}")
    except Exception as e:
        print(f"  Warning: Failed to fetch deposits/withdraws: {e}")
        deposits = []
        withdraws = []

    # 4. 시간순 역순으로 거래 역산
    print("[Backfill] Step 4/5: Calculating daily snapshots...")

    # 잔고 추적기 초기화 (현재 상태)
    balance_tracker = {
        'krw_balance': current_krw_balance,
        'krw_locked': current_krw_locked,
        'holdings': {k: v.copy() for k, v in current_holdings.items()}
    }

    # 모든 거래를 시간순 역순으로 정렬 (최신 → 과거)
    all_transactions = []

    for order in all_orders:
        all_transactions.append({
            'type': 'order',
            'timestamp': order['created_at'],
            'data': order
        })

    for deposit in deposits:
        all_transactions.append({
            'type': 'deposit',
            'timestamp': deposit['created_at'],
            'data': deposit
        })

    for withdraw in withdraws:
        all_transactions.append({
            'type': 'withdraw',
            'timestamp': withdraw['created_at'],
            'data': withdraw
        })

    # 시간순 역순 정렬 (최신 → 과거)
    all_transactions.sort(key=lambda x: x['timestamp'], reverse=True)

    print(f"  Processing {len(all_transactions)} transactions...")

    # 일자별 스냅샷 저장
    daily_snapshots = {}

    # 오늘 스냅샷 (현재 상태)
    today = datetime.now(timezone.utc).date()
    daily_snapshots[str(today)] = create_snapshot(balance_tracker, api, today)

    # 거래를 역으로 적용하며 과거 복원
    for transaction in all_transactions:
        tx_date = datetime.fromisoformat(transaction['timestamp'].replace('Z', '+00:00')).date()
        tx_type = transaction['type']
        tx_data = transaction['data']

        # 주문 역산
        if tx_type == 'order':
            side = tx_data['side']  # 'bid' (매수) or 'ask' (매도)
            market = tx_data['market']
            currency = market.split('-')[1]  # KRW-BTC → BTC
            executed_volume = float(tx_data.get('executed_volume', 0))
            paid_fee = float(tx_data.get('paid_fee', 0))
            trades_sum = float(tx_data.get('trades', [{}])[0].get('funds', 0)) if tx_data.get('trades') else 0

            if side == 'bid':  # 매수 주문을 역산
                # 과거에는: KRW 많았고, 코인 적었음
                balance_tracker['krw_balance'] += trades_sum + paid_fee

                if currency in balance_tracker['holdings']:
                    balance_tracker['holdings'][currency]['amount'] -= executed_volume
                    if balance_tracker['holdings'][currency]['amount'] <= 0:
                        del balance_tracker['holdings'][currency]

            elif side == 'ask':  # 매도 주문을 역산
                # 과거에는: KRW 적었고, 코인 많았음
                balance_tracker['krw_balance'] -= trades_sum - paid_fee

                if currency not in balance_tracker['holdings']:
                    balance_tracker['holdings'][currency] = {
                        'amount': 0,
                        'avg_buy_price': 0
                    }
                balance_tracker['holdings'][currency]['amount'] += executed_volume

        # 입금 역산
        elif tx_type == 'deposit':
            if tx_data.get('currency') == 'KRW':
                amount = float(tx_data.get('amount', 0))
                # 과거에는: 입금 전이므로 KRW가 적었음
                balance_tracker['krw_balance'] -= amount
                balance_tracker['has_deposit'] = True  # 입금 이벤트 플래그
                balance_tracker['deposit_amount'] = amount

        # 출금 역산
        elif tx_type == 'withdraw':
            if tx_data.get('currency') == 'KRW':
                amount = float(tx_data.get('amount', 0))
                fee = float(tx_data.get('fee', 0))
                # 과거에는: 출금 전이므로 KRW가 많았음
                balance_tracker['krw_balance'] += amount + fee

        # 해당 날짜의 스냅샷 저장 (하루에 1개만)
        date_str = str(tx_date)
        if date_str not in daily_snapshots:
            daily_snapshots[date_str] = create_snapshot(balance_tracker, api, tx_date)
            # 입금 플래그 초기화 (다음 날짜를 위해)
            balance_tracker['has_deposit'] = False
            balance_tracker['deposit_amount'] = 0

    # 거래가 없는 날짜 채우기 (선형 보간)
    print(f"  Generated {len(daily_snapshots)} snapshots")

    # 5. DB에 저장
    print("[Backfill] Step 5/5: Saving to database...")
    db = get_db_session()

    try:
        saved_count = 0
        for date_str, snapshot_data in sorted(daily_snapshots.items()):
            # 이미 존재하는지 확인
            existing = db.query(HoldingsHistory).filter(
                HoldingsHistory.user_id == user_id,
                HoldingsHistory.snapshot_time >= datetime.fromisoformat(date_str),
                HoldingsHistory.snapshot_time < datetime.fromisoformat(date_str) + timedelta(days=1)
            ).first()

            if existing:
                continue

            # 새 스냅샷 저장
            snapshot = HoldingsHistory(
                user_id=user_id,
                snapshot_time=snapshot_data['snapshot_time'],
                krw_balance=snapshot_data['krw_balance'],
                krw_locked=snapshot_data['krw_locked'],
                krw_total=snapshot_data['krw_total'],
                total_value=snapshot_data['total_value'],
                crypto_value=snapshot_data['crypto_value'],
                total_profit=snapshot_data['total_profit'],
                total_profit_rate=snapshot_data['total_profit_rate'],
                coin_count=snapshot_data['coin_count'],
                holdings_detail=snapshot_data['holdings_detail']
            )

            db.add(snapshot)
            saved_count += 1

        db.commit()
        print(f"  ✓ Saved {saved_count} new snapshots to database")
        print(f"\n[Backfill] ✓ Backfill completed successfully!")

    except Exception as e:
        print(f"\n[Backfill] ✗ Error saving to database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_historical_price(db, market, date):
    """
    Get historical price from coin_price_history table

    Args:
        db: Database session
        market: Market code (e.g., 'KRW-BTC')
        date: Date to query

    Returns:
        float: Close price, or 0 if not found
    """
    try:
        query = text("""
            SELECT close_price
            FROM coin_price_history
            WHERE market = :market
            AND date = :date
            LIMIT 1
        """)

        result = db.execute(query, {'market': market, 'date': date})
        row = result.fetchone()

        if row:
            return float(row[0])

        # Fallback: get latest price if date's not available
        query = text("""
            SELECT close_price
            FROM coin_price_history
            WHERE market = :market
            ORDER BY date DESC
            LIMIT 1
        """)

        result = db.execute(query, {'market': market})
        row = result.fetchone()

        return float(row[0]) if row else 0

    except Exception as e:
        return 0


def create_snapshot(balance_tracker, api, date):
    """
    현재 balance_tracker 상태로 스냅샷 생성

    Args:
        balance_tracker: 잔고 추적 딕셔너리
        api: UpbitAPI instance
        date: 날짜

    Returns:
        dict: 스냅샷 데이터
    """
    krw_balance = balance_tracker['krw_balance']
    krw_locked = balance_tracker.get('krw_locked', 0)
    krw_total = krw_balance + krw_locked

    # 코인 평가
    holdings_detail = []
    crypto_value = 0
    total_purchase_amount = 0

    # Get database session for price lookup
    db = get_db_session()

    for currency, holding in balance_tracker['holdings'].items():
        market = f'KRW-{currency}'
        amount = holding['amount']
        avg_buy_price = holding.get('avg_buy_price', 0)

        # 해당 날짜의 가격 가져오기 (coin_price_history 테이블)
        current_price = get_historical_price(db, market, date)
        if current_price == 0:
            current_price = avg_buy_price

        current_value = amount * current_price
        purchase_amount = amount * avg_buy_price

        holdings_detail.append({
            'currency': currency,
            'market': market,
            'amount': amount,
            'avg_buy_price': avg_buy_price,
            'current_price': current_price,
            'current_value': current_value,
            'purchase_amount': purchase_amount
        })

        crypto_value += current_value
        total_purchase_amount += purchase_amount

    total_value = krw_total + crypto_value
    total_profit = crypto_value - total_purchase_amount
    total_profit_rate = (total_profit / total_purchase_amount * 100) if total_purchase_amount > 0 else 0

    # Close database session
    db.close()

    return {
        'snapshot_time': datetime.combine(date, datetime.min.time()),
        'krw_balance': krw_balance,
        'krw_locked': krw_locked,
        'krw_total': krw_total,
        'total_value': total_value,
        'crypto_value': crypto_value,
        'total_profit': total_profit,
        'total_profit_rate': total_profit_rate,
        'coin_count': len(balance_tracker['holdings']),
        'holdings_detail': {
            'coins': holdings_detail,
            'total_purchase_amount': total_purchase_amount,
            'has_deposit': balance_tracker.get('has_deposit', False),  # 입금 이벤트 플래그
            'deposit_amount': balance_tracker.get('deposit_amount', 0)  # 입금 금액
        }
    }


if __name__ == '__main__':
    import sys

    # Optional: specify user_id and days as command line arguments
    # Usage: python script.py [user_id] [days]
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
        print(f"\n[Backfill] Using user_id from command line: {user_id}")
    else:
        db = get_db_session()
        try:
            user_id = get_user_id(db)
            print(f"\n[Backfill] Using first user from database: {user_id}")
        finally:
            db.close()

    # Get days parameter (default: 90)
    if len(sys.argv) > 2:
        days = int(sys.argv[2])
        print(f"[Backfill] Using days from command line: {days}")
    else:
        days = 90
        print(f"[Backfill] Using default days: {days}")

    backfill_balance_history(user_id, days=days)
