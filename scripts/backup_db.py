"""
Database Backup Utility for NyayVeya Online Legal Drafting Platform.
Supports automatic timestamped snapshots for SQLite and export instructions for MySQL.

Usage:
  python scripts/backup_db.py
"""
import os
import shutil
import datetime
import sys

# Ensure root folder is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app


def perform_backup(app=None):
    if app is None:
        app = create_app()
    with app.app_context():
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backups_dir = os.path.abspath(os.path.join(app.root_path, '..', 'backups'))
        os.makedirs(backups_dir, exist_ok=True)

        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        print(f"[*] Inspecting database connection: {db_uri.split('@')[-1] if '@' in db_uri else db_uri}")

        if 'sqlite:///' in db_uri:
            db_path = db_uri.replace('sqlite:///', '')
            if os.name == 'nt' and db_path.startswith('/'):
                db_path = db_path[1:]
            db_path = os.path.abspath(db_path)

            if os.path.exists(db_path):
                dest_path = os.path.join(backups_dir, f"nyayveya_sqlite_{timestamp}.db")
                shutil.copy2(db_path, dest_path)
                file_size_kb = round(os.path.getsize(dest_path) / 1024, 2)
                print(f"[+] Backup successfully created: {dest_path} ({file_size_kb} KB)")
                return dest_path
            else:
                print(f"[-] SQLite file not found at: {db_path}")
                return None
        elif 'mysql' in db_uri:
            print("[+] Production MySQL configured.")
            print(f"    Automated command: mysqldump --single-transaction -u [user] -p [dbname] > backups/mysql_{timestamp}.sql")
            return None


if __name__ == '__main__':
    perform_backup()
