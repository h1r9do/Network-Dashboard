#!/usr/bin/env python3
"""
Test ping from ALB 03 to see what information we can get
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

print("ALB 03 Ping Test")
print("=" * 50)

# Create ping request
url = f'https://api.meraki.com/api/v1/devices/{device_serial}/liveTools/ping'
data = {
    'target': '8.8.8.8',
    'count': 5
}

print("\nCreating ping request...")
response = requests.post(url, headers=headers, json=data)

if response.status_code == 201:
    result = response.json()
    ping_id = result.get('pingId')
    print(f"✅ Ping created! ID: {ping_id}")
    
    # Poll for results
    result_url = f'https://api.meraki.com/api/v1/devices/{device_serial}/liveTools/ping/{ping_id}'
    
    print("\nPolling for results...")
    time.sleep(5)
    
    for i in range(10):
        response = requests.get(result_url, headers=headers)
        
        if response.status_code == 200:
            ping_result = response.json()
            status = ping_result.get('status')
            
            if status == 'complete':
                print("\n✅ PING COMPLETE!\n")
                print("Full result:")
                print(json.dumps(ping_result, indent=2))
                
                # Check if there's any source information
                if 'results' in ping_result:
                    results = ping_result.get('results', {})
                    replies = results.get('replies', [])
                    loss = results.get('loss', {})
                    latencies = results.get('latencies', {})
                    
                    print(f"\nPing statistics:")
                    print(f"  Sent: {results.get('sent', 0)}")
                    print(f"  Received: {results.get('received', 0)}")
                    print(f"  Loss: {loss.get('percentage', 0)}%")
                    if latencies:
                        print(f"  Average latency: {latencies.get('average', 0)}ms")
                
                break
            else:
                print(f"  Status: {status}")
        
        time.sleep(3)
else:
    print(f"❌ Error: {response.text}")

# Also check what other information we can get about the device
print("\n\nChecking device connectivity information...")

# Try to get uplink information differently
get_device_url = f'https://api.meraki.com/api/v1/devices/{device_serial}'
response = requests.get(get_device_url, headers=headers)

if response.status_code == 200:
    device_info = response.json()
    print("\nDevice info that might help:")
    if 'wan1Ip' in device_info:
        print(f"  WAN1 IP: {device_info.get('wan1Ip')}")
    if 'wan2Ip' in device_info:
        print(f"  WAN2 IP: {device_info.get('wan2Ip')}")
    if 'publicIp' in device_info:
        print(f"  Public IP: {device_info.get('publicIp')}")