#!/usr/bin/env python3
"""
Quick sample check of a few sites
"""
import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
ORIGINAL_JSON_FILE = "/var/www/html/meraki-data.bak/mx_inventory_live.json"

# Sample sites to check
SAMPLE_SITES = ["ALB 01", "AZC 01", "AZP 09", "CAL 01", "COD 02"]

def load_original_notes():
    """Load original notes from mx_inventory_live.json"""
    with open(ORIGINAL_JSON_FILE, 'r') as f:
        inventory_data = json.load(f)
    
    original_notes = {}
    for device in inventory_data:
        network_name = device.get('network_name', '')
        device_serial = device.get('device_serial', '')
        raw_notes = device.get('raw_notes', '')
        
        if network_name and device_serial:
            original_notes[network_name] = {
                'device_serial': device_serial,
                'raw_notes': raw_notes
            }
    
    return original_notes

def get_current_device_notes(device_serial):
    """Get current device notes from Meraki API"""
    url = f"{BASE_URL}/devices/{device_serial}"
    headers = {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            device_data = response.json()
            return device_data.get('notes', '')
        else:
            return None
    except Exception as e:
        return None

def main():
    print("=== Quick Sample Check of Notes ===\n")
    
    # Load original notes
    original_notes = load_original_notes()
    
    for site_name in SAMPLE_SITES:
        print(f"\n{'='*60}")
        print(f"SITE: {site_name}")
        print('='*60)
        
        if site_name not in original_notes:
            print("Not found in original JSON")
            continue
        
        device_serial = original_notes[site_name]['device_serial']
        original_raw_notes = original_notes[site_name]['raw_notes']
        
        # Get current notes
        current_notes = get_current_device_notes(device_serial)
        
        if current_notes is None:
            print("API error getting current notes")
            continue
        
        print(f"\nCURRENT NOTES:")
        print("-" * 40)
        current_lines = current_notes.split('\n')
        for line in current_lines[:10]:  # Show first 10 lines
            print(f"  {line}")
        if len(current_lines) > 10:
            print(f"  ... ({len(current_lines)} total lines)")
        
        print(f"\nORIGINAL NOTES (Expected):")
        print("-" * 40)
        original_lines = original_raw_notes.split('\n')
        for line in original_lines[:10]:  # Show first 10 lines
            print(f"  {line}")
        if len(original_lines) > 10:
            print(f"  ... ({len(original_lines)} total lines)")
        
        # Check if they match
        if current_notes == original_raw_notes:
            print(f"\n✅ EXACT MATCH - Successfully reverted!")
        elif current_notes.strip() == original_raw_notes.strip():
            print(f"\n✅ MATCH (after trimming) - Successfully reverted!")
        else:
            # Check formats
            if len(current_lines) >= 3 and current_lines[0] in ["WAN 1", "WAN 2"]:
                print(f"\n❌ NOT REVERTED - Still has new format!")
            else:
                print(f"\n⚠️  MISMATCH - Different content but both old format")

if __name__ == "__main__":
    main()