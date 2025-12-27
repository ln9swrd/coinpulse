"""
Daily Balance Snapshot Script

매일 실행하여 모든 사용자의 오늘 잔고 스냅샷을 생성합니다.
- 과거 거래 조회 불필요 (효율적)
- 현재 잔고만 조회 (API 1회)
- 코인 가격은 coin_price_history 테이블 활용

Usage:
    python scripts/daily_snapshot.py [user_id]

    user_id: 특정 사용자만 처리 (선택사항, 없으면 모든 사용자)

Examples:
    python scripts/daily_snapshot.py        # 모든 사용자
    python scripts/daily_snapshot.py 1      # 사용자 1만
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.common import UpbitAPI, load_api_keys
from backend.database.connection import get_db_session
from backend.database.models import HoldingsHistory
from sqlalchemy import text


def get_active_users(db):
    """Get all active users with Upbit API keys"""
    query = text("""
        SELECT DISTINCT user_id
        FROM upbit_api_keys
        WHERE is_active = true
        AND access_key_encrypted IS NOT NULL
        AND secret_key_encrypted IS NOT NULL
        ORDER BY user_id
    """)

    result = db.execute(query)
    return [row[0] for row in result]


def get_coin_price_from_db(db, market, date=None):
    """
    Get coin price from coin_price_history table

    Args:
        db: Database session
        market: Market code (e.g., 'KRW-BTC')
        date: Date to query (default: today)

    Returns:
        float: Close price, or 0 if not found
    """
    if date is None:
        date = datetime.now(timezone.utc).date()

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

        # Fallback: get latest price if today's not available
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
        print(f"  Warning: Failed to get price for {market}: {e}")
        return 0


def get_current_price_from_api(api, market):
    """
    Get current price from Upbit API (fallback)

    Args:
        api: UpbitAPI instance
        market: Market code

    Returns:
        float: Current price, or 0 if failed
    """
    try:
        ticker = api.get_current_price(market)
        return float(ticker.get('trade_price', 0)) if ticker else 0
    except Exception as e:
        print(f"  Warning: Failed to get API price for {market}: {e}")
        return 0


def create_today_snapshot(user_id):
    """
    Create today's snapshot for a user

    Args:
        user_id: User ID

    Returns:
        dict: Snapshot data, or None if failed
    """
    print(f"\n[DailySnapshot] Processing user {user_id}...")

    try:
        # 1. Get API keys
        access_key, secret_key = load_api_keys(user_id)
        if not access_key or not secret_key:
            print(f"  [WARNING] No API keys found for user {user_id}")
            return None

        # 2. Initialize API
        api = UpbitAPI(access_key, secret_key)

        # 3. Get current accounts
        accounts = api.get_accounts()
        if not accounts:
            print(f"  [WARNING] Failed to fetch accounts for user {user_id}")
            return None

        print(f"  [OK] Fetched {len(accounts)} accounts")

        # 4. Process KRW balance
        krw_account = next((acc for acc in accounts if acc['currency'] == 'KRW'), None)
        krw_balance = float(krw_account['balance']) if krw_account else 0
        krw_locked = float(krw_account['locked']) if krw_account else 0
        krw_total = krw_balance + krw_locked

        print(f"  KRW: {krw_total:,.0f} (balance: {krw_balance:,.0f}, locked: {krw_locked:,.0f})")

        # 5. Process crypto holdings
        db = get_db_session()
        today = datetime.now(timezone.utc).date()

        holdings_detail = []
        crypto_value = 0
        total_purchase_amount = 0

        for account in accounts:
            if account['currency'] == 'KRW':
                continue

            currency = account['currency']
            balance = float(account['balance'])
            locked = float(account['locked'])
            amount = balance + locked

            if amount <= 0:
                continue

            market = f'KRW-{currency}'
            avg_buy_price = float(account.get('avg_buy_price', 0))

            # Get current price (from DB first, then API fallback)
            current_price = get_coin_price_from_db(db, market, today)
            if current_price == 0:
                current_price = get_current_price_from_api(api, market)
            if current_price == 0:
                current_price = avg_buy_price  # Last resort

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

        db.close()

        print(f"  Crypto: {len(holdings_detail)} coins, {crypto_value:,.0f} KRW")

        # 6. Calculate totals
        total_value = krw_total + crypto_value
        total_profit = crypto_value - total_purchase_amount
        total_profit_rate = (total_profit / total_purchase_amount * 100) if total_purchase_amount > 0 else 0

        print(f"  Total: {total_value:,.0f} KRW (profit: {total_profit:+,.0f} KRW, {total_profit_rate:+.2f}%)")

        # 7. Create snapshot
        snapshot_time = datetime.combine(today, datetime.min.time())

        snapshot = {
            'user_id': user_id,
            'snapshot_time': snapshot_time,
            'krw_balance': krw_balance,
            'krw_locked': krw_locked,
            'krw_total': krw_total,
            'total_value': total_value,
            'crypto_value': crypto_value,
            'total_profit': total_profit,
            'total_profit_rate': total_profit_rate,
            'coin_count': len(holdings_detail),
            'holdings_detail': {
                'coins': holdings_detail,
                'total_purchase_amount': total_purchase_amount,
                'has_deposit': False,
                'deposit_amount': 0
            }
        }

        return snapshot

    except Exception as e:
        print(f"  [ERROR] Error processing user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_snapshot(snapshot):
    """
    Save snapshot to database (insert or update)

    Args:
        snapshot: Snapshot dict

    Returns:
        bool: True if saved, False if failed
    """
    db = get_db_session()

    try:
        user_id = snapshot['user_id']
        snapshot_time = snapshot['snapshot_time']

        # Check if snapshot already exists for today
        existing = db.query(HoldingsHistory).filter(
            HoldingsHistory.user_id == user_id,
            HoldingsHistory.snapshot_time >= snapshot_time,
            HoldingsHistory.snapshot_time < snapshot_time + timedelta(days=1)
        ).first()

        if existing:
            # Update existing snapshot
            existing.krw_balance = snapshot['krw_balance']
            existing.krw_locked = snapshot['krw_locked']
            existing.krw_total = snapshot['krw_total']
            existing.total_value = snapshot['total_value']
            existing.crypto_value = snapshot['crypto_value']
            existing.total_profit = snapshot['total_profit']
            existing.total_profit_rate = snapshot['total_profit_rate']
            existing.coin_count = snapshot['coin_count']
            existing.holdings_detail = snapshot['holdings_detail']

            print(f"  [OK] Updated existing snapshot for user {user_id}")
        else:
            # Insert new snapshot
            new_snapshot = HoldingsHistory(
                user_id=user_id,
                snapshot_time=snapshot_time,
                krw_balance=snapshot['krw_balance'],
                krw_locked=snapshot['krw_locked'],
                krw_total=snapshot['krw_total'],
                total_value=snapshot['total_value'],
                crypto_value=snapshot['crypto_value'],
                total_profit=snapshot['total_profit'],
                total_profit_rate=snapshot['total_profit_rate'],
                coin_count=snapshot['coin_count'],
                holdings_detail=snapshot['holdings_detail']
            )

            db.add(new_snapshot)
            print(f"  [OK] Created new snapshot for user {user_id}")

        db.commit()
        return True

    except Exception as e:
        print(f"  [ERROR] Error saving snapshot for user {user_id}: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Main function"""
    print("=" * 70)
    print("  Daily Balance Snapshot")
    print("=" * 70)
    print()

    # Get target user (if specified)
    target_user_id = None
    if len(sys.argv) > 1:
        target_user_id = int(sys.argv[1])
        print(f"[DailySnapshot] Target: User {target_user_id}")
    else:
        print("[DailySnapshot] Target: All active users")

    print()

    # Get database session
    db = get_db_session()

    try:
        # Get users to process
        if target_user_id:
            user_ids = [target_user_id]
        else:
            user_ids = get_active_users(db)

        print(f"[DailySnapshot] Found {len(user_ids)} user(s) to process")
        print()

        if not user_ids:
            print("[WARNING] No users found")
            return 0

        # Process each user
        success_count = 0
        failed_count = 0

        for user_id in user_ids:
            snapshot = create_today_snapshot(user_id)

            if snapshot:
                if save_snapshot(snapshot):
                    success_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1

        # Summary
        print()
        print("=" * 70)
        print("  Summary")
        print("=" * 70)
        print(f"Total Users: {len(user_ids)}")
        print(f"Success: {success_count}")
        print(f"Failed: {failed_count}")
        print("=" * 70)
        print()

        if success_count > 0:
            print("[SUCCESS] Daily snapshot completed successfully!")
        else:
            print("[WARNING] No snapshots were created")

        return 0

    except Exception as e:
        print()
        print(f"[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print("[DailySnapshot] Interrupted by user (Ctrl+C)")
        sys.exit(1)
