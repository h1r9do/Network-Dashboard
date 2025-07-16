#!/usr/bin/env python3
"""Test script to verify IP addresses are available in confirm modal data"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from confirm_meraki_notes_db_fixed import confirm_site
import json

# Test with a few sites
test_sites = ['NYB 01', 'NYB 02', 'ALB 01', 'AZP 40']

print("Testing confirm_site function to verify IP addresses are included:\n")

for site in test_sites:
    print(f"Testing site: {site}")
    print("-" * 50)
    
    result = confirm_site(site)
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"WAN1 IP: {result.get('wan1_ip', 'Not found')}")
        print(f"WAN1 Provider (ARIN): {result.get('wan1_provider', 'Not found')}")
        print(f"WAN2 IP: {result.get('wan2_ip', 'Not found')}")
        print(f"WAN2 Provider (ARIN): {result.get('wan2_provider', 'Not found')}")
        
        # Also show the WAN data
        if 'wan1' in result:
            print(f"WAN1 Provider (Enriched): {result['wan1'].get('provider', 'Not found')}")
        if 'wan2' in result:
            print(f"WAN2 Provider (Enriched): {result['wan2'].get('provider', 'Not found')}")
    
    print()

print("\nIf IPs show as 'N/A', check if:")
print("1. The site exists in meraki_inventory table")
print("2. The nightly_meraki_db.py has run to populate IP data")
print("3. The network_name matches between tables")