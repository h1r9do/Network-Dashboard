#!/usr/bin/env python3
import psycopg2
import re
import json
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

# Check meraki_inventory for sites with empty providers in enriched_circuits
print("=== Checking Meraki raw data for sites with empty providers ===\n")

# Get sites with empty providers
cursor.execute("""
    SELECT DISTINCT network_name 
    FROM enriched_circuits 
    WHERE wan1_provider = '' OR wan2_provider = ''
    ORDER BY network_name
    LIMIT 10
""")
sites = [row[0] for row in cursor.fetchall()]

for site in sites:
    print(f"\n{site}:")
    
    # Check meraki_inventory
    cursor.execute("""
        SELECT device_serial, wan1, wan2
        FROM meraki_inventory 
        WHERE network_name = %s
        LIMIT 1
    """, (site,))
    
    result = cursor.fetchone()
    if result:
        serial, wan1_data, wan2_data = result
        
        # Parse JSON data
        try:
            wan1 = json.loads(wan1_data) if wan1_data else {}
            wan2 = json.loads(wan2_data) if wan2_data else {}
        except:
            wan1 = {}
            wan2 = {}
        
        print(f"  Device: {serial}")
        print(f"  WAN1 from Meraki: Provider='{wan1.get('provider_label', '')}', Speed='{wan1.get('speed', '')}', IP='{wan1.get('ip', '')}'")
        print(f"  WAN2 from Meraki: Provider='{wan2.get('provider_label', '')}', Speed='{wan2.get('speed', '')}', IP='{wan2.get('ip', '')}'")
    
    # Check enriched_circuits
    cursor.execute("""
        SELECT wan1_provider, wan1_speed, wan2_provider, wan2_speed
        FROM enriched_circuits 
        WHERE network_name = %s
    """, (site,))
    
    result = cursor.fetchone()
    if result:
        print(f"  Current enriched: WAN1='{result[0]}' {result[1]}, WAN2='{result[2]}' {result[3]}")

# Check a specific example with data
print("\n\n=== Checking a site that should have data: COD 23 ===")
cursor.execute("""
    SELECT raw_notes 
    FROM meraki_inventory 
    WHERE network_name = 'COD 23'
""")
result = cursor.fetchone()
if result and result[0]:
    print(f"Raw notes from device:\n{result[0]}")

cursor.close()
conn.close()