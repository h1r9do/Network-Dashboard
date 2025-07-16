#!/usr/bin/env python3
"""Test ARIN lookups for first 50 sites with public IPs"""

import sys
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_provider_for_ip
from sqlalchemy import create_engine, text
from config import Config
import time

def main():
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as conn:
        # Get first 50 sites with public IPs
        result = conn.execute(text('''
            SELECT DISTINCT network_name, wan1_ip, wan1_arin_provider, wan2_ip, wan2_arin_provider
            FROM meraki_inventory
            WHERE device_model LIKE 'MX%'
            AND wan1_ip IS NOT NULL
            AND wan1_ip NOT LIKE '10.%'
            AND wan1_ip NOT LIKE '172.%'
            AND wan1_ip NOT LIKE '192.168%'
            ORDER BY network_name
            LIMIT 50
        '''))
        
        sites = list(result)
    
    print(f"Testing ARIN lookups for {len(sites)} sites...\n")
    
    # Test with our fixed parser
    cache = {}
    missing_set = set()
    results = []
    
    for i, (network_name, wan1_ip, wan1_db, wan2_ip, wan2_db) in enumerate(sites):
        print(f"{i+1}. Testing {network_name}...")
        
        # Test WAN1
        wan1_new = get_provider_for_ip(wan1_ip, cache, missing_set) if wan1_ip else 'N/A'
        wan1_match = (wan1_db == wan1_new) if wan1_db else False
        
        # Test WAN2 (skip private IPs)
        wan2_new = 'N/A'
        wan2_match = True
        if wan2_ip and not any(wan2_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
            wan2_new = get_provider_for_ip(wan2_ip, cache, missing_set)
            wan2_match = (wan2_db == wan2_new) if wan2_db else False
        
        results.append({
            'network': network_name,
            'wan1_ip': wan1_ip,
            'wan1_db': wan1_db or 'Unknown',
            'wan1_new': wan1_new,
            'wan1_match': wan1_match,
            'wan2_ip': wan2_ip,
            'wan2_db': wan2_db or 'Unknown',
            'wan2_new': wan2_new,
            'wan2_match': wan2_match
        })
        
        # Rate limit
        if (i + 1) % 10 == 0:
            time.sleep(1)
    
    # Print results
    print("\n" + "="*130)
    print("RESULTS")
    print("="*130)
    print(f"{'#':>3} {'Network':<15} {'WAN1 IP':<15} {'DB Provider':<25} {'New Provider':<25} {'Match':<6}")
    print("-"*130)
    
    for i, r in enumerate(results):
        print(f"{i+1:>3} {r['network']:<15} {r['wan1_ip']:<15} {r['wan1_db']:<25} {r['wan1_new']:<25} {'✓' if r['wan1_match'] else '✗':<6}")
    
    # Summary
    matches = sum(1 for r in results if r['wan1_match'])
    print("\n" + "="*70)
    print(f"Total sites: {len(results)}")
    print(f"Matching ARIN providers: {matches}")
    print(f"Mismatches: {len(results) - matches}")
    
    # Show some specific examples
    print("\nExamples of what should be updated:")
    for r in results[:10]:
        if r['wan1_db'] == 'Unknown' and r['wan1_new'] != 'Unknown':
            print(f"  {r['network']} - {r['wan1_ip']} → {r['wan1_new']}")

if __name__ == "__main__":
    main()