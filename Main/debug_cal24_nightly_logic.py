#!/usr/bin/env python3
"""Debug the nightly script logic for CAL 24"""

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

BASE_URL = "https://api.meraki.com/api/v1"

def get_organization_uplink_statuses(org_id):
    """Exactly like nightly script"""
    all_statuses = []
    url = f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses"
    params = {'perPage': 1000, 'startingAfter': None}
    
    while True:
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            statuses = response.json()
            all_statuses.extend(statuses)
            
            # Check for more pages
            link_header = response.headers.get('Link', '')
            if 'rel="next"' not in link_header:
                break
            # Extract next page cursor
            for link in link_header.split(','):
                if 'rel="next"' in link:
                    start_after = link.split('startingAfter=')[1].split('&')[0].split('>')[0]
                    params['startingAfter'] = start_after
                    break
        except Exception as e:
            print(f"Error getting uplink statuses: {e}")
            break
    
    return all_statuses

def get_all_networks(org_id):
    """Get all networks from org"""
    url = f"{BASE_URL}/organizations/{org_id}/networks"
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting networks: {e}")
        return []

def get_devices(network_id):
    """Get devices in a network"""
    url = f"{BASE_URL}/networks/{network_id}/devices"
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting devices for network {network_id}: {e}")
        return []

def debug_cal24_nightly():
    """Debug exactly what nightly script would see for CAL 24"""
    
    # Get org ID
    orgs_response = requests.get(f"{BASE_URL}/organizations", headers=headers, timeout=30)
    org_id = None
    for org in orgs_response.json():
        if org.get('name') == "DTC-Store-Inventory-All":
            org_id = org['id']
            break
    
    if not org_id:
        print("Organization not found")
        return
    
    print(f"=== Debugging CAL 24 in nightly script logic ===")
    print(f"Organization ID: {org_id}")
    
    # Step 1: Get uplink statuses (this is where CAL 24 device is missing)
    print(f"\n1. Getting uplink statuses...")
    uplink_statuses = get_organization_uplink_statuses(org_id)
    print(f"Found {len(uplink_statuses)} devices with uplink data")
    
    # Look for CAL 24 device in uplinks
    cal24_device_serial = "Q2QN-YZRA-UCYJ"
    cal24_in_uplinks = False
    
    for status in uplink_statuses:
        if status.get('serial') == cal24_device_serial:
            cal24_in_uplinks = True
            print(f"✓ Found CAL 24 device in uplinks: {status}")
            break
    
    if not cal24_in_uplinks:
        print(f"✗ CAL 24 device {cal24_device_serial} NOT in uplink statuses")
    
    # Step 2: Get all networks and look for CAL 24
    print(f"\n2. Getting all networks...")
    networks = get_all_networks(org_id)
    print(f"Found {len(networks)} networks")
    
    cal24_network = None
    for net in networks:
        if net.get('name') == 'CAL 24':
            cal24_network = net
            print(f"✓ Found CAL 24 network: {net}")
            break
    
    if not cal24_network:
        print(f"✗ CAL 24 network NOT found in networks list")
        
        # Look for any similar names
        cal_networks = [net for net in networks if 'CAL' in net.get('name', '')]
        print(f"Found {len(cal_networks)} networks with 'CAL' in name:")
        for net in cal_networks[:10]:  # Show first 10
            print(f"  - {net.get('name')}")
        
        return
    
    # Step 3: Get devices in CAL 24 network
    print(f"\n3. Getting devices in CAL 24 network...")
    devices = get_devices(cal24_network['id'])
    print(f"Found {len(devices)} devices in CAL 24 network")
    
    for device in devices:
        print(f"  Device: {device}")
        
        # Check if this is an MX device
        model = device.get('model', '')
        if model.startswith("MX"):
            serial = device.get('serial')
            print(f"\n  Found MX device: {serial}")
            
            # This is where nightly script would check uplink_dict
            print(f"  Checking uplink data for {serial}...")
            
            # Simulate nightly script logic
            if not cal24_in_uplinks:
                print(f"  ✗ No uplink data found for {serial}")
                print(f"  → This means wan1_ip and wan2_ip would be empty")
                print(f"  → ARIN providers would be 'Unknown'")
            else:
                print(f"  ✓ Uplink data available")
    
    # Summary
    print(f"\n4. SUMMARY:")
    print(f"   - CAL 24 network exists in Meraki: {cal24_network is not None}")
    print(f"   - CAL 24 device in uplink status: {cal24_in_uplinks}")
    print(f"   - This explains why database has device but no IPs")
    
    if cal24_network and not cal24_in_uplinks:
        print(f"\n5. CONCLUSION:")
        print(f"   - Network exists, device exists, but no uplink status")
        print(f"   - Device may be offline, disconnected, or not reporting uplinks")
        print(f"   - Nightly script stores device but with NULL IP addresses")
        print(f"   - ARIN refresh fails because there are no IPs to look up")

if __name__ == "__main__":
    debug_cal24_nightly()