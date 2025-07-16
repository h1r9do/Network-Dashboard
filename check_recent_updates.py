#!/usr/bin/env python3
"""
Check recently updated devices for notes with \n
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
    """Check recent devices for literal newlines"""
    print("🔍 Checking Recently Updated Devices for \\n")
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
    
    # Get all devices
    print("🔄 Getting all devices...")
    response = requests.get(f"{BASE_URL}/organizations/{org_id}/devices", headers=headers)
    all_devices = response.json()
    
    # Filter MX devices with notes containing WAN
    devices_with_notes = []
    for device in all_devices:
        if device.get('model', '').startswith('MX') and device.get('notes'):
            notes = device['notes']
            if 'WAN' in notes:
                devices_with_notes.append(device)
    
    print(f"✅ Found {len(devices_with_notes)} MX devices with WAN notes")
    
    # Check first 10 for literal \n
    print("\n📊 Checking for literal \\n in notes:")
    devices_needing_fix = []
    
    for i, device in enumerate(devices_with_notes[:20]):
        name = device.get('name', 'Unknown')
        notes = device['notes']
        
        if '\\n' in notes:
            devices_needing_fix.append(device)
            print(f"   ❌ {name}: Has literal \\n")
            print(f"      Raw: {repr(notes[:50])}...")
        elif '\n' in notes:
            print(f"   ✅ {name}: Has proper newlines")
        else:
            print(f"   ⚠️  {name}: No newlines found")
    
    if devices_needing_fix:
        print(f"\n🔧 Fixing {len(devices_needing_fix)} devices...")
        
        for device in devices_needing_fix[:5]:  # Fix first 5 as example
            serial = device['serial']
            name = device.get('name', 'Unknown')
            current_notes = device['notes']
            
            # Fix the notes
            fixed_notes = current_notes.replace('\\n', '\n')
            
            # Update device
            update_data = {"notes": fixed_notes}
            response = requests.put(
                f"{BASE_URL}/devices/{serial}",
                headers=headers,
                json=update_data
            )
            
            if response.status_code == 200:
                print(f"   ✅ Fixed: {name}")
            else:
                print(f"   ❌ Error fixing {name}: {response.status_code}")

if __name__ == "__main__":
    main()