#!/usr/bin/env python3
"""
Debug ARIN response structure
"""

import requests
import json

def debug_arin_response(ip):
    """Debug ARIN RDAP response structure"""
    print(f"\nDebugging IP: {ip}")
    print("-" * 50)
    
    try:
        rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
        response = requests.get(rdap_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Show key structure
        print("Top-level keys:", list(data.keys()))
        
        # Check network field
        if 'network' in data:
            print("\nNetwork field:")
            network = data['network']
            print(f"  name: {network.get('name', 'NOT FOUND')}")
            print(f"  handle: {network.get('handle', 'NOT FOUND')}")
            print(f"  type: {network.get('type', 'NOT FOUND')}")
        
        # Check entities
        if 'entities' in data:
            print(f"\nEntities ({len(data['entities'])} found):")
            for i, entity in enumerate(data['entities']):
                print(f"\n  Entity {i}:")
                print(f"    handle: {entity.get('handle', 'NOT FOUND')}")
                print(f"    roles: {entity.get('roles', [])}")
                
                # Check vcard
                vcard = entity.get('vcardArray', [])
                if vcard and len(vcard) > 1:
                    print("    vCard data:")
                    for item in vcard[1]:
                        if item[0] in ['fn', 'org']:
                            print(f"      {item[0]}: {item[3] if len(item) > 3 else 'NO VALUE'}")
        
        # Try simple extraction
        print("\n" + "=" * 50)
        print("SIMPLE EXTRACTION:")
        org = data.get('network', {}).get('name', 'Unknown')
        print(f"Organization from network.name: '{org}'")
        
        return data
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    # Test both IPs
    test_ips = ["205.171.3.65", "8.8.8.8"]
    
    for ip in test_ips:
        debug_arin_response(ip)

if __name__ == "__main__":
    main()