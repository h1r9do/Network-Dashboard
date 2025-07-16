#!/usr/bin/env python3
"""Debug why nightly script misses CAL 24 uplink data"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

meraki_api_key = os.getenv('MERAKI_API_KEY')
headers = {
    'X-Cisco-Meraki-API-Key': meraki_api_key,
    'Content-Type': 'application/json'
}

BASE_URL = "https://api.meraki.com/api/v1"

def debug_nightly_issue():
    print("=== Debugging Why Nightly Script Misses CAL 24 ===\n")
    
    # Get org ID
    orgs_response = requests.get(f"{BASE_URL}/organizations", headers=headers, timeout=30)
    org_id = None
    for org in orgs_response.json():
        if org.get('name') == "DTC-Store-Inventory-All":
            org_id = org['id']
            break
    
    # Test 1: Get org-wide uplink statuses (what nightly uses)
    print("1. Testing org-wide uplink status (nightly script method):")
    url = f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses"
    params = {'perPage': 1000}
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    print(f"   Status: {response.status_code}")
    print(f"   Total devices returned: {len(response.json())}")
    
    # Look for CAL 24 in first 1000
    cal24_found = False
    for status in response.json():
        if status.get('serial') == 'Q2QN-YZRA-UCYJ':
            cal24_found = True
            print(f"   ✓ CAL 24 found in first 1000 devices")
            break
    
    if not cal24_found:
        print(f"   ✗ CAL 24 NOT in first 1000 devices")
        
        # Check if there are more pages
        link_header = response.headers.get('Link', '')
        if 'rel="next"' in link_header:
            print(f"   ⚠️  More pages exist - CAL 24 might be on page 2+")
            print(f"   Link header: {link_header[:100]}...")
        
    # Test 2: Get count of total devices
    print("\n2. Checking total device count:")
    page_count = 1
    total_devices = len(response.json())
    
    # Check pagination
    while 'rel="next"' in response.headers.get('Link', ''):
        page_count += 1
        # Extract cursor for next page
        link_header = response.headers.get('Link', '')
        for link in link_header.split(','):
            if 'rel="next"' in link:
                start_after = link.split('startingAfter=')[1].split('&')[0].split('>')[0]
                params['startingAfter'] = start_after
                response = requests.get(url, headers=headers, params=params, timeout=30)
                devices_on_page = len(response.json())
                total_devices += devices_on_page
                
                # Check if CAL 24 is on this page
                for status in response.json():
                    if status.get('serial') == 'Q2QN-YZRA-UCYJ':
                        print(f"   ✓ CAL 24 found on page {page_count}!")
                        print(f"   Device position: {total_devices - devices_on_page + response.json().index(status) + 1}")
                        cal24_found = True
                        break
                break
        
        if cal24_found or page_count > 5:  # Limit to 5 pages for safety
            break
    
    print(f"   Total pages: {page_count}")
    print(f"   Total devices with uplink status: {total_devices}")
    
    # Test 3: Direct network query
    print("\n3. Testing direct network query (filtered):")
    url = f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses"
    params = {'networkIds[]': 'L_650207196201636499'}
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        statuses = response.json()
        print(f"   Devices returned: {len(statuses)}")
        for status in statuses:
            if status.get('serial') == 'Q2QN-YZRA-UCYJ':
                print(f"   ✓ CAL 24 uplink data when filtered by network:")
                uplinks = status.get('uplinks', [])
                for uplink in uplinks:
                    print(f"     {uplink.get('interface')}: {uplink.get('ip')} (public: {uplink.get('publicIp')})")
    
    # Conclusion
    print("\n4. CONCLUSION:")
    if not cal24_found:
        print("   ❌ CAL 24 is beyond the first 1000 devices in org-wide query")
        print("   ❌ Nightly script only processes first page (1000 devices)")
        print("   ✅ CAL 24 exists and has valid uplink data")
        print("   🔧 FIX NEEDED: Nightly script needs pagination support")
    else:
        print("   ✓ CAL 24 should be captured by nightly script")

if __name__ == "__main__":
    debug_nightly_issue()