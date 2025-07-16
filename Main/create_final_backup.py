#!/usr/bin/env python3
"""
Create final backup of circuit tables before exit
"""

import os
import psycopg2
from datetime import datetime
import subprocess
import sys

# Create timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_dir = f'/usr/local/bin/circuit_backups_{timestamp}'

print(f'Creating backup directory: {backup_dir}')
os.makedirs(backup_dir, exist_ok=True)

# Database connection
db_config = {
    'host': 'localhost',
    'port': '5432',
    'user': 'dsruser',
    'password': 'dsrpass123',
    'database': 'dsrcircuits'
}

# Create pg_dump backups
os.environ['PGPASSWORD'] = db_config['password']

print('Backing up enriched_circuits table...')
result = subprocess.run([
    'pg_dump',
    '-h', db_config['host'],
    '-p', db_config['port'],
    '-U', db_config['user'],
    '-d', db_config['database'],
    '-t', 'enriched_circuits',
    '-f', f'{backup_dir}/enriched_circuits_backup_{timestamp}.sql'
], capture_output=True, text=True)

if result.returncode != 0:
    print(f"Error backing up enriched_circuits: {result.stderr}")
    sys.exit(1)

print('Backing up circuits table...')
result = subprocess.run([
    'pg_dump',
    '-h', db_config['host'],
    '-p', db_config['port'],
    '-U', db_config['user'],
    '-d', db_config['database'],
    '-t', 'circuits',
    '-f', f'{backup_dir}/circuits_backup_{timestamp}.sql'
], capture_output=True, text=True)

if result.returncode != 0:
    print(f"Error backing up circuits: {result.stderr}")
    sys.exit(1)

# Get record counts
conn = psycopg2.connect(**db_config)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM enriched_circuits")
enriched_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM circuits WHERE status = 'Enabled'")
circuits_enabled_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM circuits")
circuits_total_count = cursor.fetchone()[0]

conn.close()

# Create restore script
restore_script = f'''#!/bin/bash
# Emergency restore script created {timestamp}
# Usage: ./restore_circuit_tables.sh

echo "=== Circuit Tables Restore Script ==="
echo "This will restore circuits and enriched_circuits tables from backup"
echo "Backup timestamp: {timestamp}"
echo
read -p "Are you sure you want to restore? This will DELETE current data! (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 1
fi

# Database connection details
export PGPASSWORD='dsrpass123'
DB_HOST='localhost'
DB_PORT='5432'
DB_USER='dsruser'
DB_NAME='dsrcircuits'

echo "Restoring enriched_circuits table..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "TRUNCATE TABLE enriched_circuits CASCADE;"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f {backup_dir}/enriched_circuits_backup_{timestamp}.sql

echo "Restoring circuits table..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "TRUNCATE TABLE circuits CASCADE;"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f {backup_dir}/circuits_backup_{timestamp}.sql

echo "Restore complete!"
'''

restore_file = f'{backup_dir}/restore_circuit_tables_{timestamp}.sh'
with open(restore_file, 'w') as f:
    f.write(restore_script)

os.chmod(restore_file, 0o755)

# Create summary
summary = f'''Circuit Tables Backup Summary
==================================================
Backup Date: {datetime.now()}
Backup Location: {backup_dir}
Database: {db_config['database']}
Host: {db_config['host']}

Tables Backed Up:
- enriched_circuits: {enriched_count:,} records
- circuits: {circuits_total_count:,} total records ({circuits_enabled_count:,} enabled)

Key Information:
- Includes all DSR-ARIN matched fixes (870 sites)
- Includes WAN2 cellular provider updates (53 circuits)
- New nightly script deployed at: /usr/local/bin/Main/nightly/nightly_enriched_db.py
- Script will run at 3:00 AM preserving all fixes

Restore Instructions:
1. Run: {restore_file}
2. Or manually restore using psql with the .sql files

Previous Backup:
- /usr/local/bin/circuit_backups_20250710_202818/ (created during deployment)
'''

with open(f'{backup_dir}/backup_summary.txt', 'w') as f:
    f.write(summary)

print(f'\nBackup complete!')
print(f'Location: {backup_dir}')
print(f'Restore script: {restore_file}')
print(f'\nRecord counts:')
print(f'- enriched_circuits: {enriched_count:,} records')
print(f'- circuits: {circuits_total_count:,} total ({circuits_enabled_count:,} enabled)')
print(f'\nBoth current and previous backups are available for recovery if needed.')