#!/usr/bin/env python3
"""
Final traceroute test with sourceInterface
"""

import os
import requests
import json
import time
import socket
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

print("ALB 03 Traceroute Test with sourceInterface")
print("=" * 50)

# Create traceroute with sourceInterface
url = f'https://api.meraki.com/api/v1/devices/{device_serial}/liveTools/traceRoute'
data = {
    'target': '8.8.8.8',
    'sourceInterface': wan2_ip
}

print(f"\nRequest data: {json.dumps(data, indent=2)}")
print("\nCreating traceroute request...")

response = requests.post(url, headers=headers, json=data)
print(f"Status: {response.status_code}")

if response.status_code == 201:
    result = response.json()
    traceroute_id = result.get('traceRouteId')
    print(f"✅ Traceroute created! ID: {traceroute_id}")
    
    # Wait a bit then poll for results
    print("\nWaiting 5 seconds before polling...")
    time.sleep(5)
    
    result_url = f'https://api.meraki.com/api/v1/devices/{device_serial}/liveTools/traceRoute/{traceroute_id}'
    
    print("\nPolling for results...")
    for i in range(20):
        response = requests.get(result_url, headers=headers)
        
        if response.status_code == 200:
            trace_result = response.json()
            status = trace_result.get('status')
            print(f"  Attempt {i+1}: Status = {status}")
            
            if status == 'complete':
                print("\n✅ TRACEROUTE COMPLETE!\n")
                
                # Show full result
                print("Full result:")
                print(json.dumps(trace_result, indent=2))
                
                # Analyze hops
                if 'results' in trace_result:
                    hops = trace_result.get('results', [])
                    print(f"\n\n🔍 Analyzing {len(hops)} hops for cellular carrier:")
                    print("-" * 70)
                    
                    carrier_detected = None
                    
                    for hop in hops[:5]:
                        hop_num = hop.get('hop')
                        ip = hop.get('ip', '*')
                        rtt = hop.get('rttAvg', 0)
                        
                        if ip and ip != '*':
                            print(f"\nHop {hop_num}: {ip} ({rtt*1000:.1f}ms)")
                            
                            # Try reverse DNS
                            try:
                                hostname = socket.gethostbyaddr(ip)[0]
                                print(f"  Hostname: {hostname}")
                                
                                # Check for carrier patterns
                                hostname_lower = hostname.lower()
                                if any(pattern in hostname_lower for pattern in ['myvzw', 'verizon', 'vzw', 'cellco']):
                                    print('  🎯 VERIZON WIRELESS DETECTED!')
                                    carrier_detected = 'Verizon Wireless'
                                elif any(pattern in hostname_lower for pattern in ['att.net', 'sbcglobal', 'mobility']):
                                    print('  🎯 AT&T DETECTED!')
                                    carrier_detected = 'AT&T Mobility'
                                elif any(pattern in hostname_lower for pattern in ['tmobile', 't-mobile', 'tmus']):
                                    print('  🎯 T-MOBILE DETECTED!')
                                    carrier_detected = 'T-Mobile USA'
                            except:
                                print('  Hostname: No PTR record')
                        else:
                            print(f"\nHop {hop_num}: * (no response)")
                    
                    if carrier_detected:
                        print(f"\n\n✅ CELLULAR CARRIER CONFIRMED: {carrier_detected}")
                        print(f"   Private IP {wan2_ip} is using {carrier_detected}")
                    else:
                        print("\n\n❓ No cellular carrier detected from hostnames")
                
                break
                
            elif status == 'failed':
                print("\n❌ Traceroute failed!")
                print(json.dumps(trace_result, indent=2))
                break
        else:
            print(f"  Error getting results: {response.status_code}")
        
        time.sleep(3)
    else:
        print("\n⏱️  Timeout waiting for results")

else:
    print(f"❌ Error: {response.text}")