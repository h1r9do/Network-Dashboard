#!/usr/bin/env python3
"""
Check all sites starting with IA
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
    """Check IA sites"""
    print("🔍 Checking Sites Starting with 'IA'")
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
    
    # Find IA networks
    ia_networks = []
    for network in networks:
        if network['name'].startswith('IA'):
            ia_networks.append(network)
    
    print(f"✅ Found {len(ia_networks)} networks starting with 'IA':")
    for net in sorted(ia_networks, key=lambda x: x['name']):
        print(f"   - {net['name']}")
    
    # Check each network's devices
    print("\n📊 Checking device notes:")
    
    for network in ia_networks:
        network_name = network['name']
        network_id = network['id']
        
        # Get devices
        response = requests.get(f"{BASE_URL}/networks/{network_id}/devices", headers=headers)
        devices = response.json()
        
        # Find MX device
        for device in devices:
            if device.get('model', '').startswith('MX'):
                notes = device.get('notes', '')
                if notes:
                    print(f"\n📝 {network_name} - {device.get('name', 'Device')}:")
                    print("   Notes:")
                    for line in notes.split('\n'):
                        print(f"   {line}")
                    
                    # Check for issues
                    if '\\n' in notes:
                        print("   ⚠️  Has literal \\n!")
                    elif '\n' not in notes and 'WAN' in notes:
                        print("   ⚠️  Missing newlines!")
                break

if __name__ == "__main__":
    main()