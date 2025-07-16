#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from config import Config
import psycopg2
import re

match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
user, password, host, port, database = match.groups()

conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
cursor = conn.cursor()

print("Database vs CSV Comparison for Ready for Enablement Tracking")
print("=" * 80)

# 1. Check daily_enablements (these are circuits that went from Ready→Enabled)
print("\n1. DAILY_ENABLEMENTS TABLE (transitions from Ready→Enabled):")
print("-" * 60)
cursor.execute("""
    SELECT date, COUNT(*) as enablement_count
    FROM daily_enablements 
    WHERE date >= '2025-06-22'
    GROUP BY date
    ORDER BY date
""")
enablements = cursor.fetchall()
print(f"{'Date':12} | {'Enablements':12}")
print("-" * 25)
for row in enablements:
    print(f"{row[0]} | {row[1]:12}")

# 2. Check ready_queue_daily (ready count tracking)
print("\n\n2. READY_QUEUE_DAILY TABLE:")
print("-" * 60)
cursor.execute("""
    SELECT summary_date, ready_count
    FROM ready_queue_daily 
    WHERE summary_date >= '2025-06-22'
    ORDER BY summary_date
""")
ready_queue = cursor.fetchall()
print(f"{'Date':12} | {'Ready Count':12}")
print("-" * 25)
for row in ready_queue:
    print(f"{row[0]} | {row[1]:12}")

# 3. Check enablement_summary (daily enablement counts)
print("\n\n3. ENABLEMENT_SUMMARY TABLE:")
print("-" * 60)
cursor.execute("""
    SELECT summary_date, daily_count
    FROM enablement_summary 
    WHERE summary_date >= '2025-06-22'
    ORDER BY summary_date
""")
summary = cursor.fetchall()
print(f"{'Date':12} | {'Daily Count':12}")
print("-" * 25)
for row in summary:
    print(f"{row[0]} | {row[1]:12}")

# 4. Current circuits in ready status
print("\n\n4. CURRENT CIRCUITS IN READY FOR ENABLEMENT STATUS:")
print("-" * 60)
cursor.execute("""
    SELECT COUNT(*) 
    FROM circuits 
    WHERE LOWER(status) = 'ready for enablement'
""")
current_ready = cursor.fetchone()[0]
print(f"Total: {current_ready} circuits")

cursor.execute("""
    SELECT site_name, site_id, circuit_purpose
    FROM circuits 
    WHERE LOWER(status) = 'ready for enablement'
    ORDER BY site_name
""")
print("\nCircuits:")
for row in cursor.fetchall():
    print(f"  {row[0]:15} | {row[1]:15} | {row[2]}")

# 5. Compare with CSV counts
print("\n\n5. COMPARISON WITH CSV COUNTS:")
print("-" * 60)
csv_counts = {
    '2025-06-22': 5, '2025-06-23': 5, '2025-06-24': 6, '2025-06-25': 7,
    '2025-06-26': 8, '2025-06-27': 8, '2025-06-28': 8, '2025-06-29': 8,
    '2025-06-30': 8, '2025-07-01': 10, '2025-07-02': 11
}

# Create dict from ready_queue results
db_ready_dict = {str(row[0]): row[1] for row in ready_queue}

print(f"{'Date':12} | {'CSV Count':10} | {'DB Ready Queue':15} | {'Match?':8}")
print("-" * 50)
for date, csv_count in csv_counts.items():
    db_count = db_ready_dict.get(date, 'Missing')
    match = "YES" if str(csv_count) == str(db_count) else "NO"
    print(f"{date} | {csv_count:10} | {str(db_count):15} | {match:8}")

cursor.close()
conn.close()

print("\n" + "=" * 80)