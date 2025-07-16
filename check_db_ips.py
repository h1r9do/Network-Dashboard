#!/usr/bin/env python3
"""Check database for IP data"""

import psycopg2
from config import Config
import re

# Get database connection details from config
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
user, password, host, port, database = match.groups()

conn = psycopg2.connect(
    host=host,
    port=int(port),
    database=database,
    user=user,
    password=password
)

cursor = conn.cursor()

# Check NYB sites
cursor.execute("""
    SELECT network_name, device_serial, device_model, 
           wan1_ip, wan2_ip, wan1_arin_provider, wan2_arin_provider,
           last_updated
    FROM meraki_inventory
    WHERE network_name LIKE 'NYB%'
    AND device_model LIKE 'MX%'
    ORDER BY network_name
    LIMIT 10
""")

print("NYB Sites in meraki_inventory:")
print("-" * 100)
print(f"{'Network':<15} {'Serial':<20} {'Model':<10} {'WAN1 IP':<20} {'WAN2 IP':<20} {'Updated'}")
print("-" * 100)

for row in cursor.fetchall():
    network, serial, model, wan1_ip, wan2_ip, wan1_arin, wan2_arin, updated = row
    print(f"{network:<15} {serial:<20} {model:<10} {wan1_ip or 'NULL':<20} {wan2_ip or 'NULL':<20} {updated}")

# Count total records with IPs
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(wan1_ip) as with_wan1,
        COUNT(wan2_ip) as with_wan2
    FROM meraki_inventory
    WHERE device_model LIKE 'MX%'
""")

total, with_wan1, with_wan2 = cursor.fetchone()
print(f"\nTotal MX devices: {total}")
print(f"With WAN1 IP: {with_wan1}")
print(f"With WAN2 IP: {with_wan2}")

cursor.close()
conn.close()