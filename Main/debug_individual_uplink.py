#!/usr/bin/env python3
"""
Debug individual uplink API call for ALB 03
"""
import requests
import json
import os

API_KEY = os.getenv('MERAKI_API_KEY', '5174c907a7d57dea6a0788617287c985cc80b3c1')
device_serial = "Q2KY-FBAF-VTHH"

print("=== Debugging Individual Uplink API ===\n")

# Test individual uplink call
url = f"https://api.meraki.com/api/v1/devices/{device_serial}/appliance/uplink"
headers = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

print(f"URL: {url}")
print(f"Headers: {headers}")

try:
    response = requests.get(url, headers=headers, timeout=30)
    print(f"\nResponse Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\nFull Response:")
        print(json.dumps(data, indent=2))
        
        print("\n=== Analyzing Response ===")
        for uplink in data:
            interface = uplink.get('interface')
            print(f"\nInterface: {interface}")
            print(f"  status: {uplink.get('status')}")
            print(f"  ip: {uplink.get('ip')}")
            print(f"  publicIp: {uplink.get('publicIp')}")
            print(f"  gateway: {uplink.get('gateway')}")
            print(f"  dns: {uplink.get('dns')}")
            
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"Exception: {e}")