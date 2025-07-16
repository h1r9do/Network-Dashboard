#!/usr/bin/env python3
"""
Force sync all circuits from tracking CSV to fix mismatches
This ensures the database exactly matches the tracking CSV
"""
import psycopg2
import pandas as pd
import sys
import os
from datetime import datetime

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

def main():
    print("Force Sync from Tracking CSV")
    print("=" * 60)
    
    # Read tracking CSV
    csv_file = '/var/www/html/circuitinfo/tracking_data_2025-07-14.csv'
    print(f"Reading {csv_file}...")
    df = pd.read_csv(csv_file, low_memory=False)
    
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Find all mismatches
    print("\nFinding status mismatches...")
    mismatches = []
    
    for _, row in df.iterrows():
        record_num = row.get('record_number')
        if pd.isna(record_num) or not record_num:
            continue
            
        csv_status = row.get('status', '')
        
        # Check database
        cursor.execute("""
            SELECT status, manual_override
            FROM circuits
            WHERE record_number = %s
        """, (record_num,))
        
        db_result = cursor.fetchone()
        
        if db_result and db_result[0] != csv_status and not pd.isna(csv_status):
            mismatches.append({
                'record_number': record_num,
                'csv_status': csv_status,
                'db_status': db_result[0],
                'manual_override': db_result[1]
            })
    
    print(f"Found {len(mismatches)} mismatches")
    
    if mismatches:
        print("\nUpdating mismatched records...")
        updated = 0
        
        for m in mismatches:
            if not m['manual_override']:  # Only update if not manually overridden
                cursor.execute("""
                    UPDATE circuits
                    SET status = %s,
                        last_csv_file = 'tracking_data_2025-07-14.csv',
                        updated_at = NOW()
                    WHERE record_number = %s
                    AND manual_override IS NOT TRUE
                """, (m['csv_status'], m['record_number']))
                
                if cursor.rowcount > 0:
                    updated += 1
                    print(f"  Updated {m['record_number']}: {m['db_status']} → {m['csv_status']}")
        
        conn.commit()
        print(f"\n✓ Updated {updated} records")
        
        # Verify
        still_mismatched = 0
        for m in mismatches:
            cursor.execute("SELECT status FROM circuits WHERE record_number = %s", (m['record_number'],))
            result = cursor.fetchone()
            if result and result[0] != m['csv_status']:
                still_mismatched += 1
                
        if still_mismatched > 0:
            print(f"\n⚠ Warning: {still_mismatched} records still mismatched (may have manual_override=TRUE)")
    else:
        print("\n✓ No mismatches found - database is in sync with tracking CSV")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()