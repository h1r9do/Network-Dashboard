#!/usr/bin/env python3
"""
Diagnose why circuit updates aren't working properly
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
    print("Diagnosing Circuit Update Issues")
    print("=" * 60)
    
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Read latest tracking CSV
    csv_file = '/var/www/html/circuitinfo/tracking_data_2025-07-14.csv'
    df = pd.read_csv(csv_file, low_memory=False)
    
    # Get all circuits with status mismatches
    print("\nChecking for status mismatches between CSV and database...")
    
    mismatches = []
    
    for _, row in df.iterrows():
        record_num = row.get('record_number')
        if pd.isna(record_num) or not record_num:
            continue
            
        csv_status = row.get('status', '')
        csv_site = row.get('Site Name', '')
        csv_purpose = row.get('Circuit Purpose', '')
        
        # Check database
        cursor.execute("""
            SELECT status, site_name, circuit_purpose, manual_override, updated_at
            FROM circuits
            WHERE record_number = %s
        """, (record_num,))
        
        db_result = cursor.fetchone()
        
        if db_result:
            db_status, db_site, db_purpose, manual_override, updated_at = db_result
            
            if csv_status != db_status and not pd.isna(csv_status):
                mismatches.append({
                    'record_number': record_num,
                    'site_name': csv_site,
                    'purpose': csv_purpose,
                    'csv_status': csv_status,
                    'db_status': db_status,
                    'manual_override': manual_override,
                    'last_updated': updated_at
                })
    
    if mismatches:
        print(f"\nFound {len(mismatches)} status mismatches:")
        print("-" * 80)
        
        for m in mismatches[:20]:  # Show first 20
            print(f"\nRecord: {m['record_number']}")
            print(f"  Site: {m['site_name']} ({m['purpose']})")
            print(f"  CSV Status: {m['csv_status']}")
            print(f"  DB Status: {m['db_status']}")
            print(f"  Manual Override: {m['manual_override']}")
            print(f"  Last Updated: {m['last_updated']}")
        
        if len(mismatches) > 20:
            print(f"\n... and {len(mismatches) - 20} more mismatches")
    else:
        print("\nNo status mismatches found!")
    
    # Check for circuits in DB but not in CSV
    print("\n\nChecking for circuits in database but not in tracking CSV...")
    
    csv_records = set(df['record_number'].dropna().unique())
    
    cursor.execute("""
        SELECT record_number, site_name, status
        FROM circuits
        WHERE record_number IS NOT NULL
    """)
    
    orphaned = []
    for row in cursor.fetchall():
        if row[0] not in csv_records:
            orphaned.append(row)
    
    if orphaned:
        print(f"\nFound {len(orphaned)} circuits in DB but not in CSV:")
        for record in orphaned[:10]:
            print(f"  {record[0]}: {record[1]} - {record[2]}")
        if len(orphaned) > 10:
            print(f"  ... and {len(orphaned) - 10} more")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()