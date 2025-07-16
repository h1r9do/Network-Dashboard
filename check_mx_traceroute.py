#!/usr/bin/env python3
"""
Check different traceroute approaches for MX device
"""

import os
import requests
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')
MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')

headers = {
    'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
    'Content-Type': 'application/json'
}

# ALB 03 details
device_serial = 'Q2KY-FBAF-VTHH'
network_name = 'ALB 03'
wan2_ip = '192.168.0.151'

print("Testing MX traceroute options...")
print("=" * 50)

# Get network ID first
device_url = f'https://api.meraki.com/api/v1/devices/{device_serial}'
response = requests.get(device_url, headers=headers)
if response.status_code == 200:
    device_info = response.json()
    network_id = device_info.get('networkId')
    print(f"Network ID: {network_id}")
    print(f"Device Model: {device_info.get('model')}")
else:
    print("Failed to get device info")
    exit()

# Try different endpoints
endpoints_to_try = [
    # MX-specific endpoints
    (f"/devices/{device_serial}/appliance/connectivityMonitoringDestinations", "GET", None),
    (f"/networks/{network_id}/appliance/connectivityMonitoringDestinations", "GET", None),
    (f"/devices/{device_serial}/appliance/uplinks/statuses", "GET", None),
    
    # Try ping instead of traceroute
    (f"/devices/{device_serial}/liveTools/ping", "POST", {
        'target': '8.8.8.8',
        'count': 3
    }),
    
    # Try without sourceInterface
    (f"/devices/{device_serial}/liveTools/traceRoute", "POST", {
        'target': '8.8.8.8'
    }),
]

for endpoint, method, data in endpoints_to_try:
    print(f"\n\nTrying: {method} {endpoint}")
    url = f"https://api.meraki.com/api/v1{endpoint}"
    
    if method == "GET":
        response = requests.get(url, headers=headers)
    else:
        response = requests.post(url, headers=headers, json=data)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200 or response.status_code == 201:
        print("✅ Success!")
        result = response.json()
        print(json.dumps(result, indent=2)[:500] + "..." if len(json.dumps(result)) > 500 else json.dumps(result, indent=2))
    else:
        print(f"❌ Error: {response.text[:200]}")