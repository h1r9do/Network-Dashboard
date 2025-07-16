#!/usr/bin/env python3
"""Test ARIN lookups for first 50 sites with Discount-Tire tag"""

import json
import os
import sys
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_provider_for_ip
import time

def main():
    # Load the mx_inventory_live.json file
    json_file = '/var/www/html/meraki-data/mx_inventory_live.json'
    
    if not os.path.exists(json_file):
        # Try the backup locations
        backup_files = [
            '/usr/local/bin/backups/migration_20250624_171253/www_html/meraki-data/mx_inventory_live.json',
            '/usr/local/bin/Main/mx_inventory_live.json'
        ]
        for backup in backup_files:
            if os.path.exists(backup):
                json_file = backup
                break
        else:
            print(f"Error: mx_inventory_live.json not found in any location")
            return
    
    print(f"Loading data from: {json_file}")
    with open(json_file, 'r') as f:
        inventory = json.load(f)
    
    # Filter for sites with "Discount-Tire" tag
    discount_tire_sites = []
    for site in inventory:
        tags = site.get('tags', [])
        if 'Discount-Tire' in tags:
            discount_tire_sites.append(site)
    
    print(f"Found {len(discount_tire_sites)} sites with Discount-Tire tag")
    print("Testing first 50 sites...\n")
    
    # Test first 50 sites
    cache = {}
    missing_set = set()
    results = []
    
    for i, site in enumerate(discount_tire_sites[:50]):
        network_name = site.get('network_name', 'Unknown')
        wan1_ip = site.get('wan1_ip', 'N/A')
        wan2_ip = site.get('wan2_ip', 'N/A')
        
        # Get existing provider data from JSON
        wan1_provider_json = site.get('wan1_arin_provider', 'N/A')
        wan2_provider_json = site.get('wan2_arin_provider', 'N/A')
        
        # Test with our fixed parser
        wan1_provider_new = 'N/A'
        wan2_provider_new = 'N/A'
        
        if wan1_ip and wan1_ip != 'N/A':
            wan1_provider_new = get_provider_for_ip(wan1_ip, cache, missing_set)
            
        if wan2_ip and wan2_ip != 'N/A':
            wan2_provider_new = get_provider_for_ip(wan2_ip, cache, missing_set)
        
        # Compare results
        wan1_match = wan1_provider_json == wan1_provider_new
        wan2_match = wan2_provider_json == wan2_provider_new
        
        result = {
            'network': network_name,
            'wan1_ip': wan1_ip,
            'wan1_json': wan1_provider_json,
            'wan1_new': wan1_provider_new,
            'wan1_match': wan1_match,
            'wan2_ip': wan2_ip,
            'wan2_json': wan2_provider_json,
            'wan2_new': wan2_provider_new,
            'wan2_match': wan2_match
        }
        results.append(result)
        
        # Print progress
        print(f"{i+1}. {network_name}")
        print(f"   WAN1: {wan1_ip}")
        print(f"     JSON: {wan1_provider_json}")
        print(f"     NEW:  {wan1_provider_new}")
        print(f"     Match: {'✓' if wan1_match else '✗'}")
        
        if wan2_ip != 'N/A':
            print(f"   WAN2: {wan2_ip}")
            print(f"     JSON: {wan2_provider_json}")
            print(f"     NEW:  {wan2_provider_new}")
            print(f"     Match: {'✓' if wan2_match else '✗'}")
        print()
        
        # Rate limit to avoid overwhelming ARIN API
        if (i + 1) % 10 == 0:
            time.sleep(1)
    
    # Summary
    total_tests = sum(1 for r in results for field in ['wan1_match', 'wan2_match'] 
                     if r[field.replace('_match', '_ip')] != 'N/A')
    total_matches = sum(1 for r in results for field in ['wan1_match', 'wan2_match'] 
                       if r[field] and r[field.replace('_match', '_ip')] != 'N/A')
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Sites tested: {len(results)}")
    print(f"Total IP lookups: {total_tests}")
    print(f"Matching providers: {total_matches}")
    print(f"Match rate: {(total_matches/total_tests*100):.1f}%")
    
    # Show mismatches
    mismatches = []
    for r in results:
        if not r['wan1_match'] and r['wan1_ip'] != 'N/A':
            mismatches.append(f"{r['network']} WAN1: JSON='{r['wan1_json']}' vs NEW='{r['wan1_new']}'")
        if not r['wan2_match'] and r['wan2_ip'] != 'N/A':
            mismatches.append(f"{r['network']} WAN2: JSON='{r['wan2_json']}' vs NEW='{r['wan2_new']}'")
    
    if mismatches:
        print(f"\nMismatches ({len(mismatches)}):")
        for m in mismatches[:10]:  # Show first 10
            print(f"  - {m}")
        if len(mismatches) > 10:
            print(f"  ... and {len(mismatches) - 10} more")

if __name__ == "__main__":
    main()