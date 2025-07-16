#!/usr/bin/env python3
"""
Check clients connected to ALB 03
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

print("ALB 03 Connected Clients")
print("=" * 50)

# Get device clients
url = f"https://api.meraki.com/api/v1/devices/{device_serial}/clients"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    clients = response.json()
    print(f"\nFound {len(clients)} connected clients")
    
    # Look for gateway devices (typically .1 addresses)
    print("\nLooking for potential WAN gateway devices...")
    print("-" * 100)
    
    gateway_candidates = []
    private_ip_clients = []
    
    for client in clients:
        ip = client.get('ip', '')
        mac = client.get('mac', '')
        description = client.get('description', '') or ''
        manufacturer = client.get('manufacturer', '') or 'Unknown'
        vlan = client.get('vlan', '')
        
        # Check for private IP ranges
        if ip:
            if ip.startswith('192.168.0.'):
                private_ip_clients.append(client)
                # Gateway is typically .1
                if ip.endswith('.1') or ip == '192.168.0.1':
                    gateway_candidates.append(client)
            elif ip.endswith('.1'):
                gateway_candidates.append(client)
    
    # Show gateway candidates
    if gateway_candidates:
        print(f"\nPotential gateway devices:")
        for client in gateway_candidates:
            print(f"\n  IP: {client.get('ip')}")
            print(f"  MAC: {client.get('mac')}")
            print(f"  Manufacturer: {client.get('manufacturer', 'Unknown')}")
            print(f"  Description: {client.get('description', 'N/A')}")
            print(f"  VLAN: {client.get('vlan', 'N/A')}")
    
    # Show all 192.168.0.x devices
    if private_ip_clients:
        print(f"\n\nAll devices on 192.168.0.x subnet ({len(private_ip_clients)} found):")
        print("-" * 100)
        print(f"{'IP Address':<20} {'MAC Address':<20} {'Manufacturer':<30} {'Description':<30}")
        print("-" * 100)
        
        for client in private_ip_clients:
            ip = client.get('ip', 'N/A')
            mac = client.get('mac', 'N/A')
            manufacturer = client.get('manufacturer', 'Unknown')
            description = (client.get('description', '') or '')[:30]
            
            print(f"{ip:<20} {mac:<20} {manufacturer:<30} {description:<30}")
            
            # Identify potential carriers based on manufacturer
            if manufacturer:
                mfg_lower = manufacturer.lower()
                carrier_hint = None
                
                if any(term in mfg_lower for term in ['verizon', 'novatel', 'inseego']):
                    carrier_hint = "VERIZON WIRELESS"
                elif any(term in mfg_lower for term in ['sierra', 'netgear']):
                    carrier_hint = "Multiple carriers possible"
                elif 'cradlepoint' in mfg_lower:
                    carrier_hint = "Multi-carrier gateway"
                    
                if carrier_hint and ip == '192.168.0.1':
                    print(f"     ^ Likely WAN2 gateway - {carrier_hint}")
    
    # Also check for any interesting manufacturers
    print("\n\nManufacturer summary:")
    manufacturers = {}
    for client in clients:
        mfg = client.get('manufacturer', 'Unknown')
        if mfg:
            manufacturers[mfg] = manufacturers.get(mfg, 0) + 1
    
    for mfg, count in sorted(manufacturers.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {mfg}: {count} devices")
        
else:
    print(f"Error: {response.status_code}")
    print(response.text)