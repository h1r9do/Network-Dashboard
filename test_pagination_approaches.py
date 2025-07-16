#!/usr/bin/env python3
"""Test different pagination approaches to see which works"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ORG_NAME = "DTC-Store-Inventory-All"
BASE_URL = "https://api.meraki.com/api/v1"

def get_organization_id():
    """Get organization ID"""
    headers = {"X-Cisco-Meraki-API-Key": MERAKI_API_KEY}
    response = requests.get(f"{BASE_URL}/organizations", headers=headers)
    for org in response.json():
        if org["name"] == ORG_NAME:
            return org["id"]
    return None

def test_serial_pagination():
    """Test pagination using serial from last item"""
    print("=== Testing Serial-based Pagination ===")
    org_id = get_organization_id()
    if not org_id:
        print("Organization not found")
        return
    
    all_statuses = []
    url = f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses"
    headers = {"X-Cisco-Meraki-API-Key": MERAKI_API_KEY}
    params = {'perPage': 1000, 'startingAfter': None}
    
    page = 0
    while True:
        page += 1
        response = requests.get(url, headers=headers, params=params)
        statuses = response.json()
        
        if not statuses:
            break
            
        all_statuses.extend(statuses)
        print(f"  Page {page}: Got {len(statuses)} devices, total: {len(all_statuses)}")
        
        # Check if we got a full page
        if len(statuses) < 1000:
            print(f"  Last page had only {len(statuses)} devices")
            break
            
        # Use serial from last device
        params['startingAfter'] = statuses[-1]['serial']
        print(f"  Next cursor: {params['startingAfter']}")
    
    print(f"\n  Total devices with serial pagination: {len(all_statuses)}")
    
    # Check if CAL 24 device is in the list
    cal24_found = False
    for device in all_statuses:
        if device.get('serial') == 'Q2QN-YZRA-UCYJ':
            cal24_found = True
            print(f"\n  ✓ Found CAL 24 device at position {all_statuses.index(device) + 1}")
            break
    
    if not cal24_found:
        print("\n  ✗ CAL 24 device NOT found")
    
    return len(all_statuses)

def test_link_header_pagination():
    """Test pagination using Link header"""
    print("\n=== Testing Link Header Pagination ===")
    org_id = get_organization_id()
    if not org_id:
        print("Organization not found")
        return
    
    all_statuses = []
    url = f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses"
    headers = {"X-Cisco-Meraki-API-Key": MERAKI_API_KEY}
    params = {'perPage': 1000}
    
    page = 0
    next_url = url
    
    while next_url:
        page += 1
        response = requests.get(next_url, headers=headers, params=params if page == 1 else None)
        statuses = response.json()
        
        if not statuses:
            break
            
        all_statuses.extend(statuses)
        print(f"  Page {page}: Got {len(statuses)} devices, total: {len(all_statuses)}")
        
        # Check Link header
        link_header = response.headers.get('Link', '')
        print(f"  Link header: {link_header[:100]}...")
        
        # Parse next URL from Link header
        next_url = None
        if link_header:
            for link in link_header.split(','):
                if 'rel="next"' in link:
                    # Extract URL between < and >
                    import re
                    match = re.search(r'<([^>]+)>', link)
                    if match:
                        next_url = match.group(1)
                        print(f"  Next URL from Link header")
                        break
    
    print(f"\n  Total devices with Link header pagination: {len(all_statuses)}")
    
    # Check if CAL 24 device is in the list
    cal24_found = False
    for device in all_statuses:
        if device.get('serial') == 'Q2QN-YZRA-UCYJ':
            cal24_found = True
            print(f"\n  ✓ Found CAL 24 device at position {all_statuses.index(device) + 1}")
            break
    
    if not cal24_found:
        print("\n  ✗ CAL 24 device NOT found")
    
    return len(all_statuses)

if __name__ == "__main__":
    serial_count = test_serial_pagination()
    link_count = test_link_header_pagination()
    
    print(f"\n=== Summary ===")
    print(f"Serial-based pagination: {serial_count} devices")
    print(f"Link header pagination: {link_count} devices")
    
    if serial_count != link_count:
        print(f"\n⚠️  Warning: Different counts! Difference: {abs(serial_count - link_count)} devices")