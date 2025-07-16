#!/usr/bin/env python3
"""
Check ARIN data for FLT 02 and GAA 01
"""
import psycopg2
import re

# Read config
with open('/usr/local/bin/Main/config.py', 'r') as f:
    config_content = f.read()
    
uri_match = re.search(r"SQLALCHEMY_DATABASE_URI = ['\"]postgresql://([^:]+):([^@]+)@([^/]+)/([^'\"]+)['\"]", config_content)
if uri_match:
    user, password, host, database = uri_match.groups()

try:
    conn = psycopg2.connect(
        host=host.split(':')[0],
        port=5432,
        database=database,
        user=user,
        password=password
    )
    cursor = conn.cursor()
    
    # Check Meraki inventory for ARIN data
    cursor.execute("""
        SELECT network_name, device_name, 
               wan1_ip, wan1_arin_provider,
               wan2_ip, wan2_arin_provider,
               device_notes
        FROM meraki_inventory
        WHERE network_name IN ('FLT 02', 'GAA 01')
        ORDER BY network_name
    """)
    
    print("Meraki Inventory ARIN data:")
    for row in cursor.fetchall():
        print(f"\n{row[0]} - {row[1]}:")
        print(f"  WAN1: IP={row[2]}, ARIN={row[3]}")
        print(f"  WAN2: IP={row[4]}, ARIN={row[5]}")
        if row[6]:
            print(f"  Device Notes: {repr(row[6][:100])}")
    
    # Check enriched circuits
    cursor.execute("""
        SELECT network_name, 
               wan1_provider, wan1_speed, wan1_arin_org, wan1_confirmed,
               wan2_provider, wan2_speed, wan2_arin_org, wan2_confirmed
        FROM enriched_circuits
        WHERE network_name IN ('FLT 02', 'GAA 01')
        ORDER BY network_name
    """)
    
    print("\n" + "="*60)
    print("\nEnriched Circuits data:")
    for row in cursor.fetchall():
        print(f"\n{row[0]}:")
        print(f"  WAN1: Provider={row[1]}, Speed={row[2]}, ARIN={row[3]}, Confirmed={row[4]}")
        print(f"  WAN2: Provider={row[5]}, Speed={row[6]}, ARIN={row[7]}, Confirmed={row[8]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")