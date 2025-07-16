#!/usr/bin/env python3
"""
One-off script to test traceroute on ALB 03
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

print(f'ALB 03 Traceroute Test')
print(f'Device Serial: {device_serial}')
print(f'WAN2 IP (Private): {wan2_ip}')
print('-' * 50)

# Create traceroute request
url = f'https://api.meraki.com/api/v1/devices/{device_serial}/liveTools/traceRoute'
data = {
    'target': '8.8.8.8',
    'sourceInterface': wan2_ip
}

print('\nCreating traceroute request...')
response = requests.post(url, headers=headers, json=data)

if response.status_code == 201:
    result = response.json()
    traceroute_id = result.get('traceRouteId')
    print(f'✅ Traceroute ID: {traceroute_id}')
    
    # Poll for results
    result_url = f'https://api.meraki.com/api/v1/devices/{device_serial}/liveTools/traceRoute/{traceroute_id}'
    
    print('\nPolling for results...')
    for i in range(30):
        time.sleep(3)
        response = requests.get(result_url, headers=headers)
        
        if response.status_code == 200:
            trace_result = response.json()
            status = trace_result.get('status')
            
            if status == 'complete':
                print('\n✅ TRACEROUTE COMPLETE!\n')
                
                # Show raw results
                print('Raw results:')
                print(json.dumps(trace_result, indent=2))
                
                # Analyze hops
                if 'results' in trace_result:
                    hops = trace_result.get('results', [])
                    print(f'\n\nFound {len(hops)} hops:')
                    print('-' * 50)
                    
                    for hop in hops[:10]:  # Show first 10 hops
                        hop_num = hop.get('hop')
                        ip = hop.get('ip', '*')
                        rtt = hop.get('rttAvg', 0)
                        
                        print(f'\nHop {hop_num}: {ip} ({rtt*1000:.1f}ms)')
                        
                        # Try reverse DNS
                        if ip and ip != '*':
                            try:
                                import socket
                                hostname = socket.gethostbyaddr(ip)[0]
                                print(f'  Hostname: {hostname}')
                                
                                # Check for carrier
                                hostname_lower = hostname.lower()
                                if 'myvzw' in hostname_lower or 'verizon' in hostname_lower:
                                    print('  🎯 VERIZON DETECTED!')
                                elif 'att' in hostname_lower:
                                    print('  🎯 AT&T DETECTED!')
                                elif 'tmobile' in hostname_lower:
                                    print('  🎯 T-MOBILE DETECTED!')
                            except:
                                print('  Hostname: No PTR record')
                
                break
                
            elif status == 'failed':
                print('\n❌ Traceroute failed!')
                print(json.dumps(trace_result, indent=2))
                break
                
            else:
                print(f'  Status: {status}', end='\r')
        else:
            print(f'\n❌ Error: {response.status_code}')
            break
            
    else:
        print('\n⏱️  Timeout waiting for results')
        
elif response.status_code == 429:
    print('\n❌ Rate limited! Response:')
    print(response.text)
    
elif response.status_code == 404:
    print('\n❌ 404 Not Found - API endpoint may not be available')
    print(response.text[:200])
    
else:
    print(f'\n❌ Error {response.status_code}:')
    print(response.text[:500])