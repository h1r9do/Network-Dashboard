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

# Get enabled statuses
enabled_statuses = ['Enabled', 'Service Activated', 'Enabled Using Existing Broadband', 
                   'Enabled/Disconnected', 'Enabled/Disconnect Pending']

# Check how many sites have NO enabled circuits
cursor.execute("""
    WITH enabled_sites AS (
        SELECT DISTINCT site_name
        FROM circuits
        WHERE status = ANY(%s)
    )
    SELECT 
        ec.network_name,
        ec.wan1_provider,
        ec.wan2_provider,
        CASE WHEN es.site_name IS NULL THEN 'No enabled circuits' ELSE 'Has enabled circuits' END as status
    FROM enriched_circuits ec
    LEFT JOIN enabled_sites es ON ec.network_name = es.site_name
    WHERE ec.wan1_provider = '' OR ec.wan2_provider = ''
    ORDER BY status, ec.network_name
    LIMIT 20
""", (enabled_statuses,))

results = cursor.fetchall()

print("Sites with empty providers and their enabled status:")
for row in results:
    print(f"{row[0]}: WAN1='{row[1]}', WAN2='{row[2]}' - {row[3]}")

# Count total
cursor.execute("""
    WITH enabled_sites AS (
        SELECT DISTINCT site_name
        FROM circuits
        WHERE status = ANY(%s)
    )
    SELECT 
        COUNT(CASE WHEN es.site_name IS NULL THEN 1 END) as no_enabled,
        COUNT(CASE WHEN es.site_name IS NOT NULL THEN 1 END) as has_enabled
    FROM enriched_circuits ec
    LEFT JOIN enabled_sites es ON ec.network_name = es.site_name
""", (enabled_statuses,))

counts = cursor.fetchone()
print(f"\nTotal enriched circuits: {counts[0] + counts[1]}")
print(f"  - With NO enabled circuits: {counts[0]}")
print(f"  - With enabled circuits: {counts[1]}")

# Check specific examples
print("\n=== Checking specific problematic sites ===")
for site in ['COD 23', 'TXS 24', 'COX 01']:
    cursor.execute("""
        SELECT circuit_purpose, provider_name, status, ip_address_start
        FROM circuits 
        WHERE site_name = %s
        ORDER BY circuit_purpose, status
    """, (site,))
    
    print(f"\n{site}:")
    for row in cursor.fetchall():
        print(f"  {row[0] or 'Unknown'}: {row[1]} - {row[2]} - IP: {row[3]}")

cursor.close()
conn.close()