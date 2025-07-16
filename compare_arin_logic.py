#!/usr/bin/env python3
"""Compare our ARIN lookup logic vs mx_inventory_live.json data"""

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
    
    print(f"Total sites in JSON: {len(inventory)}")
    
    # Filter for sites with public WAN IPs
    sites_with_public_ips = []
    for site in inventory:
        wan1_ip = site.get('wan1', {}).get('ip', '')
        wan2_ip = site.get('wan2', {}).get('ip', '')
        
        # Check if at least one WAN has a public IP
        has_public_wan1 = wan1_ip and not any(wan1_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.', 'N/A'])
        has_public_wan2 = wan2_ip and not any(wan2_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.', 'N/A'])
        
        if has_public_wan1 or has_public_wan2:
            sites_with_public_ips.append(site)
    
    print(f"Sites with public IPs: {len(sites_with_public_ips)}")
    print("\nTesting first 20 sites...")
    print("="*120)
    
    # Test first 20 sites
    cache = {}
    missing_set = set()
    results = []
    
    for i, site in enumerate(sites_with_public_ips[:20]):
        network_name = site.get('network_name', 'Unknown')
        wan1_ip = site.get('wan1', {}).get('ip', 'N/A')
        wan2_ip = site.get('wan2', {}).get('ip', 'N/A')
        
        # Get provider data from JSON
        wan1_provider_json = site.get('wan1', {}).get('provider', 'N/A')
        wan2_provider_json = site.get('wan2', {}).get('provider', 'N/A')
        
        # Test with our parser
        wan1_provider_new = 'N/A'
        wan2_provider_new = 'N/A'
        
        if wan1_ip and wan1_ip != 'N/A' and not any(wan1_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
            wan1_provider_new = get_provider_for_ip(wan1_ip, cache, missing_set)
            
        if wan2_ip and wan2_ip != 'N/A' and not any(wan2_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
            wan2_provider_new = get_provider_for_ip(wan2_ip, cache, missing_set)
        
        # Compare results
        wan1_match = wan1_provider_json == wan1_provider_new
        wan2_match = wan2_provider_json == wan2_provider_new
        
        # Print comparison
        print(f"\n{i+1}. {network_name}")
        if wan1_ip != 'N/A' and not any(wan1_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
            print(f"   WAN1: {wan1_ip}")
            print(f"     JSON:   {wan1_provider_json}")
            print(f"     NEW:    {wan1_provider_new}")
            print(f"     Match:  {'✓' if wan1_match else '✗'}")
        
        if wan2_ip != 'N/A' and not any(wan2_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
            print(f"   WAN2: {wan2_ip}")
            print(f"     JSON:   {wan2_provider_json}")
            print(f"     NEW:    {wan2_provider_new}")
            print(f"     Match:  {'✓' if wan2_match else '✗'}")
        
        results.append({
            'network': network_name,
            'wan1_match': wan1_match if wan1_ip != 'N/A' else None,
            'wan2_match': wan2_match if wan2_ip != 'N/A' else None,
            'wan1_json': wan1_provider_json,
            'wan1_new': wan1_provider_new,
            'wan2_json': wan2_provider_json,
            'wan2_new': wan2_provider_new
        })
        
        # Rate limit
        if (i + 1) % 5 == 0:
            time.sleep(1)
    
    # Summary
    total_tests = 0
    total_matches = 0
    
    for r in results:
        if r['wan1_match'] is not None:
            total_tests += 1
            if r['wan1_match']:
                total_matches += 1
        if r['wan2_match'] is not None:
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
    
    # Show interesting differences
    print("\nInteresting differences:")
    for r in results:
        if r['wan1_match'] is False and r['wan1_json'] != 'N/A':
            print(f"  {r['network']} WAN1: JSON='{r['wan1_json']}' vs NEW='{r['wan1_new']}'")
        if r['wan2_match'] is False and r['wan2_json'] != 'N/A':
            print(f"  {r['network']} WAN2: JSON='{r['wan2_json']}' vs NEW='{r['wan2_new']}'")

if __name__ == "__main__":
    main()