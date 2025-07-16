#!/usr/bin/env python3
"""
Rebuild enablement tracking with REAL previous status from CSV files
"""

import sys
sys.path.insert(0, '.')
from config import Config
import psycopg2
import pandas as pd
import glob
from datetime import datetime
import re
import os

# Connect to database
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
user, password, host, port, database = match.groups()

conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
cursor = conn.cursor()

print("Rebuilding Enablement Tracking with Real Previous Status")
print("=" * 80)

# Get ALL CSV files (not just last 90 days)
csv_dir = "/var/www/html/circuitinfo"
csv_files = sorted(glob.glob(f"{csv_dir}/tracking_data_*.csv"))

print(f"Processing {len(csv_files)} CSV files...")

# Clear existing data
cursor.execute("DELETE FROM daily_enablements")
cursor.execute("DELETE FROM enablement_summary")

# Track circuits and their status over time
circuit_status_history = {}  # site_id -> {date: status}
total_enablements = 0

for i, csv_file in enumerate(csv_files):
    # Extract date from filename
    filename = os.path.basename(csv_file)
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    if not date_match:
        continue
    
    file_date = date_match.group(1)
    
    try:
        # Read CSV
        df = pd.read_csv(csv_file, low_memory=False)
        
        # Track all circuits and their status
        current_statuses = {}
        for _, row in df.iterrows():
            site_id = str(row.get('Site ID', '')).strip()
            status = str(row.get('status', '')).strip()
            
            if site_id:
                current_statuses[site_id] = {
                    'site_name': str(row.get('Site Name', '')).strip(),
                    'circuit_purpose': str(row.get('Circuit Purpose', '')).strip(),
                    'provider': str(row.get('provider_name', '')).strip(),
                    'status': status,
                    'assigned_to': str(row.get('SCTASK Assignee', '')).strip(),
                    'sctask': str(row.get('SCTASK Number', '')).strip()
                }
        
        # Find circuits that became enabled today
        new_enablements = []
        for site_id, circuit_data in current_statuses.items():
            current_status = circuit_data['status'].lower()
            
            # Check if this circuit is enabled now
            if 'enabled' in current_status and 'ready' not in current_status:
                # Get previous status from history
                previous_status = None
                if site_id in circuit_status_history:
                    # Find the most recent previous status
                    prev_dates = sorted([d for d in circuit_status_history[site_id].keys() if d < file_date], reverse=True)
                    if prev_dates:
                        previous_status = circuit_status_history[site_id][prev_dates[0]]
                
                # If it wasn't enabled before (or we have no history), it's a new enablement
                if not previous_status or ('enabled' not in previous_status.lower() or 'ready' in previous_status.lower()):
                    new_enablements.append({
                        'site_id': site_id,
                        'circuit': circuit_data,
                        'previous_status': previous_status or 'No Previous Data'
                    })
        
        # Insert individual enablement records with REAL previous status
        for item in new_enablements:
            circuit = item['circuit']
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
                item['previous_status'],  # Real previous status
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
            
            # Show examples with real previous status
            for item in new_enablements[:3]:
                circuit = item['circuit']
                print(f"  - {circuit['site_name']} ({item['site_id']}): '{item['previous_status']}' → '{circuit['status']}'")
        
        # Update status history for all circuits
        for site_id, circuit_data in current_statuses.items():
            if site_id not in circuit_status_history:
                circuit_status_history[site_id] = {}
            circuit_status_history[site_id][file_date] = circuit_data['status']
        
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")
        continue

# Commit changes
conn.commit()

print(f"\nTotal enablements tracked: {total_enablements}")

# Show summary by year
print("\n" + "=" * 80)
print("ENABLEMENTS BY YEAR:")
cursor.execute("""
    SELECT 
        EXTRACT(YEAR FROM summary_date) as year,
        COUNT(*) as days_with_data,
        SUM(daily_count) as total_enablements
    FROM enablement_summary
    GROUP BY EXTRACT(YEAR FROM summary_date)
    ORDER BY year
""")
results = cursor.fetchall()
print(f"{'Year':6} | {'Days':6} | {'Enablements':12}")
print("-" * 30)
for row in results:
    print(f"{int(row[0]):6} | {row[1]:6} | {row[2]:12}")

# Show recent enablements with real status
print("\n" + "=" * 80)
print("RECENT ENABLEMENTS WITH REAL PREVIOUS STATUS:")
cursor.execute("""
    SELECT date, site_name, previous_status, current_status
    FROM daily_enablements
    ORDER BY date DESC
    LIMIT 10
""")
results = cursor.fetchall()
print(f"{'Date':12} | {'Site':15} | {'Previous Status':30} | {'Current Status':20}")
print("-" * 80)
for row in results:
    print(f"{row[0]} | {row[1]:15} | {row[2]:30} | {row[3]:20}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("Enablement tracking has been rebuilt with real previous status!")