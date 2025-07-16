#!/usr/bin/env python3
"""
Revert the 654 sites back to their original notes from mx_inventory_live.json
"""
import os
import sys
import json
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
SITES_TO_REVERT_FILE = "/tmp/sites_to_revert.txt"
ORIGINAL_JSON_FILE = "/var/www/html/meraki-data.bak/mx_inventory_live.json"

def load_sites_to_revert():
    """Load the 654 sites that need to be reverted"""
    with open(SITES_TO_REVERT_FILE, 'r') as f:
        sites = [line.strip() for line in f.readlines()]
    return sites

def load_original_notes():
    """Load original notes from mx_inventory_live.json"""
    print("Loading original notes from mx_inventory_live.json...")
    
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
    
    print(f"✅ Loaded original notes for {len(original_notes)} devices")
    return original_notes

def update_device_notes(device_serial, notes):
    """Update device notes via Meraki API"""
    url = f"{BASE_URL}/devices/{device_serial}"
    headers = {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }
    
    data = {"notes": notes}
    
    try:
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            return True
        else:
            print(f"❌ Error updating device {device_serial}: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Exception updating device {device_serial}: {e}")
        return False

def main():
    print("=== Reverting 654 Sites to Original Notes ===")
    start_time = time.time()
    
    # Load the sites that need to be reverted
    sites_to_revert = load_sites_to_revert()
    print(f"Sites to revert: {len(sites_to_revert)}")
    
    # Load original notes from JSON
    original_notes = load_original_notes()
    
    # Process each site
    success_count = 0
    error_count = 0
    not_found_count = 0
    
    print(f"\n=== Reverting {len(sites_to_revert)} sites ===")
    
    for i, site_name in enumerate(sites_to_revert, 1):
        print(f"[{i}/{len(sites_to_revert)}] Reverting {site_name}")
        
        if site_name in original_notes:
            device_serial = original_notes[site_name]['device_serial']
            original_raw_notes = original_notes[site_name]['raw_notes']
            
            print(f"  Device: {device_serial}")
            print(f"  Original notes preview: {original_raw_notes[:100]}...")
            
            if update_device_notes(device_serial, original_raw_notes):
                print(f"  ✅ Successfully reverted {site_name}")
                success_count += 1
            else:
                print(f"  ❌ Failed to revert {site_name}")
                error_count += 1
        else:
            print(f"  ⚠️  {site_name} not found in original JSON")
            not_found_count += 1
        
        # Rate limiting
        time.sleep(0.3)
        
        # Progress update every 50 sites
        if i % 50 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed * 60  # sites per minute
            remaining = len(sites_to_revert) - i
            eta_minutes = remaining / (rate / 60) if rate > 0 else 0
            print(f"\n📊 Progress: {i}/{len(sites_to_revert)} ({i/len(sites_to_revert)*100:.1f}%)")
            print(f"   Rate: {rate:.1f} sites/min, ETA: {eta_minutes:.1f} minutes\n")
    
    # Summary
    elapsed = time.time() - start_time
    print(f"\n=== Revert Summary ===")
    print(f"Total sites to revert: {len(sites_to_revert)}")
    print(f"Successfully reverted: {success_count}")
    print(f"Failed to revert: {error_count}")
    print(f"Not found in original JSON: {not_found_count}")
    print(f"Total time: {elapsed/60:.1f} minutes")
    print(f"Average rate: {len(sites_to_revert)/(elapsed/60):.1f} sites/min")
    print(f"✅ Revert operation complete!")

if __name__ == "__main__":
    main()