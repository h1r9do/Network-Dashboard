#!/usr/bin/env python3
import psycopg2
import re
from config import Config

# Get database connection
def get_db_connection():
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

conn = get_db_connection()
cursor = conn.cursor()

# Check overall stats
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN wan1_provider != '' OR wan2_provider != '' THEN 1 END) as with_data,
        COUNT(CASE WHEN wan1_provider = '' AND wan2_provider = '' THEN 1 END) as empty,
        COUNT(CASE WHEN wan1_provider LIKE '%Cell%' OR wan1_provider LIKE '%Digi%' OR wan1_provider LIKE '%VZW%' 
                    OR wan2_provider LIKE '%Cell%' OR wan2_provider LIKE '%Digi%' OR wan2_provider LIKE '%VZW%' 
                    OR wan1_provider LIKE '%Starlink%' OR wan2_provider LIKE '%Starlink%' THEN 1 END) as cellular_satellite
    FROM enriched_circuits
""")

stats = cursor.fetchone()
print("Enriched circuits statistics:")
print(f"  Total sites: {stats[0]}")
print(f"  Sites with circuit data: {stats[1]}")
print(f"  Sites with no data: {stats[2]}")
print(f"  Cellular/Satellite circuits: {stats[3]}")

# Check specific providers that were lost
cursor.execute("""
    SELECT DISTINCT wan1_provider FROM enriched_circuits WHERE wan1_provider != ''
    UNION
    SELECT DISTINCT wan2_provider FROM enriched_circuits WHERE wan2_provider != ''
    ORDER BY 1
""")

providers = [row[0] for row in cursor.fetchall()]
print(f"\nUnique providers ({len(providers)} total):")
cellular_providers = [p for p in providers if 'Cell' in p or 'Digi' in p or 'VZW' in p or 'Starlink' in p or 'satellite' in p.lower()]
if cellular_providers:
    print(f"  Cellular/Satellite providers restored: {cellular_providers}")

# Check some specific sites that had lost data
print("\n=== Previously problematic sites ===")
for site in ['COD 23', 'TXS 24', 'COX 01', 'AZH 01', 'COD 16', 'NVN 03']:
    cursor.execute("""
        SELECT wan1_provider, wan1_speed, wan2_provider, wan2_speed
        FROM enriched_circuits
        WHERE network_name = %s
    """, (site,))
    result = cursor.fetchone()
    if result:
        print(f"{site}: WAN1='{result[0]}' {result[1]}, WAN2='{result[2]}' {result[3]}")

cursor.close()
conn.close()