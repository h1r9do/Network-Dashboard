#!/usr/bin/env python3
"""
Update enablement tracking to count ANY status change to Enabled
"""

import sys
sys.path.insert(0, '.')
from config import Config
import psycopg2
import pandas as pd
import glob
from datetime import datetime, timedelta
import re

# Connect to database
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
user, password, host, port, database = match.groups()

conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
cursor = conn.cursor()

print("Updating Enablement Tracking Logic")
print("=" * 80)
print("NEW LOGIC: Count ANY circuit that changes to 'Enabled' status")
print("=" * 80)

# Get all CSV files
csv_dir = "/var/www/html/circuitinfo"
csv_files = sorted(glob.glob(f"{csv_dir}/tracking_data_*.csv"))

# Filter for last 90 days
cutoff_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
csv_files = [f for f in csv_files if f.split('tracking_data_')[1][:10] >= cutoff_date]

print(f"\nProcessing {len(csv_files)} CSV files...")

# Clear existing data
cursor.execute("DELETE FROM daily_enablements WHERE date >= CURRENT_DATE - INTERVAL '90 days'")
cursor.execute("DELETE FROM enablement_summary WHERE summary_date >= CURRENT_DATE - INTERVAL '90 days'")

# Track enabled circuits by Site ID
previous_enabled = {}
total_enablements = 0

for i, csv_file in enumerate(csv_files):
    # Extract date from filename
    filename = csv_file.split('/')[-1]
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if not date_match:
        continue
    
    file_date = date_match.group(1)
    
    try:
        # Read CSV
        df = pd.read_csv(csv_file, low_memory=False)
        
        # Get all enabled circuits
        current_enabled = {}
        for _, row in df.iterrows():
            site_id = str(row.get('Site ID', '')).strip()
            status = str(row.get('status', '')).lower().strip()
            
            if site_id and 'enabled' in status and 'ready' not in status:
                current_enabled[site_id] = {
                    'site_name': str(row.get('Site Name', '')).strip(),
                    'circuit_purpose': str(row.get('Circuit Purpose', '')).strip(),
                    'provider': str(row.get('provider_name', '')).strip(),
                    'status': str(row.get('status', '')).strip(),
                    'assigned_to': str(row.get('SCTASK Assignee', '')).strip(),
                    'sctask': str(row.get('SCTASK Number', '')).strip()
                }
        
        # Find new enablements (circuits that are enabled now but weren't before)
        new_enablements = []
        if i > 0:  # Skip first file (no previous to compare)
            for site_id, circuit_data in current_enabled.items():
                if site_id not in previous_enabled:
                    new_enablements.append((site_id, circuit_data))
        
        # Insert individual enablement records
        for site_id, circuit in new_enablements:
            cursor.execute("""
                INSERT INTO daily_enablements (
                    date, site_name, circuit_purpose, provider_name,
                    previous_status, current_status, assigned_to, sctask, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                file_date,
                circuit['site_name'],
                circuit['circuit_purpose'],
                circuit['provider'],
                'Not Enabled',  # We don't know exact previous status
                circuit['status'],
                circuit['assigned_to'] or '',
                circuit['sctask'] or ''
            ))
        
        # Insert summary record
        cursor.execute("""
            INSERT INTO enablement_summary (
                summary_date, daily_count, created_at
            ) VALUES (%s, %s, NOW())
            ON CONFLICT (summary_date) DO UPDATE SET
                daily_count = EXCLUDED.daily_count,
                created_at = NOW()
        """, (file_date, len(new_enablements)))
        
        if len(new_enablements) > 0:
            print(f"{file_date}: {len(new_enablements)} new enablements")
            total_enablements += len(new_enablements)
            
            # Show first few examples
            for site_id, circuit in new_enablements[:3]:
                print(f"  - {circuit['site_name']} ({site_id})")
        
        # Update previous_enabled for next iteration
        previous_enabled = current_enabled
        
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")
        continue

# Commit changes
conn.commit()

print(f"\nTotal enablements tracked: {total_enablements}")

# Verify the update
print("\n" + "=" * 80)
print("VERIFICATION - Recent Enablement Summary:")
cursor.execute("""
    SELECT summary_date, daily_count 
    FROM enablement_summary 
    WHERE summary_date >= CURRENT_DATE - INTERVAL '14 days'
    ORDER BY summary_date
""")
results = cursor.fetchall()
print(f"{'Date':12} | {'Enablements':12}")
print("-" * 30)
for row in results:
    print(f"{row[0]} | {row[1]:12}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("Enablement tracking logic has been updated!")
print("The report will now show ALL circuits that become enabled each day.")