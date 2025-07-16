#!/usr/bin/env python3
"""
Test the enhanced ARIN refresh functionality for CAL 24
"""

import requests
import json

# Test the ARIN refresh endpoint
base_url = "http://localhost:5052"
site_name = "CAL 24"

print(f"Testing ARIN refresh for {site_name}...")
print("="*80)

# Make the API call
try:
    response = requests.post(f"{base_url}/api/refresh-arin/{site_name}", timeout=30)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print("\nResponse Body:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code == 200:
        data = response.json()
        print("\n✓ SUCCESS - ARIN data retrieved:")
        print(f"  Source: {data.get('source', 'unknown')}")
        print(f"  WAN1 IP: {data.get('wan1_ip', 'N/A')}")
        print(f"  WAN1 Provider: {data.get('wan1_arin_provider', 'N/A')}")
        print(f"  WAN2 IP: {data.get('wan2_ip', 'N/A')}")
        print(f"  WAN2 Provider: {data.get('wan2_arin_provider', 'N/A')}")
        
        if data.get('warnings'):
            print("\n⚠️  Warnings:")
            for warning in data['warnings']:
                print(f"  - {warning}")
    else:
        print("\n✗ ERROR - Failed to refresh ARIN data")
        if response.status_code == 404:
            print("  This is expected for CAL 24 as it has no Meraki device")
        
except Exception as e:
    print(f"\n✗ ERROR: {e}")

print("\n" + "="*80)
print("Test complete!")