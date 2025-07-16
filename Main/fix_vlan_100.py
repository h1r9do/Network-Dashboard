#!/usr/bin/env python3
"""
Fix VLAN 100 - Delete VLAN 1 and create VLAN 100
"""

import os
import requests
import time
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

def make_api_request(url, method='GET', data=None):
    """Make API request"""
    time.sleep(0.5)
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=HEADERS, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, headers=HEADERS, json=data, timeout=30)
        elif method == 'POST':
            response = requests.post(url, headers=HEADERS, json=data, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, headers=HEADERS, timeout=30)
            
        response.raise_for_status()
        
        if response.text:
            return response.json()
        return {}
        
    except Exception as e:
        print(f"Error {method} {url}: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return None

def main():
    """Fix VLAN 100"""
    network_id = "L_3790904986339115852"  # TST 01
    
    print("Fixing VLAN 100 configuration...")
    
    # Step 1: Delete VLAN 1
    print("\n1. Deleting VLAN 1...")
    url = f"{BASE_URL}/networks/{network_id}/appliance/vlans/1"
    result = make_api_request(url, method='DELETE')
    
    if result is not None:
        print("   ✅ VLAN 1 deleted successfully")
    else:
        print("   ❌ Failed to delete VLAN 1")
        return
    
    time.sleep(2)  # Wait a bit
    
    # Step 2: Create VLAN 100
    print("\n2. Creating VLAN 100...")
    vlan_data = {
        'id': 100,
        'name': 'Data',
        'subnet': '10.255.255.0/25',
        'applianceIp': '10.255.255.1'
    }
    
    url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
    result = make_api_request(url, method='POST', data=vlan_data)
    
    if result:
        print("   ✅ VLAN 100 created successfully")
    else:
        print("   ❌ Failed to create VLAN 100")
        return
    
    # Step 3: Verify final configuration
    print("\n3. Verifying final VLAN configuration...")
    url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
    vlans = make_api_request(url)
    
    if vlans:
        print("\nCurrent VLANs:")
        for vlan in sorted(vlans, key=lambda x: x['id']):
            print(f"   VLAN {vlan['id']:3d}: {vlan['name']:15s} - {vlan.get('subnet', 'No subnet')}")
    
    print("\n✅ VLAN 100 migration complete!")

if __name__ == "__main__":
    main()