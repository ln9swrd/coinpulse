"""
Balance History Service Module

Captures and retrieves daily balance snapshots for historical tracking.
Tracks: Total KRW, Available amount, Portfolio total, Total purchase amount.
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from backend.database.connection import get_db_session
from backend.database.models import HoldingsHistory

logger = logging.getLogger(__name__)


class BalanceHistoryService:
    """
    Service for capturing and retrieving balance history snapshots.

    This service:
    - Captures daily balance snapshots
    - Retrieves historical balance data
    - Calculates total purchase amount from holdings
    """

    def __init__(self, upbit_api=None):
        """
        Initialize BalanceHistoryService.

        Args:
            upbit_api: UpbitAPI instance for fetching account data
        """
        self.upbit_api = upbit_api

    def capture_snapshot(self, user_id):
        """
        Capture current balance snapshot and save to database.

        Args:
            user_id: User ID to capture snapshot for

        Returns:
            dict: Captured snapshot data or None if failed
        """
        if not self.upbit_api:
            logger.warning(f"[BalanceHistory] User {user_id}: Upbit API not configured")
            return None

        try:
            logger.info(f"[BalanceHistory] User {user_id}: Capturing balance snapshot...")

            # Get accounts from Upbit
            accounts = self.upbit_api.get_accounts()
            if not accounts:
                logger.warning(f"[BalanceHistory] User {user_id}: No accounts data")
                return None

            # Extract KRW data
            krw_account = next((acc for acc in accounts if acc['currency'] == 'KRW'), None)
            krw_balance = float(krw_account['balance']) if krw_account else 0
            krw_locked = float(krw_account['locked']) if krw_account else 0
            krw_total = krw_balance + krw_locked

            # Process crypto holdings
            crypto_accounts = [acc for acc in accounts if acc['currency'] != 'KRW'
                             and (float(acc['balance']) > 0 or float(acc['locked']) > 0)]

            if not crypto_accounts:
                # No crypto holdings, just KRW
                snapshot_data = {
                    'user_id': user_id,
                    'snapshot_time': datetime.utcnow(),
                    'krw_balance': krw_balance,
                    'krw_locked': krw_locked,
                    'krw_total': krw_total,
                    'total_value': krw_total,
                    'crypto_value': 0,
                    'total_profit': 0,
                    'total_profit_rate': 0,
                    'coin_count': 0,
                    'holdings_detail': [],
                    'total_purchase_amount': 0
                }

                self._save_snapshot(snapshot_data)
                logger.info(f"[BalanceHistory] User {user_id}: Snapshot saved (KRW only)")
                return snapshot_data

            # Get current prices for all crypto holdings
            markets = [f'KRW-{acc["currency"]}' for acc in crypto_accounts]
            current_prices = self.upbit_api.get_current_prices(markets)

            # Calculate holdings details
            holdings_detail = []
            crypto_value = 0
            total_purchase_amount = 0

            for account in crypto_accounts:
                currency = account['currency']
                market = f'KRW-{currency}'
                balance = float(account['balance'])
                locked = float(account['locked'])
                amount = balance + locked
                avg_buy_price = float(account.get('avg_buy_price', 0))

                # Get current price
                price_info = current_prices.get(market, {})
                current_price = float(price_info.get('trade_price', 0))

                if current_price == 0:
                    current_price = avg_buy_price

                # Calculations
                current_value = amount * current_price
                purchase_amount = amount * avg_buy_price
                profit_loss = current_value - purchase_amount
                profit_rate = (profit_loss / purchase_amount * 100) if purchase_amount > 0 else 0

                holdings_detail.append({
                    'currency': currency,
                    'market': market,
                    'balance': balance,
                    'locked': locked,
                    'amount': amount,
                    'avg_buy_price': avg_buy_price,
                    'current_price': current_price,
                    'current_value': current_value,
                    'purchase_amount': purchase_amount,
                    'profit_loss': profit_loss,
                    'profit_rate': profit_rate
                })

                crypto_value += current_value
                total_purchase_amount += purchase_amount

            # Calculate totals
            total_value = krw_total + crypto_value
            total_profit = crypto_value - total_purchase_amount
            total_profit_rate = (total_profit / total_purchase_amount * 100) if total_purchase_amount > 0 else 0

            # Prepare snapshot data
            snapshot_data = {
                'user_id': user_id,
                'snapshot_time': datetime.utcnow(),
                'krw_balance': krw_balance,
                'krw_locked': krw_locked,
                'krw_total': krw_total,
                'total_value': total_value,
                'crypto_value': crypto_value,
                'total_profit': total_profit,
                'total_profit_rate': total_profit_rate,
                'coin_count': len(crypto_accounts),
                'holdings_detail': holdings_detail,
                'total_purchase_amount': total_purchase_amount
            }

            # Save to database
            self._save_snapshot(snapshot_data)

            logger.info(
                f"[BalanceHistory] User {user_id}: Snapshot saved - "
                f"Total: ₩{total_value:,.0f}, Crypto: ₩{crypto_value:,.0f}, "
                f"Purchase: ₩{total_purchase_amount:,.0f}, Coins: {len(crypto_accounts)}"
            )

            return snapshot_data

        except Exception as e:
            logger.error(f"[BalanceHistory] User {user_id}: Error capturing snapshot: {e}")
            return None

    def _save_snapshot(self, snapshot_data):
        """
        Save snapshot to database.

        Args:
            snapshot_data: Dictionary with snapshot fields
        """
        db = None
        try:
            db = get_db_session()

            # Add total_purchase_amount to holdings_detail JSON
            holdings_detail_json = snapshot_data.get('holdings_detail', [])
            if 'total_purchase_amount' in snapshot_data:
                # Store total_purchase_amount in JSON for easy retrieval
                holdings_detail_json = {
                    'coins': holdings_detail_json,
                    'total_purchase_amount': snapshot_data['total_purchase_amount']
                }

            snapshot = HoldingsHistory(
                user_id=snapshot_data.get('user_id'),  # Multi-user support
                snapshot_time=snapshot_data['snapshot_time'],
                krw_balance=snapshot_data['krw_balance'],
                krw_locked=snapshot_data['krw_locked'],
                krw_total=snapshot_data['krw_total'],
                total_value=snapshot_data['total_value'],
                crypto_value=snapshot_data['crypto_value'],
                total_profit=snapshot_data['total_profit'],
                total_profit_rate=snapshot_data['total_profit_rate'],
                coin_count=snapshot_data['coin_count'],
                holdings_detail=holdings_detail_json
            )

            db.add(snapshot)
            db.commit()

            logger.info(f"[BalanceHistory] Snapshot saved to database (ID: {snapshot.id})")

        except Exception as e:
            logger.error(f"[BalanceHistory] Error saving snapshot to database: {e}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()

    def get_history(self, user_id, days=30):
        """
        Retrieve balance history for specified number of days.

        Args:
            user_id: User ID to get history for
            days: Number of days to retrieve (default: 30)

        Returns:
            list: List of snapshot dictionaries ordered by date (oldest first)
        """
        db = None
        try:
            db = get_db_session()

            # Calculate start date
            start_date = datetime.utcnow() - timedelta(days=days)

            # Query snapshots (USER-SPECIFIC)
            snapshots = db.query(HoldingsHistory)\
                .filter(HoldingsHistory.user_id == user_id)\
                .filter(HoldingsHistory.snapshot_time >= start_date)\
                .order_by(HoldingsHistory.snapshot_time)\
                .all()

            if not snapshots:
                logger.info(f"[BalanceHistory] User {user_id}: No history found for last {days} days")
                return []

            # Convert to list of dictionaries
            history = []
            for snapshot in snapshots:
                # Extract total_purchase_amount from holdings_detail JSON
                holdings_detail = snapshot.holdings_detail or {}
                total_purchase_amount = 0

                if isinstance(holdings_detail, dict) and 'total_purchase_amount' in holdings_detail:
                    total_purchase_amount = holdings_detail['total_purchase_amount']
                elif isinstance(holdings_detail, dict) and 'coins' in holdings_detail:
                    # Calculate from coins array
                    coins = holdings_detail.get('coins', [])
                    total_purchase_amount = sum(coin.get('purchase_amount', 0) for coin in coins)

                history.append({
                    'id': snapshot.id,
                    'snapshot_time': snapshot.snapshot_time.isoformat(),
                    'date': snapshot.snapshot_time.strftime('%Y-%m-%d'),
                    'krw_balance': float(snapshot.krw_balance) if snapshot.krw_balance else 0,
                    'krw_locked': float(snapshot.krw_locked) if snapshot.krw_locked else 0,
                    'krw_total': float(snapshot.krw_total) if snapshot.krw_total else 0,
                    'total_value': float(snapshot.total_value) if snapshot.total_value else 0,
                    'crypto_value': float(snapshot.crypto_value) if snapshot.crypto_value else 0,
                    'total_purchase_amount': total_purchase_amount,
                    'total_profit': float(snapshot.total_profit) if snapshot.total_profit else 0,
                    'total_profit_rate': float(snapshot.total_profit_rate) if snapshot.total_profit_rate else 0,
                    'coin_count': snapshot.coin_count
                })

            logger.info(f"[BalanceHistory] User {user_id}: Retrieved {len(history)} snapshots")
            return history

        except Exception as e:
            logger.error(f"[BalanceHistory] User {user_id}: Error retrieving history: {e}")
            return []
        finally:
            if db:
                db.close()

    def get_daily_grouped_history(self, user_id, days=30):
        """
        Get balance history grouped by day (one snapshot per day).
        Uses the latest snapshot for each day.

        Args:
            user_id: User ID to get history for
            days: Number of days to retrieve (default: 30)

        Returns:
            list: List of daily snapshot dictionaries ordered by date (oldest first)
        """
        all_history = self.get_history(user_id, days)

        if not all_history:
            return []

        # Group by date and keep only the latest snapshot per day
        daily_snapshots = {}
        for snapshot in all_history:
            date = snapshot['date']
            if date not in daily_snapshots:
                daily_snapshots[date] = snapshot
            else:
                # Keep the latest snapshot for each day
                if snapshot['snapshot_time'] > daily_snapshots[date]['snapshot_time']:
                    daily_snapshots[date] = snapshot

        # Convert to list and sort by date
        result = sorted(daily_snapshots.values(), key=lambda x: x['date'])

        logger.info(f"[BalanceHistory] User {user_id}: Grouped into {len(result)} daily snapshots")
        return result
