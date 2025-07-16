#!/usr/bin/env python3
"""Test ARIN lookups for 50 Discount-Tire tagged sites from mx_inventory_live.json"""

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
        print(f"Error: {json_file} not found")
        return
    
    print(f"Loading data from: {json_file}")
    with open(json_file, 'r') as f:
        inventory = json.load(f)
    
    # Filter for sites with "Discount-Tire" tag
    discount_tire_sites = []
    for site in inventory:
        device_tags = site.get('device_tags', [])
        if 'Discount-Tire' in device_tags:
            # Also check if it has public IPs
            wan1_ip = site.get('wan1', {}).get('ip', '')
            wan2_ip = site.get('wan2', {}).get('ip', '')
            
            has_public_ip = False
            if wan1_ip and not any(wan1_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
                has_public_ip = True
            if wan2_ip and not any(wan2_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
                has_public_ip = True
                
            if has_public_ip:
                discount_tire_sites.append(site)
    
    print(f"Found {len(discount_tire_sites)} Discount-Tire sites with public IPs")
    print("Testing first 50 sites...")
    print("="*120)
    
    # Test first 50 sites
    cache = {}
    missing_set = set()
    results = []
    
    for i, site in enumerate(discount_tire_sites[:50]):
        network_name = site.get('network_name', 'Unknown')
        wan1_ip = site.get('wan1', {}).get('ip', '')
        wan2_ip = site.get('wan2', {}).get('ip', '')
        
        # Get existing provider data from JSON
        wan1_provider_json = site.get('wan1', {}).get('provider', 'N/A')
        wan2_provider_json = site.get('wan2', {}).get('provider', 'N/A')
        
        # Test with our fixed parser
        wan1_provider_new = 'N/A'
        wan2_provider_new = 'N/A'
        
        if wan1_ip and not any(wan1_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
            wan1_provider_new = get_provider_for_ip(wan1_ip, cache, missing_set)
            
        if wan2_ip and not any(wan2_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
            wan2_provider_new = get_provider_for_ip(wan2_ip, cache, missing_set)
        
        # Compare results
        wan1_match = wan1_provider_json == wan1_provider_new if wan1_ip else True
        wan2_match = wan2_provider_json == wan2_provider_new if wan2_ip else True
        
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
        print(f"\n{i+1}. {network_name}")
        
        if wan1_ip and not any(wan1_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
            print(f"   WAN1: {wan1_ip}")
            print(f"     JSON:   {wan1_provider_json}")
            print(f"     NEW:    {wan1_provider_new}")
            print(f"     Match:  {'✓' if wan1_match else '✗'}")
        
        if wan2_ip and not any(wan2_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
            print(f"   WAN2: {wan2_ip}")
            print(f"     JSON:   {wan2_provider_json}")
            print(f"     NEW:    {wan2_provider_new}")
            print(f"     Match:  {'✓' if wan2_match else '✗'}")
        
        # Rate limit to avoid overwhelming ARIN API
        if (i + 1) % 10 == 0:
            time.sleep(1)
    
    # Summary
    total_tests = 0
    total_matches = 0
    
    for r in results:
        if r['wan1_ip'] and not any(r['wan1_ip'].startswith(prefix) for prefix in ['192.168', '10.', '172.']):
            total_tests += 1
            if r['wan1_match']:
                total_matches += 1
        if r['wan2_ip'] and not any(r['wan2_ip'].startswith(prefix) for prefix in ['192.168', '10.', '172.']):
            total_tests += 1
            if r['wan2_match']:
                total_matches += 1
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Sites tested: {len(results)}")
    print(f"Total IP lookups: {total_tests}")
    print(f"Matching providers: {total_matches}")
    if total_tests > 0:
        print(f"Match rate: {(total_matches/total_tests*100):.1f}%")
    
    # Show mismatches
    mismatches = []
    for r in results:
        if not r['wan1_match'] and r['wan1_ip'] and not any(r['wan1_ip'].startswith(prefix) for prefix in ['192.168', '10.', '172.']):
            mismatches.append(f"{r['network']} WAN1: JSON='{r['wan1_json']}' vs NEW='{r['wan1_new']}'")
        if not r['wan2_match'] and r['wan2_ip'] and not any(r['wan2_ip'].startswith(prefix) for prefix in ['192.168', '10.', '172.']):
            mismatches.append(f"{r['network']} WAN2: JSON='{r['wan2_json']}' vs NEW='{r['wan2_new']}'")
    
    if mismatches:
        print(f"\nMismatches ({len(mismatches)}):")
        for m in mismatches[:20]:  # Show first 20
            print(f"  - {m}")
        if len(mismatches) > 20:
            print(f"  ... and {len(mismatches) - 20} more")

if __name__ == "__main__":
    main()