#!/usr/bin/env python3
"""
Find networks containing IAN
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ORG_NAME = "DTC-Store-Inventory-All"

def main():
    """Find IAN networks"""
    print("🔍 Finding Networks with 'IAN'")
    print("=" * 60)
    
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Get organization
    response = requests.get(f"{BASE_URL}/organizations", headers=headers)
    orgs = response.json()
    org_id = None
    for org in orgs:
        if org['name'] == ORG_NAME:
            org_id = org['id']
            break
    
    # Get networks
    response = requests.get(f"{BASE_URL}/organizations/{org_id}/networks", headers=headers)
    networks = response.json()
    
    # Find networks with IAN
    ian_networks = []
    for network in networks:
        if 'IAN' in network['name'].upper():
            ian_networks.append(network['name'])
    
    print(f"✅ Found {len(ian_networks)} networks containing 'IAN':")
    for name in sorted(ian_networks):
        print(f"   - {name}")
    
    # Check a sample network for notes format
    if ian_networks:
        sample_network_name = ian_networks[0]
        print(f"\n🔍 Checking notes for: {sample_network_name}")
        
        # Find the network
        for network in networks:
            if network['name'] == sample_network_name:
                network_id = network['id']
                
                # Get devices
                response = requests.get(f"{BASE_URL}/networks/{network_id}/devices", headers=headers)
                devices = response.json()
                
                # Find MX device
                for device in devices:
                    if device.get('model', '').startswith('MX'):
                        notes = device.get('notes', '')
                        if notes:
                            print(f"\n📝 {sample_network_name} Notes:")
                            print("=" * 40)
                            print(notes)
                            print("=" * 40)
                            print(f"\n🔍 Raw (repr): {repr(notes)}")
                            
                            if '\\n' in notes:
                                print("\n⚠️  Contains literal \\n - needs fixing!")
                            else:
                                print("\n✅ Has proper newlines")
                        break
                break

if __name__ == "__main__":
    main()