#!/usr/bin/env python3
"""
Check device clients and DHCP information for ALB 03
"""

import os
import requests
import json
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
network_id = 'L_3790904986339115389'  # From earlier test

print("ALB 03 Client and Connection Information")
print("=" * 50)

# Try different endpoints
endpoints = [
    (f"/devices/{device_serial}/clients", "Device clients"),
    (f"/networks/{network_id}/clients", "Network clients"),  
    (f"/devices/{device_serial}/clients?t0=2592000", "Device clients (30 days)"),
    (f"/networks/{network_id}/devices/{device_serial}/clients", "Network device clients"),
    (f"/devices/{device_serial}/appliance/dhcp/subnets", "DHCP subnets"),
    (f"/networks/{network_id}/appliance/vlans", "VLANs"),
]

for endpoint, description in endpoints:
    print(f"\n\nTrying: {description}")
    print(f"Endpoint: {endpoint}")
    
    url = f"https://api.meraki.com/api/v1{endpoint}"
    response = requests.get(url, headers=headers)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            print(f"✅ Found {len(data)} items")
            
            # Look for WAN-related entries
            wan_related = []
            for item in data:
                # Check various fields that might indicate WAN connection
                if isinstance(item, dict):
                    ip = item.get('ip', '')
                    vlan = item.get('vlan', '')
                    description = item.get('description', '')
                    mac = item.get('mac', '')
                    
                    # Look for private IPs that might be WAN gateways
                    if ip and (ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.')):
                        if 'WAN' in str(vlan).upper() or 'WAN' in description.upper() or ip.endswith('.1'):
                            wan_related.append(item)
                            
            if wan_related:
                print(f"\nPotential WAN-related entries:")
                for item in wan_related:
                    print(f"\n  IP: {item.get('ip')}")
                    print(f"  MAC: {item.get('mac')}")
                    print(f"  Description: {item.get('description', 'N/A')}")
                    print(f"  Manufacturer: {item.get('manufacturer', 'N/A')}")
                    
        elif isinstance(data, dict):
            print("✅ Got response (dict)")
            print(json.dumps(data, indent=2)[:500])
    elif response.status_code == 404:
        print("❌ Not found")
    else:
        print(f"❌ Error: {response.text[:100]}")

# Try to get more network information
print("\n\nChecking network settings...")
settings_url = f"https://api.meraki.com/api/v1/networks/{network_id}/appliance/settings"
response = requests.get(settings_url, headers=headers)

if response.status_code == 200:
    settings = response.json()
    print("\nNetwork appliance settings:")
    print(json.dumps(settings, indent=2))