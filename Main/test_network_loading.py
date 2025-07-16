#!/usr/bin/env python3
"""
Test script for the get_meraki_networks function
"""

import sys
sys.path.append('/usr/local/bin/Main')

from vlan_migration_api import get_meraki_networks

print("Testing get_meraki_networks() function...")
try:
    networks = get_meraki_networks()
    print(f"Returned {len(networks)} networks")
    
    if networks:
        print("\nFirst few networks:")
        for i, network in enumerate(networks[:3]):
            print(f"  {i+1}. {network['name']} ({network['id']})")
            print(f"     Subnet: {network.get('subnet_16', 'None')}")
            print(f"     Legacy VLANs: {network.get('legacy_vlans', [])}")
            print(f"     Needs migration: {network.get('needs_migration', False)}")
    else:
        print("No networks returned")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()