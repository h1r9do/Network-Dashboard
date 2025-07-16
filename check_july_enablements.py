#!/usr/bin/env python3
"""Check for actual enablements that should be tracked"""

import sys
sys.path.insert(0, '.')
from config import Config
import psycopg2
import pandas as pd
import re

# Connect to database
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
user, password, host, port, database = match.groups()

conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
cursor = conn.cursor()

print("Checking for Ready->Enabled transitions on July 1-2")
print("=" * 80)

# Check July 1 CSV vs June 30 CSV
csv_files = {
    '2025-06-30': '/var/www/html/circuitinfo/tracking_data_2025-06-30.csv',
    '2025-07-01': '/var/www/html/circuitinfo/tracking_data_2025-07-01.csv',
    '2025-07-02': '/var/www/html/circuitinfo/tracking_data_2025-07-02.csv'
}

# Read the CSV files
dfs = {}
for date, file in csv_files.items():
    try:
        df = pd.read_csv(file, low_memory=False)
        dfs[date] = df
        print(f"\nLoaded {date}: {len(df)} rows")
    except Exception as e:
        print(f"Error loading {date}: {e}")

# Check for Ready->Enabled transitions
print("\n\nChecking for transitions:")
print("-" * 80)

# June 30 -> July 1
if '2025-06-30' in dfs and '2025-07-01' in dfs:
    df_prev = dfs['2025-06-30']
    df_curr = dfs['2025-07-01']
    
    # Create lookup by Site ID
    prev_status = {}
    for _, row in df_prev.iterrows():
        site_id = str(row['Site ID']).strip()
        status = str(row['status']).lower().strip()
        prev_status[site_id] = status
    
    # Check for transitions
    transitions = []
    for _, row in df_curr.iterrows():
        site_id = str(row['Site ID']).strip()
        curr_status = str(row['status']).lower().strip()
        
        if site_id in prev_status:
            prev = prev_status[site_id]
            if 'ready for enablement' in prev and 'enabled' in curr_status and 'ready for enablement' not in curr_status:
                transitions.append({
                    'site_name': row['Site Name'],
                    'site_id': site_id,
                    'prev_status': prev,
                    'curr_status': curr_status
                })
    
    print(f"\nJune 30 -> July 1: {len(transitions)} transitions")
    for t in transitions:
        print(f"  {t['site_name']} ({t['site_id']}): '{t['prev_status']}' -> '{t['curr_status']}'")

# July 1 -> July 2
if '2025-07-01' in dfs and '2025-07-02' in dfs:
    df_prev = dfs['2025-07-01']
    df_curr = dfs['2025-07-02']
    
    # Create lookup by Site ID
    prev_status = {}
    for _, row in df_prev.iterrows():
        site_id = str(row['Site ID']).strip()
        status = str(row['status']).lower().strip()
        prev_status[site_id] = status
    
    # Check for transitions
    transitions = []
    for _, row in df_curr.iterrows():
        site_id = str(row['Site ID']).strip()
        curr_status = str(row['status']).lower().strip()
        
        if site_id in prev_status:
            prev = prev_status[site_id]
            if 'ready for enablement' in prev and 'enabled' in curr_status and 'ready for enablement' not in curr_status:
                transitions.append({
                    'site_name': row['Site Name'],
                    'site_id': site_id,
                    'prev_status': prev,
                    'curr_status': curr_status,
                    'provider': row.get('provider_name', ''),
                    'assigned_to': row.get('SCTASK Assignee', '')
                })
    
    print(f"\nJuly 1 -> July 2: {len(transitions)} transitions")
    for t in transitions:
        print(f"  {t['site_name']} ({t['site_id']}): '{t['prev_status']}' -> '{t['curr_status']}'")
        
    # If we found transitions, update the database
    if transitions:
        print(f"\nUpdating database with {len(transitions)} enablements for July 2...")
        
        # Update enablement_summary
        cursor.execute("""
            UPDATE enablement_summary 
            SET daily_count = %s
            WHERE summary_date = '2025-07-02'
        """, (len(transitions),))
        
        # Add individual records to daily_enablements
        for t in transitions:
            cursor.execute("""
                INSERT INTO daily_enablements (
                    date, site_name, circuit_purpose, provider_name,
                    previous_status, current_status, assigned_to, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                '2025-07-02',
                t['site_name'],
                'Unknown',  # We don't have circuit purpose in this context
                t.get('provider', ''),
                'Ready for Enablement',
                'Enabled',
                t.get('assigned_to', '')
            ))
        
        conn.commit()
        print("Database updated!")

cursor.close()
conn.close()