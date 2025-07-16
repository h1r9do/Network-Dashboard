#!/usr/bin/env python3
"""Test ARIN lookups for 20 stores with Discount-Tire tag and compare with existing data"""

import json
import os
import requests
import time
from datetime import datetime

def get_arin_provider(ip_address):
    """Get ISP name from ARIN RDAP API"""
    if not ip_address or ip_address == 'N/A':
        return 'N/A'
    
    # Special handling for 166.80.0.0/16 range
    if ip_address.startswith('166.80.'):
        return 'CROWN CASTLE'
    
    try:
        # Use ARIN RDAP API
        url = f"https://rdap.arin.net/registry/ip/{ip_address}"
        headers = {'Accept': 'application/json'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Try to extract ISP name from various fields
        if 'name' in data:
            return data['name'].upper()
        
        # Check remarks for ISP info
        if 'remarks' in data:
            for remark in data['remarks']:
                if 'title' in remark and 'description' in remark:
                    desc = ' '.join(remark['description'])
                    if 'network name' in desc.lower():
                        return desc.split(':')[-1].strip().upper()
        
        # Check entities
        if 'entities' in data:
            for entity in data['entities']:
                if 'vcardArray' in entity:
                    vcard = entity['vcardArray']
                    if len(vcard) > 1:
                        for item in vcard[1]:
                            if item[0] == 'fn':
                                return item[3].upper()
        
        return 'Unknown'
        
    except requests.exceptions.RequestException as e:
        print(f"  Error looking up {ip_address}: {str(e)}")
        return 'Error'
    except Exception as e:
        print(f"  Unexpected error for {ip_address}: {str(e)}")
        return 'Error'

def main():
    # Load the mx_inventory_live.json file
    json_file = '/var/www/html/meraki-data/mx_inventory_live.json'
    
    if not os.path.exists(json_file):
        print(f"Error: {json_file} not found")
        return
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} entries from mx_inventory_live.json")
    print(f"Testing ARIN lookups for stores with 'Discount-Tire' tag\n")
    
    # Filter stores with Discount-Tire tag and valid IPs
    discount_tire_stores = []
    for entry in data:
        tags = entry.get('device_tags', [])
        if 'Discount-Tire' in tags:
            wan1_ip = entry.get('wan1', {}).get('ip')
            wan2_ip = entry.get('wan2', {}).get('ip')
            if wan1_ip or wan2_ip:
                discount_tire_stores.append(entry)
    
    print(f"Found {len(discount_tire_stores)} stores with Discount-Tire tag and valid IPs")
    print("=" * 120)
    print(f"{'Store Name':<20} {'WAN':<5} {'IP Address':<20} {'Existing Provider':<25} {'New ARIN Lookup':<25} {'Match?':<10}")
    print("=" * 120)
    
    # Test first 20 stores
    tested = 0
    matches = 0
    mismatches = 0
    errors = 0
    
    for entry in discount_tire_stores[:20]:
        store_name = entry.get('network_name', 'N/A')
        
        # Test WAN1
        wan1_data = entry.get('wan1', {})
        wan1_ip = wan1_data.get('ip')
        wan1_existing = wan1_data.get('provider', 'N/A')
        
        if wan1_ip and wan1_ip != 'N/A':
            wan1_new = get_arin_provider(wan1_ip)
            
            # Compare results
            if wan1_new == 'Error':
                match_status = 'ERROR'
                errors += 1
            elif wan1_existing == wan1_new:
                match_status = 'YES'
                matches += 1
            else:
                match_status = 'NO'
                mismatches += 1
            
            print(f"{store_name:<20} {'WAN1':<5} {wan1_ip:<20} {wan1_existing:<25} {wan1_new:<25} {match_status:<10}")
            tested += 1
            time.sleep(0.5)  # Rate limit
        
        # Test WAN2
        wan2_data = entry.get('wan2', {})
        wan2_ip = wan2_data.get('ip')
        wan2_existing = wan2_data.get('provider', 'N/A')
        
        if wan2_ip and wan2_ip != 'N/A':
            wan2_new = get_arin_provider(wan2_ip)
            
            # Compare results
            if wan2_new == 'Error':
                match_status = 'ERROR'
                errors += 1
            elif wan2_existing == wan2_new:
                match_status = 'YES'
                matches += 1
            else:
                match_status = 'NO'
                mismatches += 1
            
            print(f"{store_name:<20} {'WAN2':<5} {wan2_ip:<20} {wan2_existing:<25} {wan2_new:<25} {match_status:<10}")
            tested += 1
            time.sleep(0.5)  # Rate limit
    
    # Summary
    print("=" * 120)
    print(f"\nSummary:")
    print(f"Total IPs tested: {tested}")
    if tested > 0:
        print(f"Matches: {matches} ({matches/tested*100:.1f}%)")
        print(f"Mismatches: {mismatches} ({mismatches/tested*100:.1f}%)")
        print(f"Errors: {errors} ({errors/tested*100:.1f}%)")
    else:
        print("No IPs were tested.")
    
    # Show examples of mismatches for investigation
    if mismatches > 0:
        print("\nExamples of mismatches to investigate:")
        count = 0
        for entry in discount_tire_stores[:20]:
            if count >= 5:  # Show max 5 examples
                break
            
            store_name = entry.get('network_name', 'N/A')
            
            # Check WAN1
            wan1_data = entry.get('wan1', {})
            wan1_ip = wan1_data.get('ip')
            wan1_existing = wan1_data.get('provider', 'N/A')
            
            if wan1_ip and wan1_ip != 'N/A':
                wan1_new = get_arin_provider(wan1_ip)
                if wan1_existing != wan1_new and wan1_new != 'Error':
                    print(f"\n{store_name} WAN1:")
                    print(f"  IP: {wan1_ip}")
                    print(f"  Existing: '{wan1_existing}'")
                    print(f"  New lookup: '{wan1_new}'")
                    count += 1
            
            # Check WAN2
            wan2_data = entry.get('wan2', {})
            wan2_ip = wan2_data.get('ip')
            wan2_existing = wan2_data.get('provider', 'N/A')
            
            if wan2_ip and wan2_ip != 'N/A':
                wan2_new = get_arin_provider(wan2_ip)
                if wan2_existing != wan2_new and wan2_new != 'Error':
                    print(f"\n{store_name} WAN2:")
                    print(f"  IP: {wan2_ip}")
                    print(f"  Existing: '{wan2_existing}'")
                    print(f"  New lookup: '{wan2_new}'")
                    count += 1

if __name__ == "__main__":
    main()