#!/usr/bin/env python3
"""Fix missing enablement data for July 1-2"""

import sys
sys.path.insert(0, '.')
from config import Config
import psycopg2
import re
from datetime import datetime

# Connect to database
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
user, password, host, port, database = match.groups()

conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
cursor = conn.cursor()

print("Fixing missing enablement data...")
print("=" * 80)

# Add missing enablement_summary records for July 1-2
# Based on the CSV analysis, there were no enablements on these days
missing_dates = [
    ('2025-07-01', 0),
    ('2025-07-02', 0)
]

print("\n1. Adding missing enablement_summary records:")
for date, count in missing_dates:
    cursor.execute("""
        INSERT INTO enablement_summary (summary_date, daily_count, created_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (summary_date) DO UPDATE SET
            daily_count = EXCLUDED.daily_count,
            created_at = NOW()
    """, (date, count))
    print(f"   Added {date}: {count} enablements")

# For demonstration, let's also check if there were any actual enablements we missed
# by checking recent circuit status changes in the circuits table
print("\n2. Checking for any missed enablements in circuits table:")
cursor.execute("""
    SELECT site_name, site_id, status, updated_at::date
    FROM circuits
    WHERE status ILIKE '%enabled%' 
    AND status NOT ILIKE '%ready%'
    AND updated_at >= '2025-06-28'
    ORDER BY updated_at DESC
    LIMIT 10
""")
results = cursor.fetchall()
if results:
    print("   Recent enabled circuits:")
    for row in results:
        print(f"   {row[3]}: {row[0]} ({row[1]}) - {row[2]}")
else:
    print("   No recent enablements found")

# Commit the changes
conn.commit()

# Verify the fix
print("\n3. Verifying the fix:")
cursor.execute("""
    SELECT summary_date, daily_count 
    FROM enablement_summary 
    WHERE summary_date >= '2025-06-28'
    ORDER BY summary_date
""")
results = cursor.fetchall()
print(f"\n{'Date':12} | {'Enablements':12}")
print("-" * 30)
for row in results:
    print(f"{row[0]} | {row[1]:12}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("Fix complete! The enablement report should now show data through July 2.")