#!/usr/bin/env python3
"""
Search all device notes for literal \n
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
    """Search all notes"""
    print("🔍 Searching All Device Notes for Literal \\n")
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
    
    # Check all devices
    devices_with_literal_n = []
    
    for device in all_devices:
        if device.get('notes'):
            notes = device['notes']
            if '\\n' in notes:
                devices_with_literal_n.append({
                    'name': device.get('name', 'Unknown'),
                    'serial': device['serial'],
                    'model': device.get('model', ''),
                    'notes': notes
                })
    
    print(f"\n📊 Found {len(devices_with_literal_n)} devices with literal \\n")
    
    if devices_with_literal_n:
        print("\n❌ Devices needing fixes:")
        for device in devices_with_literal_n[:10]:
            print(f"   - {device['name']} ({device['model']})")
            print(f"     Notes preview: {repr(device['notes'][:60])}...")
        
        if len(devices_with_literal_n) > 10:
            print(f"   ... and {len(devices_with_literal_n) - 10} more")
        
        # Fix all devices
        fix = input("\n🔧 Fix all devices? (y/n): ")
        if fix.lower() == 'y':
            fixed_count = 0
            for device in devices_with_literal_n:
                fixed_notes = device['notes'].replace('\\n', '\n')
                
                update_data = {"notes": fixed_notes}
                response = requests.put(
                    f"{BASE_URL}/devices/{device['serial']}",
                    headers=headers,
                    json=update_data
                )
                
                if response.status_code == 200:
                    fixed_count += 1
                    if fixed_count % 10 == 0:
                        print(f"   ✅ Fixed {fixed_count} devices...")
            
            print(f"\n✅ Fixed {fixed_count} devices total!")
    else:
        print("\n✅ No devices found with literal \\n - all notes are properly formatted!")

if __name__ == "__main__":
    main()