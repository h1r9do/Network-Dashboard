#!/usr/bin/env python3
"""
Verify TST 01 current state before deployment
"""

import os
import sys
import json
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

def make_api_request(url):
    """Make API request with error handling"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    """Verify current state"""
    network_id = "L_3790904986339115852"  # TST 01
    
    print("Verifying TST 01 current state...")
    print("=" * 50)
    
    # Check current VLANs
    print("\nCurrent VLANs:")
    url = f"{BASE_URL}/networks/{network_id}/appliance/vlans"
    vlans = make_api_request(url)
    
    if vlans:
        for vlan in vlans:
            print(f"  VLAN {vlan['id']}: {vlan['name']} - {vlan.get('subnet', 'No subnet')}")
    
    # Check firewall rules count
    print("\nCurrent Firewall Rules:")
    url = f"{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules"
    rules = make_api_request(url)
    
    if rules:
        print(f"  Total rules: {len(rules.get('rules', []))}")
    
    # Check devices
    print("\nCurrent Devices:")
    url = f"{BASE_URL}/networks/{network_id}/devices"
    devices = make_api_request(url)
    
    if devices:
        for device in devices:
            print(f"  {device.get('name', 'Unnamed')} - {device.get('model')} ({device.get('serial')})")
    
    print("\n" + "=" * 50)
    print("Ready for deployment. This is a TEST network (TST 01).")
    print("The deployment will:")
    print("1. Replace all VLANs with AZP 30 config + migration rules")
    print("2. Apply NEO 07 firewall rules with VLAN mapping")
    print("3. Update all switch ports with new VLAN assignments")
    print("4. Use test network prefix 10.255.255.x for all 10.x networks")

if __name__ == "__main__":
    main()