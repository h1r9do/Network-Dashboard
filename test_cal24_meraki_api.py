#!/usr/bin/env python3
"""Test Meraki API for CAL 24 device directly"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

meraki_api_key = os.getenv('MERAKI_API_KEY')
if not meraki_api_key:
    print("No Meraki API key found")
    exit(1)

headers = {
    'X-Cisco-Meraki-API-Key': meraki_api_key,
    'Content-Type': 'application/json'
}

# Get organization ID
org_name = "DTC-Store-Inventory-All"
orgs_response = requests.get("https://api.meraki.com/api/v1/organizations", headers=headers, timeout=30)
org_id = None
for org in orgs_response.json():
    if org.get('name') == org_name:
        org_id = org['id']
        break

if not org_id:
    print("Organization not found")
    exit(1)

print(f"Organization ID: {org_id}")

# Get uplink status for all devices
print("\nGetting uplink statuses...")
uplink_url = f"https://api.meraki.com/api/v1/organizations/{org_id}/appliance/uplink/statuses"
response = requests.get(uplink_url, headers=headers, timeout=30)

if response.status_code != 200:
    print(f"API Error: {response.status_code} - {response.text}")
    exit(1)

all_uplinks = response.json()
print(f"Found {len(all_uplinks)} devices with uplink data")

# Find CAL 24 device specifically
device_serial = "Q2QN-YZRA-UCYJ"
cal24_found = False

for device_status in all_uplinks:
    if device_status.get('serial') == device_serial:
        cal24_found = True
        print(f"\n=== Found CAL 24 device: {device_serial} ===")
        print(f"Network ID: {device_status.get('networkId')}")
        print(f"Uplinks data: {device_status}")
        
        uplinks = device_status.get('uplinks', [])
        print(f"Number of uplinks: {len(uplinks)}")
        
        for i, uplink in enumerate(uplinks):
            print(f"\nUplink {i+1}:")
            print(f"  Interface: {uplink.get('interface')}")
            print(f"  Status: {uplink.get('status')}")
            print(f"  IP: {uplink.get('ip')}")
            print(f"  Public IP: {uplink.get('publicIp')}")
            print(f"  Gateway: {uplink.get('gateway')}")
            print(f"  DNS: {uplink.get('dns')}")
            print(f"  Using static IP: {uplink.get('usingStaticIp')}")
        break

if not cal24_found:
    print(f"\nCAL 24 device {device_serial} NOT found in uplink statuses")
    
    # Check if device exists in the organization at all
    print("\nChecking networks for CAL 24...")
    networks_url = f"https://api.meraki.com/api/v1/organizations/{org_id}/networks"
    networks_response = requests.get(networks_url, headers=headers, timeout=30)
    
    cal24_network = None
    for network in networks_response.json():
        if network.get('name') == 'CAL 24':
            cal24_network = network
            print(f"Found CAL 24 network: {network}")
            break
    
    if cal24_network:
        # Check devices in this network
        devices_url = f"https://api.meraki.com/api/v1/networks/{cal24_network['id']}/devices"
        devices_response = requests.get(devices_url, headers=headers, timeout=30)
        print(f"\nDevices in CAL 24 network: {devices_response.json()}")
    else:
        print("CAL 24 network not found in API")