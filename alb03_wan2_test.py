#!/usr/bin/env python3
"""
Test ping from ALB 03 using WAN2 interface variants
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
wan2_ip = '192.168.0.151'

print("ALB 03 WAN2 Interface Test")
print("=" * 50)

# Try different sourceInterface formats
source_variants = [
    wan2_ip,              # IP address
    'wan2',               # Interface name lowercase
    'WAN2',               # Interface name uppercase
    'wan 2',              # With space
    'WAN 2',              # With space uppercase
    'internet2',          # Alternative name
    'Internet2',          # Alternative name capitalized
    '2',                  # Just the number
    'uplink2',            # Uplink variant
    'Uplink2'             # Uplink capitalized
]

successful_variant = None

for variant in source_variants:
    print(f"\n\nTrying sourceInterface: '{variant}'")
    
    # Try ping with sourceInterface
    url = f'https://api.meraki.com/api/v1/devices/{device_serial}/liveTools/ping'
    data = {
        'target': '8.8.8.8',
        'count': 3,
        'sourceInterface': variant
    }
    
    print(f"Request: {json.dumps(data)}")
    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        print("✅ Success! This variant works!")
        successful_variant = variant
        
        result = response.json()
        ping_id = result.get('pingId')
        
        # Wait and get results
        time.sleep(5)
        result_url = f'https://api.meraki.com/api/v1/devices/{device_serial}/liveTools/ping/{ping_id}'
        
        for i in range(10):
            response = requests.get(result_url, headers=headers)
            if response.status_code == 200:
                ping_result = response.json()
                status = ping_result.get('status')
                
                if status == 'complete':
                    print("\nPing complete!")
                    print(json.dumps(ping_result, indent=2))
                    break
                else:
                    print(f"  Status: {status}")
            time.sleep(2)
        
        break
    else:
        print(f"❌ Error: {response.text[:100]}")

if not successful_variant:
    print("\n\nNo sourceInterface variant worked for ping. Trying traceroute variants...")
    
    for variant in source_variants:
        print(f"\n\nTrying traceroute with sourceInterface: '{variant}'")
        
        url = f'https://api.meraki.com/api/v1/devices/{device_serial}/liveTools/traceRoute'
        data = {
            'target': '8.8.8.8',
            'sourceInterface': variant
        }
        
        response = requests.post(url, headers=headers, json=data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            print("✅ Success! Traceroute accepted this variant!")
            break
        else:
            print(f"❌ Error: {response.text[:100]}")