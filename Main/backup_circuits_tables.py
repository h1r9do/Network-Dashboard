#!/usr/bin/env python3
"""
Create comprehensive backup of circuits and related tables
Includes both SQL dump and CSV exports for easy restoration
"""
import os
import sys
import psycopg2
import pandas as pd
from datetime import datetime
import subprocess
import gzip

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config
import re

def get_db_connection():
    """Get database connection using config"""
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )

def create_backup_directory():
    """Create backup directory with timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"/var/www/html/backups/circuits_backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    print(f"Created backup directory: {backup_dir}")
    return backup_dir

def backup_table_to_csv(cursor, table_name, backup_dir):
    """Backup a single table to CSV"""
    try:
        # Get all data from table
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # Get column names
        column_names = [desc[0] for desc in cursor.description]
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(rows, columns=column_names)
        csv_path = os.path.join(backup_dir, f"{table_name}.csv")
        df.to_csv(csv_path, index=False)
        
        # Also create a compressed version
        gz_path = f"{csv_path}.gz"
        with open(csv_path, 'rb') as f_in:
            with gzip.open(gz_path, 'wb') as f_out:
                f_out.writelines(f_in)
        
        print(f"  ✓ Backed up {table_name}: {len(rows)} rows")
        return True
        
    except Exception as e:
        print(f"  ✗ Error backing up {table_name}: {e}")
        return False

def create_sql_dump(backup_dir):
    """Create SQL dump of entire database"""
    try:
        # Parse connection details
        match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
        if not match:
            raise ValueError("Invalid database URI")
        
        user, password, host, port, database = match.groups()
        
        # Create pg_dump command
        dump_file = os.path.join(backup_dir, f"dsrcircuits_full_dump.sql")
        
        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        # Run pg_dump
        cmd = [
            'pg_dump',
            '-h', host,
            '-p', port,
            '-U', user,
            '-d', database,
            '-f', dump_file,
            '--verbose',
            '--no-owner',
            '--no-privileges'
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Compress the dump
            gz_file = f"{dump_file}.gz"
            with open(dump_file, 'rb') as f_in:
                with gzip.open(gz_file, 'wb') as f_out:
                    f_out.writelines(f_in)
            print(f"  ✓ Created full database dump: {gz_file}")
            
            # Remove uncompressed file to save space
            os.remove(dump_file)
            return True
        else:
            print(f"  ✗ Error creating database dump: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ✗ Error creating database dump: {e}")
        return False

def create_restore_script(backup_dir):
    """Create a restore script for easy restoration"""
    script_content = f"""#!/bin/bash
# Restore script for circuits backup
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

BACKUP_DIR="{backup_dir}"

echo "Circuit Database Restore Script"
echo "==============================="
echo "This will restore from backup at: $BACKUP_DIR"
echo ""
echo "WARNING: This will overwrite current data!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Restore from SQL dump
if [ -f "$BACKUP_DIR/dsrcircuits_full_dump.sql.gz" ]; then
    echo "Restoring from SQL dump..."
    gunzip -c "$BACKUP_DIR/dsrcircuits_full_dump.sql.gz" | sudo -u postgres psql dsrcircuits
    echo "✓ Database restored from SQL dump"
else
    echo "✗ SQL dump not found"
fi

echo ""
echo "Restore complete!"
echo "You may need to restart the Flask application: sudo systemctl restart meraki-dsrcircuits"
"""
    
    script_path = os.path.join(backup_dir, "restore.sh")
    with open(script_path, 'w') as f:
        f.write(script_content)
    os.chmod(script_path, 0o755)
    print(f"  ✓ Created restore script: {script_path}")

def main():
    print("Creating comprehensive backup of circuits database...")
    print("=" * 60)
    
    try:
        # Create backup directory
        backup_dir = create_backup_directory()
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # List of critical tables to backup
        tables_to_backup = [
            'circuits',
            'circuit_history',
            'circuit_assignments',
            'enriched_circuits',
            'enrichment_change_tracking',
            'new_stores',
            'meraki_inventory',
            'provider_mappings',
            'daily_enablements',
            'enablement_summary'
        ]
        
        print("\nBacking up individual tables to CSV:")
        for table in tables_to_backup:
            backup_table_to_csv(cursor, table, backup_dir)
        
        print("\nCreating full database dump:")
        create_sql_dump(backup_dir)
        
        print("\nCreating restore script:")
        create_restore_script(backup_dir)
        
        # Create a summary file
        summary_path = os.path.join(backup_dir, "backup_summary.txt")
        with open(summary_path, 'w') as f:
            f.write(f"Circuits Database Backup Summary\n")
            f.write(f"================================\n")
            f.write(f"Backup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Backup Location: {backup_dir}\n")
            f.write(f"Tables Backed Up: {', '.join(tables_to_backup)}\n")
            f.write(f"\nTo restore, run: {os.path.join(backup_dir, 'restore.sh')}\n")
        
        print("\n" + "=" * 60)
        print(f"✓ Backup complete!")
        print(f"✓ Location: {backup_dir}")
        print(f"✓ To restore, run: {os.path.join(backup_dir, 'restore.sh')}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n✗ Backup failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())