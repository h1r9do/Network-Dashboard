#!/usr/bin/env python3
"""
Compare current Meraki notes vs expected original notes for all 654 sites
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
        print(f"Exception getting device {device_serial}: {e}")
        return None

def check_notes_format(notes):
    """Check if notes are in new multi-line format"""
    if not notes:
        return "empty"
    
    lines = notes.split('\n')
    # Check for new format pattern
    if len(lines) >= 3:
        if lines[0] == "WAN 1" and len(lines) >= 3:
            # This is the new format
            return "new_format"
        elif lines[0] == "WAN 2" and len(lines) >= 3:
            # This is also new format (WAN 2 only)
            return "new_format"
    
    # Check for old DSR format patterns
    if "DSR" in notes or "First IP" in notes or "Gateway" in notes or "Subnet" in notes:
        return "old_format"
    
    return "unknown"

def compare_notes(current_notes, original_notes):
    """Compare current and original notes"""
    if current_notes == original_notes:
        return "exact_match"
    elif not current_notes and not original_notes:
        return "both_empty"
    elif not current_notes:
        return "current_empty"
    elif not original_notes:
        return "original_empty"
    else:
        current_format = check_notes_format(current_notes)
        original_format = check_notes_format(original_notes)
        
        if current_format == "new_format" and original_format == "old_format":
            return "not_reverted"
        elif current_format == "old_format" and original_format == "old_format":
            if current_notes.strip() == original_notes.strip():
                return "match_after_trim"
            else:
                return "old_format_mismatch"
        else:
            return "different"

def main():
    print("=== Comparing Current Notes vs Original Notes for 654 Sites ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load data
    sites_to_check = load_sites_to_check()
    original_notes = load_original_notes()
    
    print(f"Sites to check: {len(sites_to_check)}")
    print(f"Original notes loaded: {len(original_notes)}\n")
    
    # Statistics
    stats = {
        'total': len(sites_to_check),
        'checked': 0,
        'exact_match': 0,
        'match_after_trim': 0,
        'not_reverted': 0,
        'old_format_mismatch': 0,
        'current_empty': 0,
        'original_empty': 0,
        'both_empty': 0,
        'different': 0,
        'api_error': 0,
        'not_in_original': 0
    }
    
    # Lists to track issues
    not_reverted_sites = []
    mismatch_sites = []
    api_error_sites = []
    
    # Process each site
    for i, site_name in enumerate(sites_to_check, 1):
        if i % 50 == 0:
            print(f"\n=== Progress: {i}/{len(sites_to_check)} ({i/len(sites_to_check)*100:.1f}%) ===")
        
        # Get original notes
        if site_name not in original_notes:
            print(f"[{i}] {site_name}: Not found in original JSON")
            stats['not_in_original'] += 1
            continue
        
        device_serial = original_notes[site_name]['device_serial']
        original_raw_notes = original_notes[site_name]['raw_notes']
        
        # Get current notes
        current_notes = get_current_device_notes(device_serial)
        
        if current_notes is None:
            print(f"[{i}] {site_name}: API error")
            stats['api_error'] += 1
            api_error_sites.append(site_name)
            continue
        
        # Compare notes
        comparison = compare_notes(current_notes, original_raw_notes)
        stats[comparison] += 1
        stats['checked'] += 1
        
        # Report issues
        if comparison == "not_reverted":
            print(f"[{i}] {site_name}: ❌ NOT REVERTED - Still has new format")
            not_reverted_sites.append({
                'site': site_name,
                'current': current_notes[:100] + "..." if len(current_notes) > 100 else current_notes,
                'original': original_raw_notes[:100] + "..." if len(original_raw_notes) > 100 else original_raw_notes
            })
        elif comparison == "old_format_mismatch":
            print(f"[{i}] {site_name}: ⚠️  Mismatch - Both old format but different")
            mismatch_sites.append({
                'site': site_name,
                'current': current_notes[:100] + "..." if len(current_notes) > 100 else current_notes,
                'original': original_raw_notes[:100] + "..." if len(original_raw_notes) > 100 else original_raw_notes
            })
        elif comparison in ["exact_match", "match_after_trim"]:
            # Success - no need to print for every site
            pass
        else:
            print(f"[{i}] {site_name}: {comparison}")
        
        # Rate limiting
        time.sleep(0.2)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY REPORT")
    print("="*60)
    print(f"Total sites to check: {stats['total']}")
    print(f"Successfully checked: {stats['checked']}")
    print(f"API errors: {stats['api_error']}")
    print(f"Not in original JSON: {stats['not_in_original']}")
    print()
    print("REVERT STATUS:")
    print(f"✅ Successfully reverted (exact match): {stats['exact_match']}")
    print(f"✅ Successfully reverted (match after trim): {stats['match_after_trim']}")
    print(f"❌ NOT REVERTED (still new format): {stats['not_reverted']}")
    print(f"⚠️  Old format but mismatch: {stats['old_format_mismatch']}")
    print(f"📝 Current empty: {stats['current_empty']}")
    print(f"📝 Original empty: {stats['original_empty']}")
    print(f"📝 Both empty: {stats['both_empty']}")
    print(f"📝 Different (other): {stats['different']}")
    
    # List problem sites
    if not_reverted_sites:
        print("\n" + "="*60)
        print(f"SITES NOT REVERTED ({len(not_reverted_sites)} sites):")
        print("="*60)
        for site in not_reverted_sites[:10]:  # Show first 10
            print(f"\n{site['site']}:")
            print(f"  Current (new format): {site['current']}")
            print(f"  Should be: {site['original']}")
        if len(not_reverted_sites) > 10:
            print(f"\n... and {len(not_reverted_sites) - 10} more sites not reverted")
    
    if mismatch_sites:
        print("\n" + "="*60)
        print(f"SITES WITH MISMATCHED NOTES ({len(mismatch_sites)} sites):")
        print("="*60)
        for site in mismatch_sites[:5]:  # Show first 5
            print(f"\n{site['site']}:")
            print(f"  Current: {site['current']}")
            print(f"  Should be: {site['original']}")
        if len(mismatch_sites) > 5:
            print(f"\n... and {len(mismatch_sites) - 5} more sites with mismatches")
    
    # Save detailed results
    results = {
        'timestamp': datetime.now().isoformat(),
        'summary': stats,
        'not_reverted': not_reverted_sites,
        'mismatches': mismatch_sites,
        'api_errors': api_error_sites
    }
    
    with open('/tmp/revert_comparison_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: /tmp/revert_comparison_results.json")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()