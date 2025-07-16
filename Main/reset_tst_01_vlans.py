#!/usr/bin/env python3
"""
Reset TST 01 to default state - delete all VLANs except default
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
        elif method == 'DELETE':
            response = requests.delete(url, headers=HEADERS, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, headers=HEADERS, json=data, timeout=30)
            
        response.raise_for_status()
        
        if response.text:
            return response.json()
        return {}
        
    except Exception as e:
        print(f"Error {method} {url}: {e}")
        return None

def main():
    """Reset TST 01 VLANs"""
    network_id = "L_3790904986339115852"  # TST 01
    
    print("Resetting TST 01 to default state...")
    
    # Get current VLANs
    url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
    vlans = make_api_request(url)
    
    if not vlans:
        print("Failed to get current VLANs")
        return
    
    print(f"\nCurrent VLANs: {len(vlans)}")
    
    # Delete all non-default VLANs
    for vlan in vlans:
        vlan_id = vlan['id']
        if vlan_id != 1:
            print(f"Deleting VLAN {vlan_id} ({vlan['name']})...")
            url = f"{BASE_URL}/networks/{network_id}/appliance/vlans/{vlan_id}"
            make_api_request(url, method='DELETE')
            time.sleep(1)
    
    # Create default VLAN 1 if it doesn't exist
    default_exists = any(v['id'] == 1 for v in vlans)
    if not default_exists:
        print("\nCreating default VLAN 1...")
        vlan_data = {
            'id': 1,
            'name': 'Default',
            'subnet': '192.168.128.0/24',
            'applianceIp': '192.168.128.1'
        }
        url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
        make_api_request(url, method='PUT', data=vlan_data)
    else:
        # Update VLAN 1 to default settings
        print("\nResetting VLAN 1 to default...")
        vlan_data = {
            'name': 'Default',
            'subnet': '192.168.128.0/24',
            'applianceIp': '192.168.128.1'
        }
        url = f"{BASE_URL}/networks/{network_id}/appliance/vlans/1"
        make_api_request(url, method='PUT', data=vlan_data)
    
    # Verify final state
    print("\nVerifying final state...")
    url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
    vlans = make_api_request(url)
    
    if vlans:
        print(f"Final VLANs: {len(vlans)}")
        for vlan in vlans:
            print(f"  VLAN {vlan['id']}: {vlan['name']} - {vlan.get('subnet', 'No subnet')}")
    
    print("\n✅ Reset complete!")

if __name__ == "__main__":
    main()