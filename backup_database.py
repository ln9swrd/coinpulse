"""
Automated Database Backup Script

Supports both SQLite and PostgreSQL backups with retention management.

Usage:
    python backup_database.py                    # Create backup
    python backup_database.py --clean            # Clean old backups
    python backup_database.py --restore <file>   # Restore from backup
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv
import argparse

# Load environment variables
load_dotenv()


class DatabaseBackup:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL', 'sqlite:///data/coinpulse.db')
        self.backup_dir = os.getenv('BACKUP_DIR', 'backups/database_backups')
        self.retention_days = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
        self.db_type = self._get_db_type()

        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)

    def _get_db_type(self):
        """Determine database type"""
        if self.db_url.startswith('postgresql'):
            return 'postgresql'
        elif self.db_url.startswith('sqlite'):
            return 'sqlite'
        return 'unknown'

    def create_backup(self):
        """Create database backup"""
        print("="*70)
        print("DATABASE BACKUP")
        print("="*70)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if self.db_type == 'sqlite':
            return self._backup_sqlite(timestamp)
        elif self.db_type == 'postgresql':
            return self._backup_postgresql(timestamp)
        else:
            print(f"[ERROR] Unsupported database type: {self.db_type}")
            return False

    def _backup_sqlite(self, timestamp):
        """Backup SQLite database"""
        # Extract SQLite file path from URL
        sqlite_path = self.db_url.replace('sqlite:///', '')

        if not os.path.exists(sqlite_path):
            print(f"[ERROR] SQLite database not found: {sqlite_path}")
            return False

        backup_file = os.path.join(
            self.backup_dir,
            f"coinpulse_sqlite_{timestamp}.db"
        )

        print(f"[INFO] Source: {sqlite_path}")
        print(f"[INFO] Target: {backup_file}")
        print(f"[INFO] Copying database file...")

        try:
            shutil.copy2(sqlite_path, backup_file)

            # Get file size
            size_mb = os.path.getsize(backup_file) / (1024 * 1024)

            print(f"[SUCCESS] Backup created: {backup_file}")
            print(f"[INFO] Size: {size_mb:.2f} MB")

            return True

        except Exception as e:
            print(f"[ERROR] Backup failed: {str(e)}")
            return False

    def _backup_postgresql(self, timestamp):
        """Backup PostgreSQL database using pg_dump"""
        # Parse PostgreSQL connection string
        # Format: postgresql://user:password@host:port/database
        try:
            url_parts = self.db_url.replace('postgresql://', '').split('@')
            user_pass = url_parts[0].split(':')
            host_db = url_parts[1].split('/')

            user = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else ''
            host_port = host_db[0].split(':')
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else '5432'
            database = host_db[1]

            backup_file = os.path.join(
                self.backup_dir,
                f"coinpulse_pg_{timestamp}.sql"
            )

            print(f"[INFO] Database: {database}@{host}:{port}")
            print(f"[INFO] Target: {backup_file}")
            print(f"[INFO] Running pg_dump...")

            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = password

            # Run pg_dump
            cmd = [
                'pg_dump',
                '-h', host,
                '-p', port,
                '-U', user,
                '-F', 'c',  # Custom format (compressed)
                '-f', backup_file,
                database
            ]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                size_mb = os.path.getsize(backup_file) / (1024 * 1024)
                print(f"[SUCCESS] Backup created: {backup_file}")
                print(f"[INFO] Size: {size_mb:.2f} MB")
                return True
            else:
                print(f"[ERROR] pg_dump failed:")
                print(result.stderr)
                return False

        except Exception as e:
            print(f"[ERROR] Backup failed: {str(e)}")
            return False

    def clean_old_backups(self):
        """Remove backups older than retention period"""
        print("="*70)
        print("CLEANING OLD BACKUPS")
        print("="*70)

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        print(f"[INFO] Retention period: {self.retention_days} days")
        print(f"[INFO] Removing backups older than: {cutoff_date.strftime('%Y-%m-%d')}")

        if not os.path.exists(self.backup_dir):
            print(f"[INFO] No backup directory found")
            return 0

        removed_count = 0
        total_size = 0

        for filename in os.listdir(self.backup_dir):
            if not filename.startswith('coinpulse'):
                continue

            filepath = os.path.join(self.backup_dir, filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(filepath))

            if file_time < cutoff_date:
                size = os.path.getsize(filepath)
                total_size += size
                os.remove(filepath)
                print(f"[REMOVED] {filename} ({size/(1024*1024):.2f} MB)")
                removed_count += 1

        if removed_count > 0:
            print(f"\n[SUCCESS] Removed {removed_count} old backup(s)")
            print(f"[INFO] Freed space: {total_size/(1024*1024):.2f} MB")
        else:
            print(f"[INFO] No old backups to remove")

        return removed_count

    def list_backups(self):
        """List all available backups"""
        print("="*70)
        print("AVAILABLE BACKUPS")
        print("="*70)

        if not os.path.exists(self.backup_dir):
            print("[INFO] No backups found")
            return []

        backups = []

        for filename in os.listdir(self.backup_dir):
            if not filename.startswith('coinpulse'):
                continue

            filepath = os.path.join(self.backup_dir, filename)
            size = os.path.getsize(filepath)
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))

            backups.append({
                'filename': filename,
                'filepath': filepath,
                'size_mb': size / (1024 * 1024),
                'created': mtime
            })

        backups.sort(key=lambda x: x['created'], reverse=True)

        if backups:
            print(f"\nFound {len(backups)} backup(s):\n")
            for backup in backups:
                print(f"  {backup['filename']}")
                print(f"    Created: {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"    Size: {backup['size_mb']:.2f} MB\n")
        else:
            print("[INFO] No backups found")

        return backups

    def restore_backup(self, backup_file):
        """Restore database from backup"""
        print("="*70)
        print("DATABASE RESTORE")
        print("="*70)

        if not os.path.exists(backup_file):
            print(f"[ERROR] Backup file not found: {backup_file}")
            return False

        print(f"[WARNING] This will overwrite the current database!")
        print(f"[INFO] Backup file: {backup_file}")

        if input("\nContinue? (yes/no): ").lower() != 'yes':
            print("[INFO] Restore cancelled")
            return False

        if self.db_type == 'sqlite':
            return self._restore_sqlite(backup_file)
        elif self.db_type == 'postgresql':
            return self._restore_postgresql(backup_file)

        return False

    def _restore_sqlite(self, backup_file):
        """Restore SQLite database"""
        sqlite_path = self.db_url.replace('sqlite:///', '')

        print(f"[INFO] Restoring to: {sqlite_path}")

        try:
            # Create backup of current database
            if os.path.exists(sqlite_path):
                current_backup = f"{sqlite_path}.before_restore"
                shutil.copy2(sqlite_path, current_backup)
                print(f"[INFO] Current database backed up to: {current_backup}")

            # Restore
            shutil.copy2(backup_file, sqlite_path)

            print(f"[SUCCESS] Database restored from: {backup_file}")
            return True

        except Exception as e:
            print(f"[ERROR] Restore failed: {str(e)}")
            return False

    def _restore_postgresql(self, backup_file):
        """Restore PostgreSQL database using pg_restore"""
        # Parse connection string
        try:
            url_parts = self.db_url.replace('postgresql://', '').split('@')
            user_pass = url_parts[0].split(':')
            host_db = url_parts[1].split('/')

            user = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else ''
            host_port = host_db[0].split(':')
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else '5432'
            database = host_db[1]

            print(f"[INFO] Database: {database}@{host}:{port}")
            print(f"[INFO] Running pg_restore...")

            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = password

            # Run pg_restore
            cmd = [
                'pg_restore',
                '-h', host,
                '-p', port,
                '-U', user,
                '-d', database,
                '-c',  # Clean (drop) database objects before recreating
                backup_file
            ]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"[SUCCESS] Database restored from: {backup_file}")
                return True
            else:
                print(f"[ERROR] pg_restore failed:")
                print(result.stderr)
                return False

        except Exception as e:
            print(f"[ERROR] Restore failed: {str(e)}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Database Backup Tool')
    parser.add_argument('--clean', action='store_true', help='Clean old backups')
    parser.add_argument('--list', action='store_true', help='List available backups')
    parser.add_argument('--restore', metavar='FILE', help='Restore from backup file')

    args = parser.parse_args()

    backup = DatabaseBackup()

    if args.clean:
        backup.clean_old_backups()
    elif args.list:
        backup.list_backups()
    elif args.restore:
        success = backup.restore_backup(args.restore)
        sys.exit(0 if success else 1)
    else:
        # Default: create backup
        success = backup.create_backup()

        # Auto-clean old backups after successful backup
        if success:
            print("\n")
            backup.clean_old_backups()

        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
