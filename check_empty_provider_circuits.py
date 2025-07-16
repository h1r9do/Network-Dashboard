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

# Check if these networks have circuits in the main circuits table
cursor.execute("""
    SELECT DISTINCT ec.network_name, 
           ec.wan1_provider, ec.wan2_provider,
           COUNT(c.id) as circuit_count
    FROM enriched_circuits ec
    LEFT JOIN circuits c ON c.site_name = ec.network_name
    WHERE ec.wan1_provider = '' OR ec.wan2_provider = ''
    GROUP BY ec.network_name, ec.wan1_provider, ec.wan2_provider
    ORDER BY ec.network_name
    LIMIT 20
""")
results = cursor.fetchall()

print("Networks with empty providers and their circuit count:")
for row in results:
    print(f"  {row[0]}: WAN1='{row[1]}', WAN2='{row[2]}', Circuits in DSR: {row[3]}")

# Check specific examples from meraki_inventory
cursor.execute("""
    SELECT network_name, wan1_ip, wan2_ip, device_serial
    FROM meraki_inventory 
    WHERE network_name IN ('AZH 01', 'COX 01', 'COD 23', 'TXS 24')
""")
meraki_results = cursor.fetchall()

print("\nMeraki inventory for sample networks:")
for row in meraki_results:
    print(f"  {row[0]}: WAN1_IP={row[1]}, WAN2_IP={row[2]}, Serial={row[3]}")

# Check if these are single-circuit sites
cursor.execute("""
    SELECT ec.network_name, 
           CASE WHEN ec.wan1_provider != '' THEN 1 ELSE 0 END +
           CASE WHEN ec.wan2_provider != '' THEN 1 ELSE 0 END as circuit_count
    FROM enriched_circuits ec
    WHERE ec.wan1_provider = '' OR ec.wan2_provider = ''
    ORDER BY circuit_count DESC
    LIMIT 20
""")
single_circuit = cursor.fetchall()

print("\nSites with empty providers by circuit count:")
for row in single_circuit:
    print(f"  {row[0]}: {row[1]} circuit(s) configured")

cursor.close()
conn.close()