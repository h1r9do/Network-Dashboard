#!/usr/bin/env python3
"""
Search for CAL 24 in various forms in Meraki
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

def search_cal24():
    """Search for CAL 24 in various forms"""
    
    meraki_api_key = os.getenv('MERAKI_API_KEY')
    if not meraki_api_key:
        print("ERROR: Meraki API key not found!")
        return
    
    print("Searching for CAL 24 in Meraki...")
    print("="*80)
    
    # Get organization ID
    org_name = "DTC-Store-Inventory-All"
    headers = {
        'X-Cisco-Meraki-API-Key': meraki_api_key,
        'Content-Type': 'application/json'
    }
    
    # Get org ID
    orgs_response = requests.get("https://api.meraki.com/api/v1/organizations", headers=headers, timeout=30)
    orgs_response.raise_for_status()
    org_id = None
    for org in orgs_response.json():
        if org.get('name') == org_name:
            org_id = org['id']
            break
    
    if not org_id:
        print("Organization not found!")
        return
    
    # Get all networks
    networks_url = f"https://api.meraki.com/api/v1/organizations/{org_id}/networks"
    networks_response = requests.get(networks_url, headers=headers, timeout=30)
    networks_response.raise_for_status()
    
    # Search patterns for CAL 24
    search_patterns = [
        'CAL 24',
        'CAL24',
        'CAL-24',
        'CAL_24',
        ' CAL 24 ',  # with spaces
        'CAL 24 ',   # trailing space
        ' CAL 24',   # leading space
    ]
    
    print("Searching for CAL 24 variations...")
    found_any = False
    
    for network in networks_response.json():
        network_name = network.get('name', '')
        
        # Check exact matches
        for pattern in search_patterns:
            if pattern.lower() == network_name.lower():
                print(f"\n✓ EXACT MATCH: '{network_name}' (ID: {network['id']})")
                found_any = True
                
                # Get devices for this network
                try:
                    devices_url = f"https://api.meraki.com/api/v1/networks/{network['id']}/devices"
                    devices_response = requests.get(devices_url, headers=headers, timeout=30)
                    devices_response.raise_for_status()
                    
                    for device in devices_response.json():
                        if device.get('model', '').startswith('MX'):
                            print(f"  - MX Device: {device['model']} (Serial: {device['serial']})")
                except:
                    pass
        
        # Check if contains 24
        if '24' in network_name and 'CAL' in network_name:
            if not any(pattern.lower() == network_name.lower() for pattern in search_patterns):
                print(f"\n? Potential match: '{network_name}'")
                found_any = True
    
    if not found_any:
        print("\nNo networks found containing CAL and 24")
        
        # Show all CAL networks for reference
        print("\nAll CAL networks:")
        cal_networks = []
        for network in networks_response.json():
            if 'CAL' in network.get('name', ''):
                cal_networks.append(network.get('name'))
        
        # Sort numerically
        import re
        def extract_number(name):
            match = re.search(r'CAL\s*(\d+)', name)
            return int(match.group(1)) if match else 999
        
        cal_networks.sort(key=extract_number)
        
        for name in cal_networks[:50]:  # Show first 50
            print(f"  - {name}")
            
        if len(cal_networks) > 50:
            print(f"  ... and {len(cal_networks) - 50} more")

if __name__ == "__main__":
    search_cal24()