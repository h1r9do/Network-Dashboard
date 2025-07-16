#!/usr/bin/env python3
import psycopg2

# Database connection
conn = psycopg2.connect(
    host='localhost',
    database='dsrcircuits',
    user='dsruser',
    password='dsrpass123'
)
cur = conn.cursor()

print("Examples of Non-DSR circuits:")
print("=" * 80)

# Get some examples of Non-DSR circuits
cur.execute("""
    SELECT site_name, site_id, provider_name, status, 
           details_service_speed, data_source, created_at,
           manual_override, notes
    FROM circuits
    WHERE data_source = 'Non-DSR'
    ORDER BY created_at DESC
    LIMIT 10
""")

results = cur.fetchall()
for row in results:
    print(f"\nSite: {row[0]} ({row[1]})")
    print(f"Provider: {row[2]}")
    print(f"Status: {row[3]}")
    print(f"Speed: {row[4]}")
    print(f"Data Source: {row[5]}")
    print(f"Created: {row[6]}")
    print(f"Manual Override: {row[7]}")
    if row[8]:
        print(f"Notes: {row[8][:100]}...")

print("\n\nExamples of manually added circuits (new_stores_manual):")
print("=" * 80)

cur.execute("""
    SELECT site_name, site_id, provider_name, status, 
           details_service_speed, data_source, created_at,
           manual_override, manual_override_by
    FROM circuits
    WHERE data_source = 'new_stores_manual'
    ORDER BY created_at DESC
""")

results = cur.fetchall()
for row in results:
    print(f"\nSite: {row[0]} ({row[1]})")
    print(f"Provider: {row[2]}")
    print(f"Status: {row[3]}")
    print(f"Speed: {row[4]}")
    print(f"Data Source: {row[5]}")
    print(f"Created: {row[6]}")
    print(f"Manual Override: {row[7]}")
    print(f"Override By: {row[8]}")

# Check how to identify all non-DSR circuits
print("\n\nSummary - All Non-DSR circuit sources:")
print("=" * 80)
cur.execute("""
    SELECT data_source, COUNT(*) as count
    FROM circuits
    WHERE data_source IN ('Non-DSR', 'new_stores_manual')
       OR data_source NOT LIKE '%csv%'
       OR data_source IS NULL
    GROUP BY data_source
    ORDER BY count DESC
""")

for source, count in cur.fetchall():
    print(f"{source}: {count} circuits")

cur.close()
conn.close()