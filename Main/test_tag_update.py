#!/usr/bin/env python3
"""Test script to verify tag update functionality"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5052"
DEVICE_SERIAL = "Q2QN-84BN-W54P"  # ALB 01

def test_get_device_info():
    """Get current device info including tags"""
    print(f"\n1. Getting device info for {DEVICE_SERIAL}...")
    
    # We'll need to query the database directly for now
    from dsrcircuits import app
    from models import MerakiInventory
    
    with app.app_context():
        device = MerakiInventory.query.filter_by(device_serial=DEVICE_SERIAL).first()
        if device:
            print(f"   Device: {device.device_name}")
            print(f"   Network: {device.network_name}")
            print(f"   Current tags: {device.device_tags}")
            print(f"   Tags type: {type(device.device_tags)}")
            return device.device_tags
        else:
            print("   Device not found!")
            return None

def test_update_tags(tags):
    """Test updating device tags via API"""
    print(f"\n2. Testing tag update to: {tags}")
    
    url = f"{BASE_URL}/api/update-device-tags"
    payload = {
        "device_serial": DEVICE_SERIAL,
        "tags": tags
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def main():
    """Run the tests"""
    print("DSR Circuits Tag Update Test")
    print("=" * 50)
    
    # Get current tags
    current_tags = test_get_device_info()
    
    if current_tags is None:
        print("\nERROR: Could not find device in database!")
        return
    
    # Test 1: Add a new tag
    print("\nTest 1: Adding 'test-tag' to existing tags")
    new_tags = list(current_tags) if current_tags else []
    if 'test-tag' not in new_tags:
        new_tags.append('test-tag')
    
    if test_update_tags(new_tags):
        # Verify it was saved
        updated_tags = test_get_device_info()
        if 'test-tag' in (updated_tags or []):
            print("   ✓ Tag successfully added!")
        else:
            print("   ✗ Tag was not saved to database")
    
    # Test 2: Remove the test tag
    print("\nTest 2: Removing 'test-tag'")
    new_tags = [tag for tag in (current_tags or []) if tag != 'test-tag']
    
    if test_update_tags(new_tags):
        # Verify it was removed
        updated_tags = test_get_device_info()
        if 'test-tag' not in (updated_tags or []):
            print("   ✓ Tag successfully removed!")
        else:
            print("   ✗ Tag was not removed from database")

if __name__ == "__main__":
    main()