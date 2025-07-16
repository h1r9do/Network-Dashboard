#!/usr/bin/env python3
"""
Backup the circuits table before creating Non-DSR cell/satellite circuits
"""

import sys
import os
sys.path.append('/usr/local/bin/Main')

import psycopg2
import psycopg2.extras
from datetime import datetime
import subprocess
from config import Config
import re

def get_db_connection():
    """Get database connection using SQLAlchemy URI"""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import NullPool
    
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
    url = engine.url
    
    return psycopg2.connect(
        host=url.host,
        port=url.port,
        database=url.database,
        user=url.username,
        password=url.password
    )

def backup_circuits_table():
    """Create a backup of the circuits table"""
    
    print("=== Backing up circuits table ===\n")
    
    # Get database connection details
    from sqlalchemy import create_engine
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    url = engine.url
    
    # Create timestamp for backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'/usr/local/bin/Main/backups/circuits_table_backup_{timestamp}.sql'
    
    # Ensure backup directory exists
    os.makedirs('/usr/local/bin/Main/backups', exist_ok=True)
    
    # Create pg_dump command
    dump_cmd = [
        'pg_dump',
        '-h', url.host,
        '-p', str(url.port),
        '-U', url.username,
        '-d', url.database,
        '-t', 'circuits',  # Only backup circuits table
        '--data-only',     # Data only (structure exists)
        '--inserts',       # Use INSERT statements
        '-f', backup_file
    ]
    
    # Set PGPASSWORD environment variable
    env = os.environ.copy()
    env['PGPASSWORD'] = url.password
    
    try:
        # Run pg_dump
        result = subprocess.run(dump_cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Backup created successfully: {backup_file}")
            
            # Get file size
            file_size = os.path.getsize(backup_file)
            print(f"  File size: {file_size:,} bytes")
            
            # Count records in backup
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM circuits")
            record_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"  Records backed up: {record_count:,}")
            
            return backup_file
        else:
            print(f"✗ Backup failed: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"✗ Error creating backup: {e}")
        return None

def verify_backup(backup_file):
    """Verify the backup file is valid"""
    
    print(f"\n=== Verifying backup ===")
    
    if not os.path.exists(backup_file):
        print("✗ Backup file not found")
        return False
    
    # Check file has content
    with open(backup_file, 'r') as f:
        content = f.read()
        
    if 'INSERT INTO' not in content:
        print("✗ Backup file doesn't contain INSERT statements")
        return False
    
    # Count INSERT statements
    insert_count = content.count('INSERT INTO')
    print(f"✓ Backup contains {insert_count} INSERT statements")
    
    return True

def create_restore_script(backup_file):
    """Create a restore script for easy recovery"""
    
    restore_script = backup_file.replace('.sql', '_restore.sh')
    
    from sqlalchemy import create_engine
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    url = engine.url
    
    script_content = f"""#!/bin/bash
# Restore script for circuits table
# Created: {datetime.now()}

echo "This will DELETE all current circuits and restore from backup!"
echo "Backup file: {backup_file}"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 1
fi

# Set password
export PGPASSWORD='{url.password}'

# Truncate table and restore
psql -h {url.host} -p {url.port} -U {url.username} -d {url.database} << EOF
BEGIN;
TRUNCATE TABLE circuits CASCADE;
\\i {backup_file}
COMMIT;
EOF

echo "Restore completed!"
"""
    
    with open(restore_script, 'w') as f:
        f.write(script_content)
    
    os.chmod(restore_script, 0o755)
    print(f"\n✓ Restore script created: {restore_script}")
    print(f"  To restore, run: {restore_script}")

def main():
    """Main backup process"""
    
    # Create backup
    backup_file = backup_circuits_table()
    
    if backup_file:
        # Verify backup
        if verify_backup(backup_file):
            # Create restore script
            create_restore_script(backup_file)
            
            print(f"\n=== Backup Complete ===")
            print(f"✓ Backup file: {backup_file}")
            print(f"✓ Restore script: {backup_file.replace('.sql', '_restore.sh')}")
            print(f"\nYou can now safely proceed with creating Non-DSR circuits")
        else:
            print(f"\n✗ Backup verification failed!")
    else:
        print(f"\n✗ Backup creation failed!")

if __name__ == "__main__":
    main()