#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from config import Config
import psycopg2
from datetime import datetime, timedelta
import pandas as pd

# Parse database connection
import re
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
user, password, host, port, database = match.groups()

conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
cursor = conn.cursor()

print("Database Enablement Tracking Comparison")
print("=" * 80)

# 1. Check daily_enablements table
print("\n1. DAILY_ENABLEMENTS TABLE (Ready→Enabled transitions only):")
print("-" * 60)
cursor.execute("""
    SELECT date_tracked, ready_count, enablement_count 
    FROM daily_enablements 
    WHERE date_tracked >= '2025-06-22'
    ORDER BY date_tracked
""")
db_results = cursor.fetchall()

print(f"{'Date':12} | {'Ready Count':12} | {'Enablements':12}")
print("-" * 40)
for row in db_results:
    print(f"{row[0]} | {row[1]:12} | {row[2]:12}")

# 2. Check ready_queue_daily table
print("\n\n2. READY_QUEUE_DAILY TABLE (Site-based tracking):")
print("-" * 60)
cursor.execute("""
    SELECT date_tracked, COUNT(*) as sites_ready
    FROM ready_queue_daily 
    WHERE date_tracked >= '2025-06-22'
    GROUP BY date_tracked
    ORDER BY date_tracked
""")
queue_results = cursor.fetchall()

print(f"{'Date':12} | {'Sites Ready':12}")
print("-" * 25)
for row in queue_results:
    print(f"{row[0]} | {row[1]:12}")

# 3. Check circuits table for current ready status
print("\n\n3. CURRENT CIRCUITS TABLE STATUS:")
print("-" * 60)
cursor.execute("""
    SELECT COUNT(*) as ready_count
    FROM circuits 
    WHERE LOWER(status) = 'ready for enablement'
""")
current_ready = cursor.fetchone()[0]
print(f"Current Ready for Enablement in circuits table: {current_ready}")

# 4. List current ready circuits
cursor.execute("""
    SELECT site_name, site_id, circuit_purpose, assigned_to
    FROM circuits 
    WHERE LOWER(status) = 'ready for enablement'
    ORDER BY site_name
""")
print("\nCurrent Ready Circuits:")
for row in cursor.fetchall():
    print(f"  {row[0]:15} | {row[1]:15} | {row[2]:10} | {row[3] or 'N/A'}")

# 5. Compare with CSV counts
print("\n\n4. CSV FILE COUNTS (for comparison):")
print("-" * 60)
print(f"{'Date':12} | {'CSV Count':12} | {'DB Ready':12} | {'Match?':8}")
print("-" * 45)

csv_counts = {
    '2025-06-22': 5,
    '2025-06-23': 5,
    '2025-06-24': 6,
    '2025-06-25': 7,
    '2025-06-26': 8,
    '2025-06-27': 8,
    '2025-06-28': 8,
    '2025-06-29': 8,
    '2025-06-30': 8,
    '2025-07-01': 10,
    '2025-07-02': 11
}

# Create a dict of database ready counts
db_ready_dict = {str(row[0]): row[1] for row in db_results}

for date, csv_count in csv_counts.items():
    db_count = db_ready_dict.get(date, 0)
    match = "YES" if csv_count == db_count else "NO"
    print(f"{date} | {csv_count:12} | {db_count:12} | {match:8}")

cursor.close()
conn.close()

print("\n" + "=" * 80)