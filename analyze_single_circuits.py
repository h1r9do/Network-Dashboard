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

# Count single vs dual circuit sites
cursor.execute("""
    SELECT 
        CASE 
            WHEN wan1_provider != '' AND wan2_provider != '' THEN 'Dual Circuit'
            WHEN wan1_provider != '' AND wan2_provider = '' THEN 'Single Circuit (WAN1 only)'
            WHEN wan1_provider = '' AND wan2_provider != '' THEN 'Single Circuit (WAN2 only)'
            ELSE 'No circuits'
        END as circuit_type,
        COUNT(*) as count
    FROM enriched_circuits
    GROUP BY circuit_type
    ORDER BY count DESC
""")
results = cursor.fetchall()

print("Circuit configuration breakdown:")
for row in results:
    print(f"  {row[0]}: {row[1]} sites")

# Check if DSR tracking data shows these as single circuit sites
cursor.execute("""
    SELECT c.site_name, c.circuit_purpose, c.provider_name, c.status
    FROM circuits c
    WHERE c.site_name IN (
        SELECT network_name FROM enriched_circuits 
        WHERE wan2_provider = '' 
        LIMIT 10
    )
    ORDER BY c.site_name, c.circuit_purpose
""")
dsr_circuits = cursor.fetchall()

print("\nDSR tracking data for sites with empty WAN2:")
current_site = None
for row in dsr_circuits:
    if row[0] != current_site:
        current_site = row[0]
        print(f"\n{row[0]}:")
    print(f"  - {row[1] or 'No purpose'}: {row[2]} ({row[3]})")

# Check specific examples with empty WAN1
cursor.execute("""
    SELECT network_name, wan1_provider, wan2_provider
    FROM enriched_circuits
    WHERE wan1_provider = ''
    LIMIT 10
""")
empty_wan1 = cursor.fetchall()

print("\nSites with empty WAN1 (unusual):")
for row in empty_wan1:
    print(f"  {row[0]}: WAN1='{row[1]}', WAN2='{row[2]}'")

cursor.close()
conn.close()