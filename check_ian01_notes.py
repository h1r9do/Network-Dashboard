#!/usr/bin/env python3
"""
Check IAN 01 device notes specifically
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
    """Check IAN 01 notes"""
    print("🔍 Checking IAN 01 Device Notes")
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
    
    # Find IAN 01
    ian01_network = None
    for network in networks:
        if network['name'] == 'IAN 01':
            ian01_network = network
            break
    
    if not ian01_network:
        print("❌ IAN 01 network not found")
        return
    
    network_id = ian01_network['id']
    print(f"✅ Found IAN 01 network: {network_id}")
    
    # Get devices for this network
    response = requests.get(f"{BASE_URL}/networks/{network_id}/devices", headers=headers)
    devices = response.json()
    
    # Find MX device
    mx_device = None
    for device in devices:
        if device.get('model', '').startswith('MX'):
            mx_device = device
            break
    
    if not mx_device:
        print("❌ No MX device found for IAN 01")
        return
    
    print(f"\n📊 IAN 01 Device Details:")
    print(f"   Model: {mx_device.get('model')}")
    print(f"   Serial: {mx_device.get('serial')}")
    print(f"   Name: {mx_device.get('name')}")
    
    notes = mx_device.get('notes', '')
    print(f"\n📝 Current Notes:")
    print("=" * 40)
    print(notes)
    print("=" * 40)
    
    # Show raw representation
    print(f"\n🔍 Raw Notes (repr):")
    print(repr(notes))
    
    # Check for literal \n
    if '\\n' in notes:
        print("\n⚠️  Notes contain literal \\n characters!")
        print("Fixing...")
        
        fixed_notes = notes.replace('\\n', '\n')
        
        # Update device
        update_data = {"notes": fixed_notes}
        response = requests.put(
            f"{BASE_URL}/devices/{mx_device['serial']}",
            headers=headers,
            json=update_data
        )
        
        if response.status_code == 200:
            print("✅ Fixed IAN 01 notes!")
            print("\n📝 New Notes:")
            print("=" * 40)
            print(fixed_notes)
            print("=" * 40)
        else:
            print(f"❌ Error updating: {response.status_code} - {response.text}")
    else:
        print("\n✅ Notes already have proper newlines")

if __name__ == "__main__":
    main()