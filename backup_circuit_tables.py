#!/usr/bin/env python3
"""
Backup circuits and enriched_circuits tables before implementing new nightly script
Creates both SQL dumps and CSV exports for safety
"""

import psycopg2
import subprocess
import os
from datetime import datetime
from config import Config
import re
import csv

def get_db_config():
    """Extract database configuration from SQLAlchemy URI"""
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    return {
        'user': user,
        'password': password,
        'host': host,
        'port': port,
        'database': database
    }

def backup_table_to_sql(table_name, config, backup_dir):
    """Create SQL dump of a table using pg_dump"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{backup_dir}/{table_name}_backup_{timestamp}.sql"
    
    # Set PGPASSWORD environment variable
    env = os.environ.copy()
    env['PGPASSWORD'] = config['password']
    
    cmd = [
        'pg_dump',
        '-h', config['host'],
        '-p', config['port'],
        '-U', config['user'],
        '-d', config['database'],
        '-t', table_name,
        '--data-only',
        '--no-owner',
        '--no-privileges',
        '-f', filename
    ]
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ SQL backup created: {filename}")
            # Also create a schema-only backup
            schema_filename = f"{backup_dir}/{table_name}_schema_{timestamp}.sql"
            schema_cmd = cmd[:-2] + ['--schema-only', '-f', schema_filename]
            subprocess.run(schema_cmd, env=env)
            print(f"✅ Schema backup created: {schema_filename}")
            return filename
        else:
            print(f"❌ Error creating SQL backup: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Error running pg_dump: {e}")
        return None

def backup_table_to_csv(table_name, conn, backup_dir):
    """Export table data to CSV for easy inspection"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{backup_dir}/{table_name}_backup_{timestamp}.csv"
    
    cursor = conn.cursor()
    
    try:
        # Get column names
        cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s 
            ORDER BY ordinal_position
        """, (table_name,))
        columns = [row[0] for row in cursor.fetchall()]
        
        # Export data
        cursor.execute(f"SELECT * FROM {table_name}")
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)
            
            row_count = 0
            for row in cursor:
                writer.writerow(row)
                row_count += 1
        
        print(f"✅ CSV backup created: {filename} ({row_count} rows)")
        return filename
        
    except Exception as e:
        print(f"❌ Error creating CSV backup: {e}")
        return None
    finally:
        cursor.close()

def create_restore_script(backup_dir, timestamp):
    """Create a restore script for emergency use"""
    script_content = f"""#!/bin/bash
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
export PGPASSWORD='{Config.SQLALCHEMY_DATABASE_URI.split(':')[2].split('@')[0]}'
DB_HOST='{Config.SQLALCHEMY_DATABASE_URI.split('@')[1].split(':')[0]}'
DB_PORT='{Config.SQLALCHEMY_DATABASE_URI.split(':')[3].split('/')[0]}'
DB_USER='{Config.SQLALCHEMY_DATABASE_URI.split('://')[1].split(':')[0]}'
DB_NAME='{Config.SQLALCHEMY_DATABASE_URI.split('/')[-1]}'

echo "Restoring enriched_circuits table..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "TRUNCATE TABLE enriched_circuits CASCADE;"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f {backup_dir}/enriched_circuits_backup_{timestamp}.sql

echo "Restoring circuits table..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "TRUNCATE TABLE circuits CASCADE;"
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f {backup_dir}/circuits_backup_{timestamp}.sql

echo "Restore complete!"
"""
    
    script_filename = f"{backup_dir}/restore_circuit_tables_{timestamp}.sh"
    with open(script_filename, 'w') as f:
        f.write(script_content)
    
    os.chmod(script_filename, 0o755)
    print(f"✅ Restore script created: {script_filename}")
    return script_filename

def main():
    """Main backup function"""
    print("=== Circuit Tables Backup Script ===")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    print(f"Timestamp: {timestamp}")
    
    # Create backup directory
    backup_dir = f"/usr/local/bin/circuit_backups_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    print(f"Backup directory: {backup_dir}")
    
    # Get database configuration
    config = get_db_config()
    
    # Connect to database
    conn = psycopg2.connect(
        host=config['host'],
        port=int(config['port']),
        database=config['database'],
        user=config['user'],
        password=config['password']
    )
    
    # Get table sizes
    cursor = conn.cursor()
    for table in ['circuits', 'enriched_circuits']:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"\n{table} table: {count} rows")
    cursor.close()
    
    print("\nCreating backups...")
    
    # Backup enriched_circuits table
    print("\n1. Backing up enriched_circuits table:")
    backup_table_to_sql('enriched_circuits', config, backup_dir)
    backup_table_to_csv('enriched_circuits', conn, backup_dir)
    
    # Backup circuits table (this is large, so we'll be selective)
    print("\n2. Backing up circuits table:")
    backup_table_to_sql('circuits', config, backup_dir)
    
    # Create a smaller CSV backup of just enabled circuits
    print("   Creating CSV of enabled circuits only...")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT site_name, record_number, circuit_purpose, provider_name, 
               details_service_speed, status, manual_override, data_source
        FROM circuits 
        WHERE status = 'Enabled'
        ORDER BY site_name, circuit_purpose
    """)
    
    filename = f"{backup_dir}/circuits_enabled_only_{timestamp}.csv"
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['site_name', 'record_number', 'circuit_purpose', 'provider_name', 
                        'details_service_speed', 'status', 'manual_override', 'data_source'])
        row_count = 0
        for row in cursor:
            writer.writerow(row)
            row_count += 1
    
    print(f"✅ Enabled circuits CSV created: {filename} ({row_count} rows)")
    cursor.close()
    
    # Create restore script
    print("\n3. Creating restore script:")
    create_restore_script(backup_dir, timestamp)
    
    # Create a summary file
    summary_file = f"{backup_dir}/backup_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Circuit Tables Backup Summary\n")
        f.write(f"="*50 + "\n")
        f.write(f"Backup Date: {datetime.now()}\n")
        f.write(f"Backup Location: {backup_dir}\n")
        f.write(f"Database: {config['database']}\n")
        f.write(f"Host: {config['host']}\n")
        f.write(f"\nTables Backed Up:\n")
        f.write(f"- enriched_circuits (full backup)\n")
        f.write(f"- circuits (full backup)\n")
        f.write(f"\nRestore Instructions:\n")
        f.write(f"1. Run: {backup_dir}/restore_circuit_tables_{timestamp}.sh\n")
        f.write(f"2. Or manually restore using psql with the .sql files\n")
    
    print(f"\n✅ Backup summary: {summary_file}")
    
    # Close connection
    conn.close()
    
    print("\n" + "="*60)
    print("BACKUP COMPLETE!")
    print("="*60)
    print(f"All backups stored in: {backup_dir}")
    print(f"To restore, run: {backup_dir}/restore_circuit_tables_{timestamp}.sh")
    print("\nIMPORTANT: Keep this backup until you've verified the new script works correctly!")

if __name__ == "__main__":
    main()