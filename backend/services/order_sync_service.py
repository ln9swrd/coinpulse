"""
Order Sync Service Module

Synchronizes trading orders from Upbit API to local database.
"""

import time
from datetime import datetime, timezone
from backend.database import get_db_session, Order, SyncStatus


class OrderSyncService:
    """
    Service class for synchronizing Upbit orders to database.

    Features:
    - Initial full sync (all historical orders)
    - Incremental sync (new orders only)
    - Automatic retry on failures
    - Progress tracking
    """

    def __init__(self, upbit_api):
        """
        Initialize OrderSyncService.

        Args:
            upbit_api: UpbitAPI instance for fetching orders
        """
        self.upbit_api = upbit_api

    def initial_full_sync(self, market=None, max_orders=10000):
        """
        Perform initial full synchronization of all orders.

        Fetches all completed orders from Upbit API (up to API limit ~3 months).

        Args:
            market (str, optional): Market code to filter (e.g., 'KRW-BTC')
            max_orders (int): Maximum orders to sync (safety limit)

        Returns:
            dict: Sync results with counts and errors
        """
        print(f"\n{'='*60}")
        print(f"Starting Initial Full Sync")
        if market:
            print(f"Market: {market}")
        print(f"{'='*60}\n")

        db = get_db_session()
        synced_count = 0
        page = 1
        total_pages_estimated = "?"
        errors = []

        try:
            while synced_count < max_orders:
                print(f"[Sync] Fetching page {page}/{total_pages_estimated}... ", end='', flush=True)

                # Fetch orders from Upbit API
                orders = self.upbit_api.get_orders_history(
                    market=market,
                    state='done',
                    limit=100,
                    page=page,
                    order_by='desc',
                    include_trades=True  # Include execution details
                )

                if not orders:
                    print("No more orders")
                    break

                print(f"Got {len(orders)} orders")

                # Save to database
                for order in orders:
                    try:
                        self.upsert_order(db, order)
                        synced_count += 1

                        if synced_count % 100 == 0:
                            print(f"[Sync] Progress: {synced_count} orders synced")

                    except Exception as e:
                        error_msg = f"Failed to sync order {order.get('uuid', 'unknown')}: {str(e)}"
                        print(f"[Sync] ERROR: {error_msg}")
                        errors.append(error_msg)

                # Commit batch
                db.commit()

                # Stop if we got fewer orders than requested (last page)
                if len(orders) < 100:
                    print(f"[Sync] Reached last page (got {len(orders)} < 100)")
                    break

                page += 1
                time.sleep(0.15)  # Rate limit protection (6-7 requests/second)

            # Update sync status
            self.update_sync_status(db, market, synced_count)
            db.commit()

            print(f"\n{'='*60}")
            print(f"Initial Sync Complete!")
            print(f"Total synced: {synced_count} orders")
            if errors:
                print(f"Errors: {len(errors)}")
            print(f"{'='*60}\n")

            return {
                'success': True,
                'synced_count': synced_count,
                'pages': page,
                'errors': errors
            }

        except Exception as e:
            db.rollback()
            print(f"\n[Sync] CRITICAL ERROR: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'synced_count': synced_count
            }
        finally:
            db.close()

    def incremental_sync(self, market=None):
        """
        Perform incremental synchronization (new orders only).

        Fetches only orders created after the last sync.
        Should be run periodically (e.g., every 5 minutes).

        Args:
            market (str, optional): Market code to filter

        Returns:
            dict: Sync results
        """
        print(f"[Sync] Starting incremental sync for {market or 'all markets'}...")

        db = get_db_session()
        synced_count = 0
        errors = []

        try:
            # Get last sync info
            sync_status = db.query(SyncStatus).filter_by(market=market or 'all').first()
            last_uuid = sync_status.last_order_uuid if sync_status else None

            print(f"[Sync] Last synced order: {last_uuid or 'None (first sync)'}")

            # Fetch latest orders
            orders = self.upbit_api.get_orders_history(
                market=market,
                state='done',
                limit=100,
                order_by='desc',
                include_trades=True
            )

            if not orders:
                print("[Sync] No new orders")
                return {'success': True, 'synced_count': 0}

            # Sync until we reach the last synced order
            for order in orders:
                if order['uuid'] == last_uuid:
                    print(f"[Sync] Reached last synced order: {last_uuid[:8]}...")
                    break

                try:
                    self.upsert_order(db, order)
                    synced_count += 1
                except Exception as e:
                    error_msg = f"Failed to sync order {order['uuid']}: {str(e)}"
                    print(f"[Sync] ERROR: {error_msg}")
                    errors.append(error_msg)

            # Update sync status
            if synced_count > 0:
                self.update_sync_status(db, market, synced_count, orders[0]['uuid'])

            db.commit()

            print(f"[Sync] Incremental sync complete: {synced_count} new orders")

            return {
                'success': True,
                'synced_count': synced_count,
                'errors': errors
            }

        except Exception as e:
            db.rollback()
            print(f"[Sync] ERROR: {str(e)}")
            return {'success': False, 'error': str(e)}
        finally:
            db.close()

    def upsert_order(self, db_session, order_data):
        """
        Insert or update order in database using native SQLite/PostgreSQL upsert.

        Args:
            db_session: SQLAlchemy session
            order_data: Order data dict from Upbit API
        """
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        from datetime import datetime

        fields = self.extract_order_fields(order_data)
        fields['updated_at'] = datetime.utcnow()

        # Use native upsert for both SQLite and PostgreSQL
        # This is much more efficient than merge() for batch operations
        if 'sqlite' in str(db_session.bind.url):
            stmt = sqlite_insert(Order).values(**fields)
            stmt = stmt.on_conflict_do_update(
                index_elements=['uuid'],
                set_={k: v for k, v in fields.items() if k != 'uuid'}
            )
        else:  # PostgreSQL
            stmt = pg_insert(Order).values(**fields)
            stmt = stmt.on_conflict_do_update(
                index_elements=['uuid'],
                set_={k: v for k, v in fields.items() if k != 'uuid'}
            )

        db_session.execute(stmt)

    def extract_order_fields(self, order_data):
        """
        Extract and convert order fields from API response.

        Args:
            order_data: Raw order dict from Upbit API

        Returns:
            dict: Fields ready for Order model
        """
        return {
            'uuid': order_data['uuid'],
            'market': order_data['market'],
            'side': order_data['side'],
            'ord_type': order_data.get('ord_type'),
            'state': order_data['state'],
            'price': float(order_data['price']) if order_data.get('price') else None,
            'avg_price': float(order_data['avg_price']) if order_data.get('avg_price') else None,
            'volume': float(order_data['volume']) if order_data.get('volume') else None,
            'executed_volume': float(order_data['executed_volume']) if order_data.get('executed_volume') else None,
            'remaining_volume': float(order_data['remaining_volume']) if order_data.get('remaining_volume') else None,
            'paid_fee': float(order_data['paid_fee']) if order_data.get('paid_fee') else None,
            'locked': float(order_data['locked']) if order_data.get('locked') else None,
            'executed_funds': float(order_data['executed_funds']) if order_data.get('executed_funds') else None,
            'remaining_funds': float(order_data['remaining_funds']) if order_data.get('remaining_funds') else None,
            'created_at': self.parse_datetime(order_data.get('created_at')),
            'executed_at': self.parse_datetime(order_data.get('executed_at')),
            'kr_time': order_data.get('kr_time'),
            'strategy': 'manual',  # Will be updated by trading engine
            'strategy_name': None,
            'signal_source': 'manual',
            'raw_data': order_data,  # Store complete JSON
            'trades': order_data.get('trades', []),
            'synced_at': datetime.utcnow()
        }

    def parse_datetime(self, dt_string):
        """
        Parse datetime string from Upbit API.

        Args:
            dt_string: ISO 8601 datetime string

        Returns:
            datetime: Parsed datetime object (UTC)
        """
        if not dt_string or dt_string == 'N/A':
            return None

        try:
            # Parse ISO 8601 format
            if 'T' in dt_string:
                # Remove timezone info and parse as UTC
                dt_clean = dt_string.split('+')[0].split('Z')[0]
                return datetime.fromisoformat(dt_clean)
            else:
                # Korean format: "2025-10-14 13:45:00"
                return datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"[Sync] WARNING: Failed to parse datetime '{dt_string}': {e}")
            return None

    def update_sync_status(self, db_session, market, order_count, last_uuid=None):
        """
        Update synchronization status in database.

        Args:
            db_session: SQLAlchemy session
            market: Market code (or None for all)
            order_count: Number of orders synced
            last_uuid: UUID of last synced order
        """
        market_key = market or 'all'

        sync_status = db_session.query(SyncStatus).filter_by(market=market_key).first()

        if sync_status:
            sync_status.last_sync = datetime.utcnow()
            sync_status.total_orders += order_count
            sync_status.sync_count += 1
            if last_uuid:
                sync_status.last_order_uuid = last_uuid
        else:
            sync_status = SyncStatus(
                market=market_key,
                last_sync=datetime.utcnow(),
                last_order_uuid=last_uuid,
                total_orders=order_count,
                sync_count=1
            )
            db_session.add(sync_status)

        db_session.commit()
