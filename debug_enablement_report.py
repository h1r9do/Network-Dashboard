#!/usr/bin/env python3
"""Debug and fix enablement report data"""

import sys
sys.path.insert(0, '.')
from config import Config
import psycopg2
import re
from datetime import datetime, timedelta

# Connect to database
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
user, password, host, port, database = match.groups()

conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
cursor = conn.cursor()

print("Enablement Report Data Debug")
print("=" * 80)

# 1. Check enablement_summary table
print("\n1. ENABLEMENT_SUMMARY TABLE (Daily enablement counts):")
print("-" * 60)
cursor.execute("""
    SELECT summary_date, daily_count 
    FROM enablement_summary 
    WHERE summary_date >= '2025-06-28'
    ORDER BY summary_date
""")
results = cursor.fetchall()
print(f"{'Date':12} | {'Enablements':12}")
print("-" * 30)
for row in results:
    print(f"{row[0]} | {row[1]:12}")

# 2. Check ready_queue_daily table
print("\n\n2. READY_QUEUE_DAILY TABLE (Ready for Enablement counts):")
print("-" * 60)
cursor.execute("""
    SELECT summary_date, ready_count 
    FROM ready_queue_daily 
    WHERE summary_date >= '2025-06-28'
    ORDER BY summary_date
""")
results = cursor.fetchall()
print(f"{'Date':12} | {'Ready Count':12}")
print("-" * 30)
for row in results:
    print(f"{row[0]} | {row[1]:12}")

# 3. Check daily_enablements table (individual records)
print("\n\n3. DAILY_ENABLEMENTS TABLE (Individual enablement records):")
print("-" * 60)
cursor.execute("""
    SELECT date, COUNT(*) as count
    FROM daily_enablements 
    WHERE date >= '2025-06-28'
    GROUP BY date
    ORDER BY date
""")
results = cursor.fetchall()
print(f"{'Date':12} | {'Records':12}")
print("-" * 30)
for row in results:
    print(f"{row[0]} | {row[1]:12}")

# 4. Sample recent enablements
print("\n\n4. SAMPLE RECENT ENABLEMENTS:")
print("-" * 60)
cursor.execute("""
    SELECT date, site_name, circuit_purpose, previous_status, current_status, assigned_to
    FROM daily_enablements 
    WHERE date >= '2025-06-25'
    ORDER BY date DESC
    LIMIT 10
""")
results = cursor.fetchall()
print(f"{'Date':12} | {'Site':15} | {'Purpose':10} | {'Prev Status':20} | {'Curr Status':20} | {'Assigned':15}")
print("-" * 100)
for row in results:
    print(f"{row[0]} | {row[1]:15} | {row[2]:10} | {row[3]:20} | {row[4]:20} | {row[5] or 'Unknown':15}")

# 5. Check if there's data missing for July 1-2
print("\n\n5. CHECKING FOR JULY 1-2 DATA:")
print("-" * 60)

# Check if we have any data for July
cursor.execute("""
    SELECT COUNT(*) FROM enablement_summary WHERE summary_date >= '2025-07-01'
""")
july_summary_count = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) FROM ready_queue_daily WHERE summary_date >= '2025-07-01'
""")
july_ready_count = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) FROM daily_enablements WHERE date >= '2025-07-01'
""")
july_enablement_count = cursor.fetchone()[0]

print(f"July data in enablement_summary: {july_summary_count} records")
print(f"July data in ready_queue_daily: {july_ready_count} records")
print(f"July data in daily_enablements: {july_enablement_count} records")

# 6. Test the API endpoints
print("\n\n6. TESTING API ENDPOINTS:")
print("-" * 60)

# Simulate the daily-enablement-data query
cursor.execute("""
    SELECT summary_date, daily_count 
    FROM enablement_summary 
    ORDER BY summary_date DESC
    LIMIT 5
""")
results = cursor.fetchall()
print("Latest enablement_summary records:")
for row in results:
    print(f"  {row[0]}: {row[1]} enablements")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("SUMMARY:")
print("The enablement report queries these tables:")
print("1. enablement_summary - for daily enablement counts")
print("2. ready_queue_daily - for ready queue size") 
print("3. daily_enablements - for individual circuit details")
print("\nIf July data is missing from these tables, the nightly script needs to be run.")