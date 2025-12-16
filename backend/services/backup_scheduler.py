"""
Automated Backup Scheduler

Schedules daily database backups at 02:00 AM (local time).
Integrates with backup_database.py for actual backup execution.

Features:
- Daily automatic backups
- Configurable schedule
- Error handling and logging
- Manual trigger support
"""

import schedule
import time
import threading
import subprocess
import sys
import os
from datetime import datetime


class BackupScheduler:
    def __init__(self, backup_time="02:00"):
        """
        Initialize backup scheduler

        Args:
            backup_time: Time to run backup (HH:MM format, 24-hour)
        """
        self.backup_time = backup_time
        self.running = False
        self.thread = None

        # Path to backup script
        self.backup_script = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'backup_database.py'
        )

        print(f"[BackupScheduler] Initialized with schedule: {backup_time} daily")

    def run_backup(self):
        """Execute database backup"""
        print(f"\n[BackupScheduler] Starting backup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Run backup script
            result = subprocess.run(
                [sys.executable, self.backup_script],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode == 0:
                print(f"[BackupScheduler] Backup completed successfully")
                print(result.stdout)
            else:
                print(f"[BackupScheduler] ERROR: Backup failed")
                print(result.stderr)

        except subprocess.TimeoutExpired:
            print(f"[BackupScheduler] ERROR: Backup timed out after 10 minutes")

        except Exception as e:
            print(f"[BackupScheduler] ERROR: Backup failed: {str(e)}")

    def _schedule_loop(self):
        """Main scheduling loop (runs in separate thread)"""
        print(f"[BackupScheduler] Schedule loop started")

        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

        print(f"[BackupScheduler] Schedule loop stopped")

    def start(self):
        """Start the backup scheduler"""
        if self.running:
            print(f"[BackupScheduler] WARNING: Already running")
            return

        # Schedule daily backup
        schedule.every().day.at(self.backup_time).do(self.run_backup)

        # Start background thread
        self.running = True
        self.thread = threading.Thread(target=self._schedule_loop, daemon=True)
        self.thread.start()

        print(f"[BackupScheduler] Started - Daily backups at {self.backup_time}")
        print(f"[BackupScheduler] Next backup: {schedule.next_run()}")

    def stop(self):
        """Stop the backup scheduler"""
        if not self.running:
            print(f"[BackupScheduler] WARNING: Not running")
            return

        self.running = False
        schedule.clear()

        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        print(f"[BackupScheduler] Stopped")

    def trigger_manual_backup(self):
        """Manually trigger a backup (for admin API)"""
        print(f"[BackupScheduler] Manual backup triggered")

        # Run in separate thread to avoid blocking
        backup_thread = threading.Thread(target=self.run_backup)
        backup_thread.start()

        return backup_thread


# Global instance (singleton pattern)
_scheduler_instance = None


def get_backup_scheduler():
    """Get or create backup scheduler singleton"""
    global _scheduler_instance

    if _scheduler_instance is None:
        # Get backup time from environment or use default
        backup_time = os.getenv('BACKUP_TIME', '02:00')
        _scheduler_instance = BackupScheduler(backup_time=backup_time)

    return _scheduler_instance


def start_backup_scheduler():
    """Start the backup scheduler (call from app.py)"""
    scheduler = get_backup_scheduler()
    scheduler.start()
    return scheduler


if __name__ == '__main__':
    # Test the scheduler
    print("="*70)
    print("BACKUP SCHEDULER TEST")
    print("="*70)

    # Create scheduler with 1-minute interval for testing
    test_scheduler = BackupScheduler(backup_time="00:00")  # Won't trigger in test

    # Trigger manual backup for testing
    print("\nTriggering manual backup...")
    test_scheduler.trigger_manual_backup()

    print("\nWaiting for backup to complete...")
    time.sleep(5)

    print("\nTest complete!")
