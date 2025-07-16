#!/usr/bin/env python3
"""Test script to find working Meraki devices and test tag updates"""

import requests
import os
import time
import json
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
MERAKI_API_KEY = os.getenv('MERAKI_API_KEY')
BASE_URL = "https://api.meraki.com/api/v1"

def make_api_request(url, method='GET', data=None):
    """Make Meraki API request"""
    headers = {
        'X-Cisco-Meraki-API-Key': MERAKI_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data, timeout=30)
        
        print(f"{method} {url}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"Exception: {e}")
        return None

def test_organizations():
    """Test getting organizations"""
    print("=== Testing Organizations ===")
    orgs = make_api_request(f"{BASE_URL}/organizations")
    if orgs:
        for org in orgs:
            print(f"Org: {org.get('name')} (ID: {org.get('id')})")
        return orgs
    return []

def test_networks(org_id):
    """Test getting networks for an org"""
    print(f"\n=== Testing Networks for Org {org_id} ===")
    networks = make_api_request(f"{BASE_URL}/organizations/{org_id}/networks")
    if networks:
        print(f"Found {len(networks)} networks")
        for net in networks[:5]:  # Show first 5
            print(f"  Network: {net.get('name')} (ID: {net.get('id')})")
        return networks
    return []

def test_devices(org_id):
    """Test getting devices for an org"""
    print(f"\n=== Testing Devices for Org {org_id} ===")
    devices = make_api_request(f"{BASE_URL}/organizations/{org_id}/devices")
    if devices:
        mx_devices = [d for d in devices if d.get('model', '').startswith('MX')]
        print(f"Found {len(devices)} total devices, {len(mx_devices)} MX devices")
        
        for device in mx_devices[:3]:  # Show first 3 MX devices
            serial = device.get('serial')
            name = device.get('name', 'Unknown')
            model = device.get('model', 'Unknown')
            print(f"  MX Device: {name} ({model}) - Serial: {serial}")
            
            # Test getting individual device
            device_details = make_api_request(f"{BASE_URL}/devices/{serial}")
            if device_details:
                tags = device_details.get('tags', [])
                print(f"    Current tags: {tags}")
                
        return mx_devices
    return []

def test_tag_update(device_serial, test_tags):
    """Test updating tags on a specific device"""
    print(f"\n=== Testing Tag Update on {device_serial} ===")
    
    # First, get current tags
    current = make_api_request(f"{BASE_URL}/devices/{device_serial}")
    if not current:
        print("Could not get current device info")
        return False
        
    original_tags = current.get('tags', [])
    print(f"Original tags: {original_tags}")
    
    # Test updating tags
    print(f"Attempting to set tags to: {test_tags}")
    result = make_api_request(
        f"{BASE_URL}/devices/{device_serial}", 
        method='PUT', 
        data={'tags': ' '.join(test_tags)}  # Meraki expects space-separated string
    )
    
    if result:
        new_tags = result.get('tags', [])
        print(f"Successfully updated! New tags: {new_tags}")
        
        # Restore original tags
        time.sleep(2)
        print(f"Restoring original tags: {original_tags}")
        restore = make_api_request(
            f"{BASE_URL}/devices/{device_serial}", 
            method='PUT', 
            data={'tags': ' '.join(original_tags)}
        )
        if restore:
            print("Successfully restored original tags")
        return True
    else:
        print("Failed to update tags")
        return False

def main():
    print("Meraki API Tag Update Test")
    print("=" * 50)
    
    if not MERAKI_API_KEY:
        print("ERROR: No Meraki API key found")
        return
        
    print(f"Using API key: {MERAKI_API_KEY[:20]}...")
    
    # Test 1: Get organizations
    orgs = test_organizations()
    if not orgs:
        print("No organizations found - check API key")
        return
        
    # Use first org
    org_id = orgs[0]['id']
    org_name = orgs[0]['name']
    print(f"\nUsing organization: {org_name} ({org_id})")
    
    # Test 2: Get networks
    networks = test_networks(org_id)
    
    # Test 3: Get devices
    devices = test_devices(org_id)
    
    if devices:
        # Test 4: Try updating tags on first device
        test_device = devices[0]
        serial = test_device['serial']
        
        success = test_tag_update(serial, ['test-tag', 'api-test'])
        
        if success:
            print(f"\n✅ SUCCESS: Tag updates work on device {serial}")
            print("You can use this device serial for testing")
        else:
            print(f"\n❌ FAILED: Could not update tags on device {serial}")
    else:
        print("\n❌ No MX devices found to test")

if __name__ == "__main__":
    main()