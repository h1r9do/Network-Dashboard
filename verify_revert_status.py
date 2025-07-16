#!/usr/bin/env python3
"""
Verify revert status by checking a representative sample of sites
"""
import os
import sys
import json
import requests
import time
import random
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
    print("=== Verify Revert Status - Sample Check ===\n")
    
    # Load data
    all_sites = load_sites_to_check()
    original_notes = load_original_notes()
    
    # Create a representative sample (10% or 65 sites)
    sample_size = min(65, len(all_sites))
    sample_sites = random.sample(all_sites, sample_size)
    
    print(f"Total sites: {len(all_sites)}")
    print(f"Checking sample of: {sample_size} sites\n")
    
    # Statistics
    results = {
        'exact_match': 0,
        'not_reverted': 0,
        'mismatch': 0,
        'empty': 0,
        'api_error': 0,
        'not_found': 0
    }
    
    not_reverted_list = []
    
    # Check each sample site
    for i, site_name in enumerate(sample_sites, 1):
        print(f"[{i}/{sample_size}] Checking {site_name}...", end='')
        
        if site_name not in original_notes:
            print(" Not in original JSON")
            results['not_found'] += 1
            continue
        
        device_serial = original_notes[site_name]['device_serial']
        original_raw_notes = original_notes[site_name]['raw_notes']
        
        # Get current notes
        current_notes = get_current_device_notes(device_serial)
        
        if current_notes is None:
            print(" API error")
            results['api_error'] += 1
        elif not current_notes:
            print(" Empty notes")
            results['empty'] += 1
        elif current_notes == original_raw_notes:
            print(" ✅ Exact match")
            results['exact_match'] += 1
        else:
            current_format = check_notes_format(current_notes)
            if current_format == "new_format":
                print(" ❌ NOT REVERTED")
                results['not_reverted'] += 1
                not_reverted_list.append(site_name)
            else:
                print(" ⚠️  Mismatch")
                results['mismatch'] += 1
        
        time.sleep(0.3)  # Rate limiting
    
    # Print summary
    print("\n" + "="*50)
    print("SAMPLE RESULTS")
    print("="*50)
    print(f"Sample size: {sample_size} sites")
    print(f"✅ Exact matches: {results['exact_match']} ({results['exact_match']/sample_size*100:.1f}%)")
    print(f"❌ Not reverted: {results['not_reverted']} ({results['not_reverted']/sample_size*100:.1f}%)")
    print(f"⚠️  Mismatches: {results['mismatch']} ({results['mismatch']/sample_size*100:.1f}%)")
    print(f"📝 Empty notes: {results['empty']} ({results['empty']/sample_size*100:.1f}%)")
    print(f"🔴 API errors: {results['api_error']} ({results['api_error']/sample_size*100:.1f}%)")
    
    if not_reverted_list:
        print(f"\nSites still with new format:")
        for site in not_reverted_list:
            print(f"  - {site}")
    
    # Extrapolate to full set
    print("\n" + "="*50)
    print("ESTIMATED FULL RESULTS (based on sample)")
    print("="*50)
    total = len(all_sites)
    print(f"Total sites: {total}")
    print(f"✅ Estimated successful reverts: {int(results['exact_match']/sample_size*total)} ({results['exact_match']/sample_size*100:.1f}%)")
    print(f"❌ Estimated not reverted: {int(results['not_reverted']/sample_size*total)} ({results['not_reverted']/sample_size*100:.1f}%)")
    
    success_rate = results['exact_match'] / sample_size * 100
    if success_rate > 95:
        print(f"\n✅ REVERT OPERATION SUCCESSFUL - {success_rate:.1f}% success rate")
    elif success_rate > 80:
        print(f"\n⚠️  REVERT MOSTLY SUCCESSFUL - {success_rate:.1f}% success rate")
    else:
        print(f"\n❌ REVERT HAD ISSUES - Only {success_rate:.1f}% success rate")

if __name__ == "__main__":
    main()