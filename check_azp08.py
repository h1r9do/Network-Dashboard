#!/usr/bin/env python3
"""
Check AZP 08 device notes specifically
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
    """Check AZP 08 notes"""
    print("🔍 Checking AZP 08 Device Notes")
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
    
    # Find AZP 08
    azp08_network = None
    for network in networks:
        if network['name'] == 'AZP 08':
            azp08_network = network
            break
    
    if not azp08_network:
        print("❌ AZP 08 network not found")
        return
    
    network_id = azp08_network['id']
    print(f"✅ Found AZP 08 network: {network_id}")
    
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
        print("❌ No MX device found for AZP 08")
        return
    
    print(f"\n📊 AZP 08 Device Details:")
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
    
    # Show each character
    print(f"\n🔍 Character breakdown:")
    for i, char in enumerate(notes[:50]):
        if char == '\n':
            print(f"   Position {i}: [NEWLINE]")
        elif char == '\\':
            print(f"   Position {i}: [BACKSLASH]")
        elif char == 'n' and i > 0 and notes[i-1] == '\\':
            print(f"   Position {i}: [n after backslash]")
        else:
            print(f"   Position {i}: '{char}'")
    
    # Check what's in our live data
    live_data_file = "/tmp/live_meraki_all_except_55.json"
    if os.path.exists(live_data_file):
        with open(live_data_file, 'r') as f:
            live_data = json.load(f)
        
        # Find AZP 08
        for site in live_data:
            if site['network_name'] == 'AZP 08':
                print(f"\n📊 Live data for AZP 08:")
                print(f"   WAN1 ARIN: {site['wan1'].get('arin_provider')}")
                print(f"   WAN1 DSR: {site['wan1'].get('dsr_match')}")
                print(f"   WAN2 ARIN: {site['wan2'].get('arin_provider')}")
                print(f"   WAN2 DSR: {site['wan2'].get('dsr_match')}")
                break

if __name__ == "__main__":
    main()