#!/usr/bin/env python3
"""
Verify all device notes are properly formatted
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
    """Verify all notes"""
    print("🔍 Verifying All Device Notes")
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
    
    # Statistics
    total_devices = 0
    devices_with_notes = 0
    devices_with_wan_notes = 0
    devices_with_proper_newlines = 0
    devices_with_literal_n = 0
    devices_with_no_newlines = 0
    problem_devices = []
    
    for device in all_devices:
        total_devices += 1
        notes = device.get('notes', '')
        
        if notes:
            devices_with_notes += 1
            
            if 'WAN' in notes:
                devices_with_wan_notes += 1
                
                # Check format
                if '\\n' in notes:
                    devices_with_literal_n += 1
                    problem_devices.append({
                        'name': device.get('name', 'Unknown'),
                        'issue': 'Has literal \\n',
                        'notes': notes[:50] + '...'
                    })
                elif '\n' in notes:
                    devices_with_proper_newlines += 1
                else:
                    # WAN notes without newlines might be a problem
                    if 'WAN 1' in notes and 'WAN 2' in notes:
                        devices_with_no_newlines += 1
                        problem_devices.append({
                            'name': device.get('name', 'Unknown'),
                            'issue': 'No newlines found',
                            'notes': notes[:50] + '...'
                        })
    
    # Report
    print(f"\n📊 DEVICE STATISTICS:")
    print(f"   Total devices: {total_devices}")
    print(f"   Devices with notes: {devices_with_notes}")
    print(f"   Devices with WAN notes: {devices_with_wan_notes}")
    print(f"   Properly formatted: {devices_with_proper_newlines}")
    print(f"   With literal \\n: {devices_with_literal_n}")
    print(f"   Missing newlines: {devices_with_no_newlines}")
    
    if problem_devices:
        print(f"\n❌ PROBLEM DEVICES ({len(problem_devices)}):")
        for device in problem_devices[:10]:
            print(f"   - {device['name']}: {device['issue']}")
            print(f"     Notes: {device['notes']}")
        if len(problem_devices) > 10:
            print(f"   ... and {len(problem_devices) - 10} more")
    else:
        print("\n✅ ALL NOTES ARE PROPERLY FORMATTED!")
    
    # Sample some properly formatted ones
    print(f"\n📝 Sample of properly formatted notes:")
    sample_count = 0
    for device in all_devices:
        if sample_count >= 3:
            break
        notes = device.get('notes', '')
        if notes and 'WAN' in notes and '\n' in notes and '\\n' not in notes:
            print(f"\n   {device.get('name', 'Unknown')}:")
            for line in notes.split('\n')[:6]:  # Show first 6 lines
                print(f"   {line}")
            sample_count += 1

if __name__ == "__main__":
    main()