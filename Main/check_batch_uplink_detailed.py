#!/usr/bin/env python3
"""
Check the batch uplink endpoint for detailed data including publicIp
"""
import requests
import json
import os

API_KEY = os.getenv('MERAKI_API_KEY', '5174c907a7d57dea6a0788617287c985cc80b3c1')
ORG_ID = '436883'
device_serial = "Q2KY-FBAF-VTHH"

print("=== Detailed Batch Uplink Analysis ===\n")

url = f"https://api.meraki.com/api/v1/organizations/{ORG_ID}/appliance/uplink/statuses"
headers = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

try:
    response = requests.get(url, headers=headers, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        
        # Find ALB 03 device
        device_data = None
        for device in data:
            if device.get('serial') == device_serial:
                device_data = device
                break
        
        if device_data:
            print(f"Found device: {device_serial}")
            print("\nFull device data:")
            print(json.dumps(device_data, indent=2))
            
            print("\n=== Analyzing Uplinks ===")
            uplinks = device_data.get('uplinks', [])
            for i, uplink in enumerate(uplinks):
                print(f"\nUplink {i+1}:")
                print(f"  interface: {uplink.get('interface')}")
                print(f"  status: {uplink.get('status')}")
                print(f"  ip: {uplink.get('ip')}")
                print(f"  gateway: {uplink.get('gateway')}")
                print(f"  dns: {uplink.get('dns')}")
                
                # Check all keys in uplink
                print("  All keys:", list(uplink.keys()))
                
        else:
            print(f"Device {device_serial} not found")
            
    else:
        print(f"API Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")