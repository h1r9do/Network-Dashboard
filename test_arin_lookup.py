#!/usr/bin/env python3
"""
Test ARIN lookup for specific IPs
"""

import requests
import json

def lookup_ip(ip):
    """Lookup IP address in ARIN RDAP"""
    print(f"\nLooking up IP: {ip}")
    
    try:
        # Query ARIN RDAP
        rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
        response = requests.get(rdap_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract organization info - try different fields
        org_name = data.get('network', {}).get('name', '')
        handle = data.get('network', {}).get('handle', '')
        
        # If no network name, look in entities
        if not org_name:
            entities = data.get('entities', [])
            for entity in entities:
                if entity.get('roles') and 'registrant' in entity.get('roles', []):
                    vcard = entity.get('vcardArray', [])
                    if vcard and len(vcard) > 1:
                        for item in vcard[1]:
                            if item[0] == 'fn':
                                org_name = item[3]
                                break
        
        print(f"  Organization: {org_name or 'Unknown'}")
        print(f"  Handle: {handle}")
        
        # Get more details
        entities = data.get('entities', [])
        for entity in entities:
            if entity.get('roles') and 'registrant' in entity.get('roles', []):
                org_details = entity.get('vcardArray', [])
                if org_details and len(org_details) > 1:
                    for item in org_details[1]:
                        if item[0] == 'org':
                            print(f"  Organization Name: {item[3]}")
        
        # Show IP range
        cidr = data.get('cidr0_cidrs', [])
        if cidr:
            print(f"  CIDR Blocks: {', '.join([c.get('v4prefix', '') or c.get('v6prefix', '') for c in cidr])}")
        
        return org_name
        
    except Exception as e:
        print(f"  Error: {e}")
        return None

def main():
    """Test specific IPs"""
    test_ips = ["205.171.3.65", "8.8.8.8"]
    
    print("ARIN RDAP IP Lookup Test")
    print("=" * 50)
    
    for ip in test_ips:
        lookup_ip(ip)
    
    print("\n" + "=" * 50)
    print("Test complete")

if __name__ == "__main__":
    main()