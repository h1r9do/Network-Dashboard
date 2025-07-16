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
        COUNT(CASE WHEN wan1_provider = '' AND wan2_provider = '' THEN 1 END) as empty
    FROM enriched_circuits
""")

stats = cursor.fetchone()
print("=== Enriched circuits statistics ===")
print(f"  Total sites: {stats[0]}")
print(f"  Sites with circuit data: {stats[1]}") 
print(f"  Sites with no data: {stats[2]}")

# Check that we only have Meraki MX sites
cursor.execute("""
    SELECT COUNT(*)
    FROM enriched_circuits ec
    WHERE NOT EXISTS (
        SELECT 1 FROM meraki_inventory mi 
        WHERE mi.network_name = ec.network_name 
        AND mi.device_model LIKE 'MX%'
    )
""")
non_mx = cursor.fetchone()[0]
print(f"\nNon-MX sites in enriched_circuits: {non_mx}")

# Check excluded sites are not present
cursor.execute("""
    SELECT COUNT(*)
    FROM enriched_circuits
    WHERE network_name ILIKE '%hub%'
       OR network_name ILIKE '%voice%' 
       OR network_name ILIKE '%lab%'
       OR 'hub' = ANY(device_tags)
       OR 'voice' = ANY(device_tags)
       OR 'lab' = ANY(device_tags)
""")
excluded = cursor.fetchone()[0]
print(f"Hub/Voice/Lab sites in enriched_circuits: {excluded}")

# Check cellular/satellite preservation
cursor.execute("""
    SELECT COUNT(*)
    FROM enriched_circuits
    WHERE wan1_provider LIKE '%Cell%' OR wan1_provider LIKE '%Digi%' 
       OR wan1_provider LIKE '%VZW%' OR wan1_provider LIKE '%Starlink%'
       OR wan2_provider LIKE '%Cell%' OR wan2_provider LIKE '%Digi%' 
       OR wan2_provider LIKE '%VZW%' OR wan2_provider LIKE '%Starlink%'
""")
cellular = cursor.fetchone()[0]
print(f"Cellular/Satellite circuits preserved: {cellular}")

# Check a few specific sites to ensure data is good
print("\n=== Sample site verification ===")
sample_sites = ['COD 23', 'TXS 24', 'AZH 01', 'NVN 03', 'COD 16']
for site in sample_sites:
    cursor.execute("""
        SELECT wan1_provider, wan1_speed, wan2_provider, wan2_speed,
               ARRAY_LENGTH(device_tags, 1) as tag_count
        FROM enriched_circuits
        WHERE network_name = %s
    """, (site,))
    result = cursor.fetchone()
    if result:
        tags = f", {result[4]} tags" if result[4] else ""
        print(f"{site}: WAN1='{result[0]}' {result[1]}, WAN2='{result[2]}' {result[3]}{tags}")

cursor.close()
conn.close()