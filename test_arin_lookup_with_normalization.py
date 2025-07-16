#!/usr/bin/env python3
"""Test ARIN lookups with proper normalization for 20 stores with Discount-Tire tag"""

import json
import os
import requests
import time
from datetime import datetime
import re

# Company normalization map (from clean_ip_network_cache.py)
COMPANY_NAME_MAP = {
    "AT&T": ["AT&T", "AT&T Internet Services", "AT&T Enterprises, LLC", "AT&T Broadband", 
             "IPAdmin-ATT Internet Services", "AT&T Communications", "AT&T Business"],
    "Charter Communications": ["Charter Communications LLC", "Charter Communications Inc", 
                             "Charter Communications, LLC", "Charter Communications"],
    "Comcast": ["Comcast Cable Communications, LLC", "Comcast Communications", 
                "Comcast Cable", "Comcast Corporation"],
    "Cox Communications": ["Cox Communications Inc.", "Cox Communications", "Cox Communications Group"],
    "CenturyLink": ["CenturyLink Communications", "CenturyLink", "Lumen Technologies", 
                    "Level 3 Parent, LLC", "Level 3 Communications", "Level3"],
    "Frontier Communications": ["Frontier Communications Corporation", "Frontier Communications", 
                              "Frontier Communications Inc."],
    "Verizon": ["Verizon Communications", "Verizon Internet", "Verizon Business", "Verizon Wireless"],
    "Optimum": ["Optimum", "Altice USA", "Suddenlink Communications"],
    "Crown Castle": ["Crown Castle", "CROWN CASTLE"],
}

def normalize_company_name(name):
    """Normalize company names using known variations"""
    if not name:
        return name
    
    # Clean the name first
    name = re.sub(r"^Private Customer -\s*", "", name).strip()
    
    # Check against known variations
    for company, variations in COMPANY_NAME_MAP.items():
        for variant in variations:
            if variant.lower() in name.lower():
                return company
    
    return name

def collect_org_entities(entity_list):
    """Recursively collect organization entities from RDAP response"""
    org_candidates = []
    
    for entity in entity_list:
        vcard = entity.get("vcardArray")
        if vcard and isinstance(vcard, list) and len(vcard) > 1:
            vcard_props = vcard[1]
            name = None
            kind = None
            
            for prop in vcard_props:
                if len(prop) >= 4:
                    label = prop[0]
                    value = prop[3]
                    if label == "fn":
                        name = value
                    elif label == "kind":
                        kind = value
            
            if kind and kind.lower() == "org" and name:
                # Skip personal names
                if not any(keyword in name for keyword in ["Mr.", "Ms.", "Dr.", "Mrs.", "Miss"]):
                    org_candidates.append(name)
        
        # Check sub-entities
        sub_entities = entity.get("entities", [])
        if sub_entities:
            org_candidates.extend(collect_org_entities(sub_entities))
    
    return org_candidates

def get_arin_provider_normalized(ip_address):
    """Get ISP name from ARIN RDAP API with proper normalization"""
    if not ip_address or ip_address == 'N/A':
        return 'N/A'
    
    # Special handling for 166.80.0.0/16 range
    if ip_address.startswith('166.80.'):
        return 'Crown Castle'
    
    try:
        # Use ARIN RDAP API
        url = f"https://rdap.arin.net/registry/ip/{ip_address}"
        headers = {'Accept': 'application/json'}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # First try to get the network name (this is what the simple parser returns)
        network_name = data.get('network', {}).get('name', '')
        
        # Now look for organization entities (this is what gives us clean names)
        entities = data.get('entities', [])
        if entities:
            org_names = collect_org_entities(entities)
            if org_names:
                # Use the first organization name found
                clean_name = org_names[0]
                normalized_name = normalize_company_name(clean_name)
                return normalized_name
        
        # If no org entities found, try to normalize the network name
        if network_name:
            # Check if it's an AT&T network (SBC-*)
            if network_name.startswith('SBC-'):
                return 'AT&T'
            # Check for other patterns
            elif 'CHARTER' in network_name.upper():
                return 'Charter Communications'
            elif 'COMCAST' in network_name.upper():
                return 'Comcast'
            elif 'COX' in network_name.upper():
                return 'Cox Communications'
            elif 'VERIZON' in network_name.upper():
                return 'Verizon'
            elif 'CENTURYLINK' in network_name.upper():
                return 'CenturyLink'
            elif 'FRONTIER' in network_name.upper():
                return 'Frontier Communications'
            elif 'CC04' in network_name:  # Charter network code
                return 'Charter Communications'
            else:
                # Return the network name as-is if no pattern matches
                return network_name
        
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
    print(f"Testing ARIN lookups with proper normalization for stores with 'Discount-Tire' tag\n")
    
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
            wan1_new = get_arin_provider_normalized(wan1_ip)
            
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
            wan2_new = get_arin_provider_normalized(wan2_ip)
            
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
                wan1_new = get_arin_provider_normalized(wan1_ip)
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
                wan2_new = get_arin_provider_normalized(wan2_ip)
                if wan2_existing != wan2_new and wan2_new != 'Error':
                    print(f"\n{store_name} WAN2:")
                    print(f"  IP: {wan2_ip}")
                    print(f"  Existing: '{wan2_existing}'")
                    print(f"  New lookup: '{wan2_new}'")
                    count += 1

if __name__ == "__main__":
    main()