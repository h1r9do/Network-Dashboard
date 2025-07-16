#!/usr/bin/env python3
"""
Test traceroute for ALB 03 with private IP
"""

import os
import requests
import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')
MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')

headers = {
    'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
    'Content-Type': 'application/json'
}

# ALB 03 details from our database
device_serial = 'Q2KY-FBAF-VTHH'
network_name = 'ALB 03'
wan2_ip = '192.168.0.151'  # Private IP from our database

print(f'Running traceroute for {network_name}')
print(f'Device Serial: {device_serial}')
print(f'Source IP (WAN2): {wan2_ip}')

# Step 1: Initiate traceroute from private IP
traceroute_url = f'https://api.meraki.com/api/v1/devices/{device_serial}/liveTools/traceroute'
traceroute_data = {
    'target': '8.8.8.8',
    'sourceInterface': wan2_ip
}

print('\nStarting traceroute from private IP to 8.8.8.8...')
response = requests.post(traceroute_url, headers=headers, json=traceroute_data)
print(f'Traceroute POST status: {response.status_code}')

if response.status_code == 201:
    result_data = response.json()
    traceroute_id = result_data.get('tracerouteId')
    print(f'Traceroute ID: {traceroute_id}')
    print(f'Initial status: {result_data.get("status")}')
    
    # Step 2: Poll for results
    result_url = f'https://api.meraki.com/api/v1/devices/{device_serial}/liveTools/traceroute/{traceroute_id}'
    
    print('\nPolling for results...')
    for i in range(30):  # Poll for up to 90 seconds
        time.sleep(3)
        result_response = requests.get(result_url, headers=headers)
        
        if result_response.status_code == 200:
            trace_result = result_response.json()
            status = trace_result.get('status')
            print(f'  Status: {status}')
            
            if status == 'complete':
                print('\n✅ Traceroute complete!')
                
                # Show the full result
                print('\nFull traceroute result:')
                print(json.dumps(trace_result, indent=2))
                
                # Extract and analyze the hops
                if 'results' in trace_result and 'hops' in trace_result['results']:
                    print('\n🔍 Hop Analysis for Carrier Detection:')
                    print('=' * 60)
                    
                    hops = trace_result['results']['hops']
                    for hop in hops[:5]:  # Analyze first 5 hops
                        hop_num = hop.get('number', '?')
                        hosts = hop.get('hosts', [])
                        
                        if hosts:
                            print(f'\nHop {hop_num}:')
                            for host in hosts:
                                ip = host.get('ip', 'unknown')
                                hostname = host.get('hostname', 'N/A')
                                print(f'  IP: {ip}')
                                print(f'  Hostname: {hostname}')
                                
                                # Check for carrier indicators
                                if hostname and hostname != 'N/A':
                                    hostname_lower = hostname.lower()
                                    if 'verizon' in hostname_lower or 'vzw' in hostname_lower or 'myvzw' in hostname_lower:
                                        print(f'  🎯 VERIZON DETECTED!')
                                    elif 'att' in hostname_lower or 'sbcglobal' in hostname_lower:
                                        print(f'  🎯 AT&T DETECTED!')
                                    elif 'tmobile' in hostname_lower or 't-mobile' in hostname_lower:
                                        print(f'  🎯 T-MOBILE DETECTED!')
                break
                
            elif status == 'failed':
                print('\n❌ Traceroute failed')
                print(json.dumps(trace_result, indent=2))
                break
        else:
            print(f'Error polling results: {result_response.status_code}')
            break
            
else:
    print(f'Failed to start traceroute: {response.text[:500]}')