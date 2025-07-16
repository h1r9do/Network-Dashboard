#!/usr/bin/env python3
"""Test CAL 24 network ID directly in Meraki API"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

meraki_api_key = os.getenv('MERAKI_API_KEY')
headers = {
    'X-Cisco-Meraki-API-Key': meraki_api_key,
    'Content-Type': 'application/json'
}

BASE_URL = "https://api.meraki.com/api/v1"

def test_cal24_network():
    # Network ID from database
    network_id = "L_650207196201636499"
    device_serial = "Q2QN-YZRA-UCYJ"
    
    print("=== Testing CAL 24 Network in Meraki API ===\n")
    
    # 1. Test if network exists
    print("1. Testing network endpoint:")
    try:
        url = f"{BASE_URL}/networks/{network_id}"
        response = requests.get(url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            network = response.json()
            print(f"   ✓ Network found: {network.get('name')}")
            print(f"   Organization ID: {network.get('organizationId')}")
            print(f"   Time Zone: {network.get('timeZone')}")
        else:
            print(f"   ✗ Network not found: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 2. Test device in network
    print("\n2. Testing device in network:")
    try:
        url = f"{BASE_URL}/networks/{network_id}/devices"
        response = requests.get(url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            devices = response.json()
            print(f"   Found {len(devices)} devices")
            for device in devices:
                if device.get('serial') == device_serial:
                    print(f"   ✓ Found CAL 24 device: {device}")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. Test device directly
    print("\n3. Testing device endpoint directly:")
    try:
        url = f"{BASE_URL}/devices/{device_serial}"
        response = requests.get(url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            device = response.json()
            print(f"   ✓ Device found:")
            print(f"   Name: {device.get('name')}")
            print(f"   Model: {device.get('model')}")
            print(f"   Network ID: {device.get('networkId')}")
            print(f"   Notes: {device.get('notes', '')[:100]}...")
        else:
            print(f"   ✗ Device not found: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. Test device uplink
    print("\n4. Testing device uplink status:")
    try:
        url = f"{BASE_URL}/devices/{device_serial}/appliance/uplinks/settings"
        response = requests.get(url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            settings = response.json()
            print(f"   ✓ Uplink settings: {settings}")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 5. Check why it's not in org-wide uplink status
    print("\n5. Checking organization uplink statuses for CAL 24:")
    try:
        # Get org ID first
        orgs_response = requests.get(f"{BASE_URL}/organizations", headers=headers, timeout=30)
        org_id = None
        for org in orgs_response.json():
            if org.get('name') == "DTC-Store-Inventory-All":
                org_id = org['id']
                break
        
        if org_id:
            url = f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses"
            params = {'networkIds[]': network_id}  # Filter for just CAL 24
            response = requests.get(url, headers=headers, params=params, timeout=30)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                statuses = response.json()
                print(f"   Found {len(statuses)} uplink statuses for network")
                for status in statuses:
                    if status.get('serial') == device_serial:
                        print(f"   ✓ CAL 24 uplink status: {status}")
                if not statuses:
                    print(f"   ✗ No uplink status for CAL 24 - device may be offline")
        else:
            print("   ✗ Organization not found")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 6. Check appliance performance (might have connectivity info)
    print("\n6. Testing appliance performance endpoint:")
    try:
        url = f"{BASE_URL}/devices/{device_serial}/appliance/performance"
        response = requests.get(url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            performance = response.json()
            print(f"   ✓ Performance data available")
            print(f"   WAN1 IP: {performance.get('wan1', {}).get('ip', 'N/A')}")
            print(f"   WAN2 IP: {performance.get('wan2', {}).get('ip', 'N/A')}")
        else:
            print(f"   ✗ Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_cal24_network()