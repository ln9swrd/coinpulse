"""
Background Sync Scheduler

Runs incremental order synchronization in the background every 5 minutes.
"""

import threading
import time
from datetime import datetime
from backend.services.order_sync_service import OrderSyncService


class BackgroundSyncScheduler:
    """
    Background scheduler for incremental order synchronization.

    Runs in a separate thread and syncs orders every 5 minutes.
    """

    def __init__(self, upbit_api, sync_interval_seconds=300):
        """
        Initialize background sync scheduler.

        Args:
            upbit_api: UpbitAPI instance
            sync_interval_seconds: Sync interval in seconds (default: 300 = 5 minutes)
        """
        self.upbit_api = upbit_api
        self.sync_interval = sync_interval_seconds
        self.sync_service = OrderSyncService(upbit_api)
        self.running = False
        self.thread = None

        print(f"[BackgroundSync] Initialized (interval: {sync_interval_seconds}s = {sync_interval_seconds//60} minutes)")

    def start(self):
        """Start the background sync thread."""
        if self.running:
            print("[BackgroundSync] Already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.thread.start()
        print("[BackgroundSync] Started")

    def stop(self):
        """Stop the background sync thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        print("[BackgroundSync] Stopped")

    def _sync_loop(self):
        """Main sync loop - runs in background thread."""
        print("[BackgroundSync] Loop started")

        # Wait 60 seconds before first sync (let server start)
        time.sleep(60)

        while self.running:
            try:
                self._run_incremental_sync()
            except Exception as e:
                print(f"[BackgroundSync] ❌ Sync error: {e}")

            # Wait for next sync
            time.sleep(self.sync_interval)

    def _run_incremental_sync(self):
        """Run incremental sync for all markets."""
        start_time = datetime.now()
        print(f"\n{'='*60}")
        print(f"[BackgroundSync] Starting incremental sync...")
        print(f"[BackgroundSync] Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        try:
            # Run incremental sync (only fetches new orders since last sync)
            result = self.sync_service.incremental_sync(market=None)

            duration = (datetime.now() - start_time).total_seconds()

            if result['success']:
                print(f"\n[BackgroundSync] SUCCESS: Sync completed in {duration:.1f}s")
                print(f"[BackgroundSync] New orders synced: {result['synced_count']}")

                if result['synced_count'] > 0:
                    print(f"[BackgroundSync] Latest order: {result.get('latest_order_time', 'N/A')}")
            else:
                print(f"\n[BackgroundSync] WARNING: Sync failed: {result.get('error')}")
                print(f"[BackgroundSync] Orders synced before failure: {result['synced_count']}")

        except Exception as e:
            print(f"\n[BackgroundSync] ERROR: Unexpected error: {e}")
            import traceback
            traceback.print_exc()

        print(f"{'='*60}\n")

    def sync_now(self):
        """
        Trigger immediate incremental sync (can be called from API endpoint).

        Returns:
            dict: Sync result
        """
        print("[BackgroundSync] Manual sync triggered")
        return self.sync_service.incremental_sync(market=None)
