#!/usr/bin/env python3
"""
Fix device notes to use actual newlines instead of \n characters
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
    """Fix notes with actual newlines"""
    print("🔧 Fixing Device Notes Newlines")
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
    
    # Filter MX devices with notes
    mx_devices = [d for d in all_devices if d.get('model', '').startswith('MX') and d.get('notes')]
    print(f"✅ Found {len(mx_devices)} MX devices with notes")
    
    # Fix each device
    fixed_count = 0
    
    for device in mx_devices:
        serial = device['serial']
        network_name = device.get('name', 'Unknown')
        current_notes = device['notes']
        
        # Check if notes contain literal \n
        if '\\n' in current_notes:
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
                    print(f"   ✅ {network_name}: Fixed newlines")
                    fixed_count += 1
                else:
                    print(f"   ❌ {network_name}: Error {response.status_code}")
                
            except Exception as e:
                print(f"   ❌ {network_name}: Exception - {str(e)}")
    
    print(f"\n📋 SUMMARY:")
    print(f"   Devices fixed: {fixed_count}")
    print(f"\n✅ Newline fix completed!")

if __name__ == "__main__":
    main()