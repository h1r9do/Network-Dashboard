#!/usr/bin/env python3
"""
Check WAN interface details for ALB 03
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
network_id = 'L_3790904986339115389'

print("ALB 03 WAN Interface Details")
print("=" * 50)

# Get management interface (we know this works)
print("\n1. Management Interface:")
url = f"https://api.meraki.com/api/v1/devices/{device_serial}/managementInterface"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    mgmt = response.json()
    print(json.dumps(mgmt, indent=2))
    
    # WAN2 info
    wan2 = mgmt.get('wan2', {})
    if wan2.get('usingStaticIp') == False:
        print("\n🔍 WAN2 is using DHCP (dynamic IP)")
        print("   This suggests it's getting IP from a cellular modem or ISP router")

# Get appliance uplinks for the network
print("\n\n2. Network Appliance Uplinks:")
url = f"https://api.meraki.com/api/v1/networks/{network_id}/appliance/uplinks/statuses"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    uplinks = response.json()
    for uplink in uplinks:
        interface = uplink.get('interface', '')
        if interface == 'wan2':
            print(f"\nWAN2 Uplink Status:")
            print(f"  Status: {uplink.get('status')}")
            print(f"  IP: {uplink.get('ip')}")
            print(f"  Gateway: {uplink.get('gateway')}")
            print(f"  DNS: {uplink.get('dns')}")
            print(f"  Public IP: {uplink.get('publicIp')}")
            
            # The gateway IP might give us a clue
            gateway = uplink.get('gateway')
            if gateway == '192.168.0.1':
                print(f"\n  🎯 WAN2 gateway is {gateway}")
                print(f"     This is the device we need to identify!")
else:
    print(f"Error: {response.status_code}")

# Try to get DHCP info
print("\n\n3. DHCP Settings:")
url = f"https://api.meraki.com/api/v1/networks/{network_id}/appliance/vlans"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    vlans = response.json()
    for vlan in vlans:
        print(f"\nVLAN {vlan.get('id')}: {vlan.get('name')}")
        print(f"  Subnet: {vlan.get('subnet')}")
        print(f"  Appliance IP: {vlan.get('applianceIp')}")

# Get device details
print("\n\n4. Device Details:")
url = f"https://api.meraki.com/api/v1/devices/{device_serial}"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    device = response.json()
    # Check for any WAN-related fields
    for key, value in device.items():
        if 'wan' in key.lower() or 'uplink' in key.lower():
            print(f"  {key}: {value}")

# Check cellular settings if available
print("\n\n5. Cellular Settings (if available):")
url = f"https://api.meraki.com/api/v1/devices/{device_serial}/appliance/uplinks/settings"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    settings = response.json()
    print(json.dumps(settings, indent=2))
    
    # Check if there's cellular info
    interfaces = settings.get('interfaces', {})
    wan2_settings = interfaces.get('wan2', {})
    if wan2_settings:
        print(f"\nWAN2 Settings:")
        print(f"  Enabled: {wan2_settings.get('enabled')}")
        print(f"  VLAN tagging: {wan2_settings.get('vlanTagging', {})}")
        print(f"  SVI: {wan2_settings.get('svis', {})}")
else:
    print(f"Error: {response.status_code} - {response.text[:100]}")