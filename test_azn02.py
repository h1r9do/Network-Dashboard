#!/usr/bin/env python3
"""Test AZN 02 specifically"""

import sys
sys.path.insert(0, '/usr/local/bin/Main')

from confirm_meraki_notes_db_fixed import confirm_site
import json

# Test AZN 02
result = confirm_site('AZN 02')

print("AZN 02 Test Results:")
print("=" * 50)
print(f"WAN1 IP: {result.get('wan1_ip', 'N/A')}")
print(f"WAN1 Provider (ARIN): {result.get('wan1_provider', 'N/A')}")
print(f"WAN2 IP: {result.get('wan2_ip', 'N/A')}")
print(f"WAN2 Provider (ARIN): {result.get('wan2_provider', 'N/A')}")
print()
print(f"WAN1 Provider (Enriched): {result.get('wan1', {}).get('provider', 'N/A')}")
print(f"WAN2 Provider (Enriched): {result.get('wan2', {}).get('provider', 'N/A')}")

# Check the database directly
from config import Config
import psycopg2
import re

# Get database connection
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

# Check meraki_inventory
cursor.execute("""
    SELECT wan1_ip, wan1_arin_provider, wan2_ip, wan2_arin_provider, last_updated
    FROM meraki_inventory
    WHERE network_name = 'AZN 02'
    AND device_model LIKE 'MX%'
""")

meraki_result = cursor.fetchone()
if meraki_result:
    print("\nDatabase (meraki_inventory):")
    print(f"WAN1 IP: {meraki_result[0]}")
    print(f"WAN1 ARIN Provider: {meraki_result[1]}")
    print(f"WAN2 IP: {meraki_result[2]}")
    print(f"WAN2 ARIN Provider: {meraki_result[3]}")
    print(f"Last Updated: {meraki_result[4]}")
    
    # Test ARIN lookup for the IPs
    if meraki_result[0] and meraki_result[1] == 'Unknown':
        print(f"\nWAN1 IP {meraki_result[0]} has 'Unknown' provider - checking why...")
        import requests
        try:
            response = requests.get(f"https://rdap.arin.net/registry/ip/{meraki_result[0]}")
            if response.status_code == 200:
                data = response.json()
                print(f"ARIN response has data: {bool(data)}")
                if 'network' in data:
                    print(f"Network name: {data.get('network', {}).get('name')}")
            else:
                print(f"ARIN query failed: {response.status_code}")
        except Exception as e:
            print(f"Error querying ARIN: {e}")

cursor.close()
conn.close()