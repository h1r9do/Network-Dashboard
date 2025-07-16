#!/usr/bin/env python3
"""Test ARIN lookups for NYB stores with proper normalization"""

import json
import os
import requests
import time
from datetime import datetime
import re
import ipaddress

# Known static IP-to-provider mappings
KNOWN_IPS = {
    "63.228.128.81": "CenturyLink",
    "24.101.188.52": "Charter Communications",
    "198.99.82.203": "AT&T",
    "206.222.219.64": "Cogent Communications",
    "208.83.9.194": "CenturyLink",
    "195.252.240.66": "Deutsche Telekom",
    "209.66.104.34": "Verizon",
    "65.100.99.25": "CenturyLink",
    "69.130.234.114": "Comcast",
    "184.61.190.6": "Frontier Communications",
    "72.166.76.98": "Cox Communications",
    "98.6.198.210": "Charter Communications",
    "65.103.195.249": "CenturyLink",
    "100.88.182.60": "Verizon",
    "66.76.161.89": "Suddenlink Communications",
    "66.152.135.50": "EarthLink",
    "216.164.196.131": "RCN",
    "209.124.218.134": "IBM Cloud",
    "67.199.174.137": "Google",
    "184.60.134.66": "Frontier Communications",
    "24.144.4.162": "Conway Corporation",
    "199.38.125.142": "Ritter Communications",
    "69.195.29.6": "Ritter Communications",
    "69.171.123.138": "FAIRNET LLC",
    "63.226.59.241": "CenturyLink Communications, LLC",
    "24.124.116.54": "Midcontinent Communications",
    "50.37.227.70": "Ziply Fiber",
    "24.220.46.162": "Midcontinent Communications",
    "76.14.161.29": "Wave Broadband",
    "71.186.165.101": "Verizon Business",
    "192.190.112.119": "Lrm-Com, Inc.",
    "149.97.243.90": "Equinix, Inc.",
    "162.247.42.4": "HUNTER COMMUNICATIONS",
}

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
        return 'Unknown'
    
    # Check if IP is private - return Unknown like the original system
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        if ip_obj.is_private:
            return 'Unknown'
    except ValueError:
        return 'Unknown'
    
    # Check KNOWN_IPS first
    if ip_address in KNOWN_IPS:
        return KNOWN_IPS[ip_address]
    
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
                # Filter out personal names
                clean_org_names = []
                for name in org_names:
                    # Skip if it looks like a personal name
                    if len(name.split()) == 2 and not any(corp_word in name.lower() for corp_word in 
                        ['communications', 'corporation', 'company', 'inc', 'llc', 'ltd']):
                        continue
                    clean_org_names.append(name)
                
                if clean_org_names:
                    # Use the first organization name found
                    clean_name = clean_org_names[0]
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
    print(f"Testing ARIN lookups for NYB stores\n")
    
    # Filter NYB stores (stores that start with NYB)
    nyb_stores = []
    for entry in data:
        network_name = entry.get('network_name', '')
        if network_name.startswith('NYB'):
            wan1_ip = entry.get('wan1', {}).get('ip')
            wan2_ip = entry.get('wan2', {}).get('ip')
            if wan1_ip or wan2_ip:
                nyb_stores.append(entry)
    
    print(f"Found {len(nyb_stores)} NYB stores with valid IPs")
    print("=" * 120)
    print(f"{'Store Name':<20} {'WAN':<5} {'IP Address':<20} {'Existing Provider':<25} {'New ARIN Lookup':<25} {'Match?':<10}")
    print("=" * 120)
    
    # Test all NYB stores (or first 20 if there are many)
    test_limit = min(20, len(nyb_stores))
    tested = 0
    matches = 0
    mismatches = 0
    errors = 0
    skipped_private = 0
    
    for entry in nyb_stores[:test_limit]:
        store_name = entry.get('network_name', 'N/A')
        
        # Test WAN1
        wan1_data = entry.get('wan1', {})
        wan1_ip = wan1_data.get('ip')
        wan1_existing = wan1_data.get('provider', 'N/A')
        
        if wan1_ip and wan1_ip != 'N/A':
            # Check if private IP
            try:
                if ipaddress.ip_address(wan1_ip).is_private:
                    print(f"{store_name:<20} {'WAN1':<5} {wan1_ip:<20} {'[Private IP - Skipped]':<52}")
                    skipped_private += 1
                    continue
            except ValueError:
                pass
            
            wan1_new = get_arin_provider_normalized(wan1_ip)
            
            # Compare results
            if wan1_new == 'Error':
                match_status = 'ERROR'
                errors += 1
            elif wan1_existing == wan1_new:
                match_status = 'YES'
                matches += 1
            elif wan1_existing == 'Unknown' and wan1_new != 'Unknown':
                match_status = 'NEW DATA'
                matches += 1  # Count as match since we're adding new data
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
            # Check if private IP
            try:
                if ipaddress.ip_address(wan2_ip).is_private:
                    print(f"{store_name:<20} {'WAN2':<5} {wan2_ip:<20} {'[Private IP - Skipped]':<52}")
                    skipped_private += 1
                    continue
            except ValueError:
                pass
            
            wan2_new = get_arin_provider_normalized(wan2_ip)
            
            # Compare results
            if wan2_new == 'Error':
                match_status = 'ERROR'
                errors += 1
            elif wan2_existing == wan2_new:
                match_status = 'YES'
                matches += 1
            elif wan2_existing == 'Unknown' and wan2_new != 'Unknown':
                match_status = 'NEW DATA'
                matches += 1  # Count as match since we're adding new data
            else:
                match_status = 'NO'
                mismatches += 1
            
            print(f"{store_name:<20} {'WAN2':<5} {wan2_ip:<20} {wan2_existing:<25} {wan2_new:<25} {match_status:<10}")
            tested += 1
            time.sleep(0.5)  # Rate limit
    
    # Summary
    print("=" * 120)
    print(f"\nSummary:")
    print(f"Total NYB stores found: {len(nyb_stores)}")
    print(f"Stores tested: {test_limit}")
    print(f"Private IPs skipped: {skipped_private}")
    print(f"Total IPs tested: {tested}")
    if tested > 0:
        print(f"Matches/New Data: {matches} ({matches/tested*100:.1f}%)")
        print(f"Mismatches: {mismatches} ({mismatches/tested*100:.1f}%)")
        print(f"Errors: {errors} ({errors/tested*100:.1f}%)")
    else:
        print("No IPs were tested.")
    
    # Show examples of mismatches for investigation
    if mismatches > 0:
        print("\nExamples of mismatches to investigate:")
        count = 0
        for entry in nyb_stores[:test_limit]:
            if count >= 5:  # Show max 5 examples
                break
            
            store_name = entry.get('network_name', 'N/A')
            
            # Check WAN1
            wan1_data = entry.get('wan1', {})
            wan1_ip = wan1_data.get('ip')
            wan1_existing = wan1_data.get('provider', 'N/A')
            
            if wan1_ip and wan1_ip != 'N/A':
                try:
                    if not ipaddress.ip_address(wan1_ip).is_private:
                        wan1_new = get_arin_provider_normalized(wan1_ip)
                        if wan1_existing != wan1_new and wan1_new != 'Error' and wan1_existing != 'Unknown':
                            print(f"\n{store_name} WAN1:")
                            print(f"  IP: {wan1_ip}")
                            print(f"  Existing: '{wan1_existing}'")
                            print(f"  New lookup: '{wan1_new}'")
                            count += 1
                except ValueError:
                    pass
            
            # Check WAN2
            wan2_data = entry.get('wan2', {})
            wan2_ip = wan2_data.get('ip')
            wan2_existing = wan2_data.get('provider', 'N/A')
            
            if wan2_ip and wan2_ip != 'N/A':
                try:
                    if not ipaddress.ip_address(wan2_ip).is_private:
                        wan2_new = get_arin_provider_normalized(wan2_ip)
                        if wan2_existing != wan2_new and wan2_new != 'Error' and wan2_existing != 'Unknown':
                            print(f"\n{store_name} WAN2:")
                            print(f"  IP: {wan2_ip}")
                            print(f"  Existing: '{wan2_existing}'")
                            print(f"  New lookup: '{wan2_new}'")
                            count += 1
                except ValueError:
                    pass

if __name__ == "__main__":
    main()