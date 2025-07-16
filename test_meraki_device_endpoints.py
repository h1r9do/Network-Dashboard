#!/usr/bin/env python3
"""
Test various Meraki API endpoints to find what's available
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')
MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')

headers = {
    'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
    'Content-Type': 'application/json'
}

# Test device
device_serial = 'Q2KY-FBAF-VTHH'
network_id = 'L_691690537529335234'  # You'll need to get this from the database

endpoints = [
    f"/devices/{device_serial}",
    f"/devices/{device_serial}/uplinks/statuses",
    f"/devices/{device_serial}/appliance/uplinks/statuses",
    f"/devices/{device_serial}/managementInterface",
    f"/devices/{device_serial}/liveTools/ping",
    f"/devices/{device_serial}/liveTools/traceroute",
    f"/devices/{device_serial}/liveTools",
    f"/networks/{network_id}/devices/{device_serial}/uplinks",
    f"/organizations/691690537529306089/devices/statuses",
]

print("Testing Meraki API endpoints for ALB 03...")
print("=" * 60)

for endpoint in endpoints:
    url = f"https://api.meraki.com/api/v1{endpoint}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"\n{endpoint}")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response type: {type(data)}")
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:5]}")  # First 5 keys
            elif isinstance(data, list):
                print(f"  Length: {len(data)}")
        else:
            print(f"  Error: {response.text[:100]}")
    except Exception as e:
        print(f"  Exception: {str(e)}")

print("\n" + "=" * 60)