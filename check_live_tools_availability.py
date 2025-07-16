#!/usr/bin/env python3
"""
Check what live tools are available for ALB 03
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

device_serial = 'Q2KY-FBAF-VTHH'

# Check device details first
device_url = f'https://api.meraki.com/api/v1/devices/{device_serial}'
response = requests.get(device_url, headers=headers)

if response.status_code == 200:
    device = response.json()
    print("Device Details:")
    print(f"  Name: {device.get('name', 'N/A')}")
    print(f"  Model: {device.get('model', 'N/A')}")
    print(f"  Firmware: {device.get('firmware', 'N/A')}")
    print(f"  Serial: {device.get('serial')}")
    
    # Check if it's an MX device
    if device.get('model', '').startswith('MX'):
        print("\n✅ This is an MX device")
    else:
        print("\n❌ This is NOT an MX device")

# Test different API endpoints
print("\n\nTesting API endpoints:")
print("-" * 50)

endpoints_to_test = [
    f"/devices/{device_serial}/liveTools",
    f"/devices/{device_serial}/liveTools/ping", 
    f"/devices/{device_serial}/liveTools/traceRoute",
    f"/devices/{device_serial}/appliance/uplinks/statuses",
    f"/devices/{device_serial}/clients",
    f"/devices/{device_serial}/managementInterface"
]

for endpoint in endpoints_to_test:
    url = f"https://api.meraki.com/api/v1{endpoint}"
    response = requests.get(url, headers=headers)
    print(f"\n{endpoint}")
    print(f"  Status: {response.status_code}")
    
    if response.status_code == 200:
        print("  ✅ Available")
    elif response.status_code == 404:
        print("  ❌ Not Found")
    elif response.status_code == 429:
        print("  ⚠️  Rate Limited")
    else:
        print(f"  ⚠️  {response.reason}")