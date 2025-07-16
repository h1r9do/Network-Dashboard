#!/usr/bin/env python3
"""
Fix the enablement ready queue counts to count ALL circuits, not just unique Site IDs
"""

import sys
sys.path.insert(0, '.')
from config import Config
import psycopg2
import pandas as pd
import glob
from datetime import datetime, timedelta
import re

# Get database connection
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
user, password, host, port, database = match.groups()

conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
cursor = conn.cursor()

print("Fixing Ready Queue Counts - Counting ALL Circuits")
print("=" * 80)

# Get CSV files for the past 90 days
csv_dir = "/var/www/html/circuitinfo"
csv_files = sorted(glob.glob(f"{csv_dir}/tracking_data_*.csv"))

# Filter for recent files
cutoff_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
csv_files = [f for f in csv_files if f.split('tracking_data_')[1][:10] >= cutoff_date]

print(f"Processing {len(csv_files)} CSV files...")

# Clear and rebuild ready_queue_daily
cursor.execute("DELETE FROM ready_queue_daily WHERE summary_date >= CURRENT_DATE - INTERVAL '90 days'")

for csv_file in csv_files:
    # Extract date from filename
    filename = csv_file.split('/')[-1]
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if not date_match:
        continue
    
    file_date = date_match.group(1)
    
    try:
        # Read CSV and count ALL circuits in ready status
        df = pd.read_csv(csv_file, low_memory=False)
        
        # Count ALL circuits with "Ready for Enablement" status
        ready_circuits = df[df['status'].str.lower() == 'ready for enablement']
        ready_count = len(ready_circuits)
        
        # Insert corrected count
        cursor.execute("""
            INSERT INTO ready_queue_daily (summary_date, ready_count, created_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (summary_date) DO UPDATE SET
                ready_count = EXCLUDED.ready_count,
                created_at = NOW()
        """, (file_date, ready_count))
        
        print(f"{file_date}: {ready_count} circuits")
        
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")
        continue

# Commit changes
conn.commit()

print("\nVerifying corrected counts...")
cursor.execute("""
    SELECT summary_date, ready_count 
    FROM ready_queue_daily 
    WHERE summary_date >= '2025-06-22'
    ORDER BY summary_date
""")

print("\nCorrected Ready Queue Counts:")
print("-" * 30)
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]} circuits")

cursor.close()
conn.close()

print("\nReady queue counts have been corrected!")
print("The enablement report should now show accurate counts.")