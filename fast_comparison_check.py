#!/usr/bin/env python3
"""
Fast comparison check - batch API calls for efficiency
"""
import os
import sys
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
SITES_FILE = "/tmp/sites_to_revert.txt"
ORIGINAL_JSON_FILE = "/var/www/html/meraki-data.bak/mx_inventory_live.json"

def load_sites_to_check():
    """Load the 654 sites that need to be checked"""
    with open(SITES_FILE, 'r') as f:
        sites = [line.strip() for line in f.readlines() if line.strip()]
    return sites

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

def get_organization_id():
    """Get organization ID"""
    url = f"{BASE_URL}/organizations"
    headers = {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        orgs = response.json()
        if orgs:
            return orgs[0]['id']
    return None

def get_all_devices(org_id):
    """Get all devices in organization"""
    url = f"{BASE_URL}/organizations/{org_id}/devices"
    headers = {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }
    
    devices = {}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        for device in response.json():
            if device.get('serial'):
                devices[device['serial']] = device.get('notes', '')
    
    return devices

def check_notes_format(notes):
    """Check if notes are in new multi-line format"""
    if not notes:
        return "empty"
    
    lines = notes.split('\n')
    # Check for new format pattern
    if len(lines) >= 3:
        if lines[0] == "WAN 1" and len(lines) >= 3:
            return "new_format"
        elif lines[0] == "WAN 2" and len(lines) >= 3:
            return "new_format"
    
    # Check for old DSR format patterns
    if "DSR" in notes or "First IP" in notes or "Gateway" in notes or "Subnet" in notes:
        return "old_format"
    
    return "unknown"

def main():
    print("=== Fast Comparison Check for 654 Sites ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load data
    sites_to_check = load_sites_to_check()
    original_notes = load_original_notes()
    
    print(f"Sites to check: {len(sites_to_check)}")
    print(f"Original notes loaded: {len(original_notes)}")
    
    # Get all devices in one API call
    print("\nFetching all devices from Meraki...")
    org_id = get_organization_id()
    if not org_id:
        print("ERROR: Could not get organization ID")
        return
    
    all_devices = get_all_devices(org_id)
    print(f"Fetched {len(all_devices)} devices\n")
    
    # Statistics
    stats = {
        'total': len(sites_to_check),
        'exact_match': 0,
        'match_after_trim': 0,
        'not_reverted': 0,
        'old_format_mismatch': 0,
        'empty': 0,
        'different': 0,
        'not_found': 0
    }
    
    # Lists to track issues
    not_reverted_sites = []
    mismatch_sites = []
    
    # Process each site
    print("Comparing notes...")
    for site_name in sites_to_check:
        # Get original notes
        if site_name not in original_notes:
            stats['not_found'] += 1
            continue
        
        device_serial = original_notes[site_name]['device_serial']
        original_raw_notes = original_notes[site_name]['raw_notes']
        
        # Get current notes from cached data
        current_notes = all_devices.get(device_serial, '')
        
        # Compare notes
        if current_notes == original_raw_notes:
            stats['exact_match'] += 1
        elif current_notes.strip() == original_raw_notes.strip():
            stats['match_after_trim'] += 1
        elif not current_notes:
            stats['empty'] += 1
        else:
            current_format = check_notes_format(current_notes)
            original_format = check_notes_format(original_raw_notes)
            
            if current_format == "new_format":
                stats['not_reverted'] += 1
                not_reverted_sites.append({
                    'site': site_name,
                    'current_preview': current_notes[:100] + "..." if len(current_notes) > 100 else current_notes
                })
            elif current_format == "old_format" and original_format == "old_format":
                stats['old_format_mismatch'] += 1
                mismatch_sites.append({
                    'site': site_name,
                    'current_preview': current_notes[:100] + "..." if len(current_notes) > 100 else current_notes,
                    'original_preview': original_raw_notes[:100] + "..." if len(original_raw_notes) > 100 else original_raw_notes
                })
            else:
                stats['different'] += 1
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY REPORT")
    print("="*60)
    print(f"Total sites to check: {stats['total']}")
    print()
    print("REVERT STATUS:")
    print(f"✅ Successfully reverted (exact match): {stats['exact_match']}")
    print(f"✅ Successfully reverted (match after trim): {stats['match_after_trim']}")
    print(f"❌ NOT REVERTED (still new format): {stats['not_reverted']}")
    print(f"⚠️  Old format but mismatch: {stats['old_format_mismatch']}")
    print(f"📝 Empty notes: {stats['empty']}")
    print(f"📝 Different (other): {stats['different']}")
    print(f"📝 Not found in device list: {stats['not_found']}")
    
    total_success = stats['exact_match'] + stats['match_after_trim']
    print(f"\nTOTAL SUCCESSFULLY REVERTED: {total_success} of {stats['total']} ({total_success/stats['total']*100:.1f}%)")
    
    # List problem sites
    if not_reverted_sites:
        print("\n" + "="*60)
        print(f"SITES STILL WITH NEW FORMAT ({len(not_reverted_sites)} sites):")
        print("="*60)
        for site in not_reverted_sites:
            print(f"- {site['site']}: {site['current_preview']}")
    
    if mismatch_sites:
        print("\n" + "="*60)
        print(f"SITES WITH MISMATCHED NOTES ({len(mismatch_sites)} sites):")
        print("="*60)
        for i, site in enumerate(mismatch_sites[:10]):  # Show first 10
            print(f"\n{i+1}. {site['site']}:")
            print(f"   Current: {site['current_preview']}")
            print(f"   Original: {site['original_preview']}")
        if len(mismatch_sites) > 10:
            print(f"\n... and {len(mismatch_sites) - 10} more sites with mismatches")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()