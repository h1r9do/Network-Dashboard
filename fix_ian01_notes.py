#!/usr/bin/env python3
"""
Fix IAN 01 device notes specifically
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

def main():
    """Fix IAN 01 notes"""
    print("🔧 Fixing IAN 01 Device Notes")
    print("=" * 60)
    
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    # IAN 01 device info from user
    device_serial = "Q2QN-DH5E-S5PR"
    network_name = "IAN 01"
    
    print(f"📊 Device: {network_name}")
    print(f"   Serial: {device_serial}")
    
    # First, let's check what's in our live data for IAN 01
    live_data_file = "/tmp/live_meraki_all_except_55.json"
    ian01_data = None
    
    if os.path.exists(live_data_file):
        with open(live_data_file, 'r') as f:
            live_data = json.load(f)
        
        # Find IAN 01
        for site in live_data:
            if site['network_name'] == 'IAN 01':
                ian01_data = site
                break
    
    if ian01_data:
        print("\n📊 Live data found for IAN 01:")
        wan1 = ian01_data['wan1']
        wan2 = ian01_data['wan2']
        
        # Determine providers
        wan1_provider = ""
        wan1_speed = ""
        wan2_provider = ""
        wan2_speed = ""
        
        # WAN1
        if wan1.get('dsr_match'):
            wan1_provider = wan1['dsr_match']['provider']
            wan1_speed = wan1['dsr_match']['speed']
        elif wan1.get('arin_provider') and wan1['arin_provider'] not in ['Unknown', 'Private IP']:
            wan1_provider = wan1['arin_provider']
            # For ARIN, we don't have speed
        
        # WAN2
        if wan2.get('dsr_match'):
            wan2_provider = wan2['dsr_match']['provider']
            wan2_speed = wan2['dsr_match']['speed']
        elif wan2.get('arin_provider') and wan2['arin_provider'] not in ['Unknown', 'Private IP']:
            wan2_provider = wan2['arin_provider']
            # For ARIN, we don't have speed
        
        print(f"   WAN1: {wan1_provider} {wan1_speed}")
        print(f"   WAN2: {wan2_provider} {wan2_speed}")
    else:
        print("\n⚠️  No live data found, using parsed notes")
        # Based on the raw notes provided
        wan1_provider = "Mediacom"
        wan1_speed = "300.0M x 20.0M"
        wan2_provider = "Cedar Falls"
        wan2_speed = "1.0G x 1.0G"
    
    # Format new notes with actual newlines
    new_notes = f"WAN 1\n{wan1_provider}"
    if wan1_speed:
        new_notes += f"\n{wan1_speed}"
    new_notes += f"\nWAN 2\n{wan2_provider}"
    if wan2_speed:
        new_notes += f"\n{wan2_speed}"
    
    print("\n📝 New notes to apply:")
    print("=" * 40)
    print(new_notes)
    print("=" * 40)
    
    # Update device
    update_data = {"notes": new_notes}
    response = requests.put(
        f"{BASE_URL}/devices/{device_serial}",
        headers=headers,
        json=update_data
    )
    
    if response.status_code == 200:
        print("\n✅ Successfully updated IAN 01 notes!")
    else:
        print(f"\n❌ Error updating: {response.status_code}")
        print(f"   Response: {response.text}")
    
    # Also run the general fix for any other devices
    print("\n🔧 Checking for other devices with literal \\n...")
    
    # Get all devices
    response = requests.get(f"{BASE_URL}/organizations/436883/devices", headers=headers)
    all_devices = response.json()
    
    # Find and fix devices with literal \n
    devices_fixed = 0
    for device in all_devices:
        if device.get('notes') and '\\n' in device['notes']:
            fixed_notes = device['notes'].replace('\\n', '\n')
            
            update_data = {"notes": fixed_notes}
            response = requests.put(
                f"{BASE_URL}/devices/{device['serial']}",
                headers=headers,
                json=update_data
            )
            
            if response.status_code == 200:
                devices_fixed += 1
                print(f"   ✅ Fixed: {device.get('name', 'Unknown')}")
    
    if devices_fixed > 0:
        print(f"\n✅ Fixed {devices_fixed} additional devices!")
    else:
        print("\n✅ No other devices needed fixing!")

if __name__ == "__main__":
    main()