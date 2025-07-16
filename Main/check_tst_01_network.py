#!/usr/bin/env python3
"""
Check access to TST 01 network in DTC-Network-Engineering organization
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def make_api_request(url, params=None):
    """Make API request with error handling"""
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("Checking for TST 01 network in DTC-Network-Engineering organization...")
    
    # Get all organizations
    url = f"{BASE_URL}/organizations"
    orgs = make_api_request(url)
    
    if not orgs:
        print("Failed to get organizations")
        return
    
    # Find DTC-Network-Engineering
    target_org = None
    for org in orgs:
        org_name = org.get('name', '')
        print(f"Found organization: {org_name} (ID: {org.get('id')})")
        if org_name == "DTC-Network-Engineering":
            target_org = org
            
    if not target_org:
        print("\nDTC-Network-Engineering organization not found!")
        return
        
    org_id = target_org['id']
    print(f"\nFound DTC-Network-Engineering with ID: {org_id}")
    
    # Get networks in this organization
    url = f"{BASE_URL}/organizations/{org_id}/networks"
    networks = make_api_request(url)
    
    if not networks:
        print("Failed to get networks or no networks found")
        return
        
    print(f"\nFound {len(networks)} networks in DTC-Network-Engineering:")
    
    # Look for TST 01
    tst_01_network = None
    for network in networks:
        network_name = network.get('name', '')
        network_id = network.get('id', '')
        print(f"  - {network_name} (ID: {network_id})")
        if network_name == "TST 01":
            tst_01_network = network
            
    if not tst_01_network:
        print("\nTST 01 network not found in this organization!")
        return
        
    print(f"\n✓ Found TST 01 network!")
    print(f"Network ID: {tst_01_network['id']}")
    print(f"Network Name: {tst_01_network['name']}")
    print(f"Product Types: {tst_01_network.get('productTypes', [])}")
    print(f"Time Zone: {tst_01_network.get('timeZone', 'Not set')}")
    print(f"Tags: {tst_01_network.get('tags', [])}")
    
    # Try to get devices in this network
    print("\nChecking devices in TST 01...")
    url = f"{BASE_URL}/networks/{tst_01_network['id']}/devices"
    devices = make_api_request(url)
    
    if devices:
        print(f"Found {len(devices)} devices:")
        for device in devices:
            print(f"  - {device.get('name', 'Unnamed')} ({device.get('model', 'Unknown')}) - Serial: {device.get('serial', 'N/A')}")
    else:
        print("No devices found or unable to access devices")
        
    # Check if we can access VLANs (if it's an MX network)
    if 'appliance' in tst_01_network.get('productTypes', []):
        print("\nChecking VLANs...")
        url = f"{BASE_URL}/networks/{tst_01_network['id']}/appliance/vlans"
        vlans = make_api_request(url)
        
        if vlans:
            print(f"Found {len(vlans)} VLANs - Access confirmed!")
            for vlan in vlans[:3]:  # Show first 3
                print(f"  - VLAN {vlan.get('id')}: {vlan.get('name')} ({vlan.get('subnet')})")
        else:
            print("Unable to access VLANs")

if __name__ == "__main__":
    main()