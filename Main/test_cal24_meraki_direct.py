#!/usr/bin/env python3
"""
Test direct Meraki API call for CAL 24 to see why no IPs are returned
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

meraki_api_key = os.getenv('MERAKI_API_KEY')
if not meraki_api_key:
    print("ERROR: Meraki API key not found!")
    exit(1)

print("Testing direct Meraki API for CAL 24...")
print("="*80)

# Headers
headers = {
    'X-Cisco-Meraki-API-Key': meraki_api_key,
    'Content-Type': 'application/json'
}

# Get organization
org_name = "DTC-Store-Inventory-All"
print("1. Getting organization...")
orgs_response = requests.get("https://api.meraki.com/api/v1/organizations", headers=headers, timeout=30)
org_id = None
for org in orgs_response.json():
    if org.get('name') == org_name:
        org_id = org['id']
        print(f"✓ Found org: {org_name} (ID: {org_id})")
        break

if not org_id:
    print("✗ Organization not found!")
    exit(1)

# Look for CAL 24 network
print("\n2. Searching for CAL 24 network...")
networks_url = f"https://api.meraki.com/api/v1/organizations/{org_id}/networks"
networks_response = requests.get(networks_url, headers=headers, timeout=30)

cal24_network = None
for network in networks_response.json():
    if network.get('name') == 'CAL 24':
        cal24_network = network
        print(f"✓ Found network: {network['name']} (ID: {network['id']})")
        break

if not cal24_network:
    print("✗ CAL 24 network not found!")
    # Show similar networks
    print("\nNetworks containing 'CAL':")
    for network in networks_response.json():
        if 'CAL' in network.get('name', ''):
            print(f"  - {network['name']}")
    exit(1)

# Get devices in network
print("\n3. Getting devices in CAL 24...")
devices_url = f"https://api.meraki.com/api/v1/networks/{cal24_network['id']}/devices"
devices_response = requests.get(devices_url, headers=headers, timeout=30)

mx_device = None
for device in devices_response.json():
    print(f"  Found device: {device.get('model')} (Serial: {device.get('serial')})")
    if device.get('model', '').startswith('MX'):
        mx_device = device
        print(f"  ✓ This is an MX device")

if not mx_device:
    print("✗ No MX device found!")
    exit(1)

# Get uplink status
print(f"\n4. Getting uplink status for device {mx_device['serial']}...")
uplink_url = f"https://api.meraki.com/api/v1/organizations/{org_id}/appliance/uplink/statuses"
response = requests.get(uplink_url, headers=headers, timeout=30)
all_uplinks = response.json()

found_device = False
for device_status in all_uplinks:
    if device_status.get('serial') == mx_device['serial']:
        found_device = True
        print(f"✓ Found uplink status for {device_status.get('serial')}")
        print(f"  Network ID: {device_status.get('networkId')}")
        print(f"  Last Reported: {device_status.get('lastReportedAt')}")
        
        uplinks = device_status.get('uplinks', [])
        if not uplinks:
            print("  ⚠️  No uplinks reported!")
        else:
            for uplink in uplinks:
                print(f"\n  Uplink: {uplink.get('interface')}")
                print(f"    Status: {uplink.get('status')}")
                print(f"    IP: {uplink.get('ip')}")
                print(f"    Public IP: {uplink.get('publicIp')}")
                print(f"    Gateway: {uplink.get('gateway')}")
                print(f"    Primary DNS: {uplink.get('primaryDns')}")
                print(f"    Secondary DNS: {uplink.get('secondaryDns')}")
        break

if not found_device:
    print(f"✗ No uplink status found for device {mx_device['serial']}")

print("\n" + "="*80)