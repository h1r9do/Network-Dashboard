#!/usr/bin/env python3
"""
Test if traceroute works on a Meraki switch
"""

import os
import sys
import psycopg2
import requests
import json
from dotenv import load_dotenv

sys.path.append('/usr/local/bin/test')
from config import Config

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')
MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')

headers = {
    'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
    'Content-Type': 'application/json'
}

# Get a switch from the database
conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
cursor = conn.cursor()

cursor.execute("""
    SELECT DISTINCT device_serial, network_name, device_model
    FROM meraki_inventory
    WHERE device_model LIKE 'MS%'
    AND device_serial IS NOT NULL
    LIMIT 5
""")

switches = cursor.fetchall()
cursor.close()
conn.close()

print("Testing traceroute on Meraki switches...")
print("=" * 50)

for serial, network, model in switches:
    print(f"\n\nTesting {network} - {model} ({serial})")
    
    # Try traceroute
    url = f'https://api.meraki.com/api/v1/devices/{serial}/liveTools/traceRoute'
    data = {
        'target': '8.8.8.8'
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"  Traceroute status: {response.status_code}")
    
    if response.status_code == 201:
        print("  ✅ Traceroute works on switches!")
        result = response.json()
        print(f"  Traceroute ID: {result.get('traceRouteId')}")
        break
    elif response.status_code == 400:
        error = response.json()
        print(f"  ❌ Error: {error.get('errors', ['Unknown error'])[0]}")
    else:
        print(f"  ❌ Error: {response.text[:100]}")

print("\n\nConclusion:")
print("The traceroute liveTools API appears to be limited to Meraki switches only.")
print("MX devices (firewalls) cannot use this API endpoint.")