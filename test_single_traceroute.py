#!/usr/bin/env python3
"""
Test single traceroute with proper rate limiting
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

print(f'Testing traceroute for {network_name}')
print(f'Device Serial: {device_serial}')
print(f'Source IP (WAN2): {wan2_ip}')
print('\nWaiting 10 seconds to respect rate limits...')
time.sleep(10)

# Step 1: Create traceroute
url = f'https://api.meraki.com/api/v1/devices/{device_serial}/liveTools/traceRoute'
data = {
    'target': '8.8.8.8',
    'sourceInterface': wan2_ip
}

print('\nStarting traceroute...')
response = requests.post(url, headers=headers, json=data)
print(f'Response status: {response.status_code}')

if response.status_code == 201:
    result = response.json()
    traceroute_id = result.get('traceRouteId')
    print(f'Traceroute ID: {traceroute_id}')
    
    # Wait before polling
    print('\nWaiting 10 seconds before polling for results...')
    time.sleep(10)
    
    # Step 2: Get results
    result_url = f'https://api.meraki.com/api/v1/devices/{device_serial}/liveTools/traceRoute/{traceroute_id}'
    
    max_attempts = 20
    for i in range(max_attempts):
        print(f'\nAttempt {i+1}/{max_attempts}...')
        response = requests.get(result_url, headers=headers)
        
        if response.status_code == 200:
            trace_result = response.json()
            status = trace_result.get('status')
            print(f'Status: {status}')
            
            if status == 'complete':
                print('\n✅ Traceroute complete!')
                print('\nFull result:')
                print(json.dumps(trace_result, indent=2))
                
                # Check for hops with DNS names
                if 'results' in trace_result:
                    print('\n🔍 Analyzing hops for carrier indicators:')
                    hops = trace_result.get('results', [])
                    for hop in hops[:5]:
                        hop_num = hop.get('hop')
                        ip = hop.get('ip')
                        if ip and ip != '*':
                            print(f'\nHop {hop_num}: {ip}')
                            # Try reverse DNS
                            try:
                                import socket
                                hostname = socket.gethostbyaddr(ip)[0]
                                print(f'  Hostname: {hostname}')
                                
                                # Check for carrier patterns
                                if any(pattern in hostname.lower() for pattern in ['myvzw', 'verizon', 'vzw']):
                                    print('  🎯 VERIZON DETECTED!')
                                elif any(pattern in hostname.lower() for pattern in ['att.net', 'sbcglobal']):
                                    print('  🎯 AT&T DETECTED!')
                                elif any(pattern in hostname.lower() for pattern in ['tmobile', 't-mobile']):
                                    print('  🎯 T-MOBILE DETECTED!')
                            except:
                                print('  No reverse DNS')
                break
            elif status == 'failed':
                print('❌ Traceroute failed')
                print(json.dumps(trace_result, indent=2))
                break
        else:
            print(f'Error getting results: {response.status_code}')
            if response.status_code == 429:
                print('Rate limited, waiting 10 seconds...')
                time.sleep(10)
        
        # Wait between polls
        time.sleep(5)
else:
    print(f'Failed to start traceroute: {response.text[:200]}')