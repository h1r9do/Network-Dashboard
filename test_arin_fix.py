#!/usr/bin/env python3
"""Test the fixed ARIN parsing"""

import sys
import requests
sys.path.insert(0, '/usr/local/bin/Main')

from nightly_meraki_db import parse_arin_response, get_db_connection

# Test IP
test_ip = "208.105.133.178"

# Get ARIN data
rdap_url = f"https://rdap.arin.net/registry/ip/{test_ip}"
response = requests.get(rdap_url)
rdap_data = response.json()

# Parse with fixed function
provider = parse_arin_response(rdap_data)
print(f"IP: {test_ip}")
print(f"Provider: {provider}")

# Update in database
conn = get_db_connection()
cursor = conn.cursor()

cursor.execute("""
    UPDATE meraki_inventory
    SET wan1_arin_provider = %s
    WHERE device_serial = 'Q2KY-4RP7-4FN8'
""", (provider,))

conn.commit()
cursor.close()
conn.close()

print("\nDatabase updated. Testing confirm modal...")

from confirm_meraki_notes_db_fixed import confirm_site
result = confirm_site('NYB 01')
print(f"WAN1 IP: {result.get('wan1_ip')}")
print(f"WAN1 Provider (ARIN): {result.get('wan1_provider')}")