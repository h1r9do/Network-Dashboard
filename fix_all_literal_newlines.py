#!/usr/bin/env python3
"""
Fix ALL devices with literal \n in notes
"""

import os
import json
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ORG_NAME = "DTC-Store-Inventory-All"

def main():
    """Fix all literal newlines"""
    print("🔧 Fixing ALL Devices with Literal \\n")
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
    
    print(f"✅ Organization: {org_id}")
    
    # Get all devices
    print("🔄 Getting all devices...")
    response = requests.get(f"{BASE_URL}/organizations/{org_id}/devices", headers=headers)
    all_devices = response.json()
    
    # Find devices with literal \n
    devices_to_fix = []
    for device in all_devices:
        if device.get('notes') and '\\n' in device['notes']:
            devices_to_fix.append(device)
    
    print(f"📊 Found {len(devices_to_fix)} devices with literal \\n")
    
    if not devices_to_fix:
        print("✅ No devices need fixing!")
        return
    
    # Show some examples
    print("\n📝 Examples of devices to fix:")
    for device in devices_to_fix[:5]:
        name = device.get('name', 'Unknown')
        notes_preview = device['notes'][:50].replace('\\n', '↵')
        print(f"   - {name}: {notes_preview}...")
    
    if len(devices_to_fix) > 5:
        print(f"   ... and {len(devices_to_fix) - 5} more")
    
    # Fix all devices
    print(f"\n🔧 Fixing {len(devices_to_fix)} devices...")
    fixed_count = 0
    error_count = 0
    
    for i, device in enumerate(devices_to_fix):
        serial = device['serial']
        name = device.get('name', 'Unknown')
        current_notes = device['notes']
        
        # Replace literal \n with actual newlines
        fixed_notes = current_notes.replace('\\n', '\n')
        
        # Update device
        try:
            update_data = {"notes": fixed_notes}
            response = requests.put(
                f"{BASE_URL}/devices/{serial}",
                headers=headers,
                json=update_data
            )
            
            if response.status_code == 200:
                fixed_count += 1
                if fixed_count % 10 == 0:
                    print(f"   ✅ Progress: {fixed_count}/{len(devices_to_fix)} fixed...")
            else:
                error_count += 1
                print(f"   ❌ Error fixing {name}: {response.status_code}")
            
            # Rate limiting
            time.sleep(0.2)
            
        except Exception as e:
            error_count += 1
            print(f"   ❌ Exception fixing {name}: {str(e)}")
    
    print(f"\n📋 SUMMARY:")
    print(f"   Devices fixed: {fixed_count}")
    print(f"   Errors: {error_count}")
    print(f"\n✅ Newline fix completed!")

if __name__ == "__main__":
    main()