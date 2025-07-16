#!/usr/bin/env python3
"""Test the tag update API endpoint"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:5052"
TEST_DEVICE = "Q2QN-84BN-W54P"  # ALB 01

def test_tag_update():
    """Test updating tags via the API"""
    
    # Test data
    test_tags = ["Discount-Tire", "TestTag1", "TestTag2"]
    
    # API endpoint
    url = f"{BASE_URL}/api/update-device-tags/{TEST_DEVICE}"
    
    # Request payload
    payload = {
        "action": "replace",
        "tags": test_tags
    }
    
    print(f"Testing tag update API...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Make the request
        response = requests.post(url, json=payload)
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        # Try to parse JSON response
        try:
            response_data = response.json()
            print(f"Response Body: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response Body (raw): {response.text}")
            
        if response.status_code == 200:
            print("\n✅ Tag update successful!")
        else:
            print(f"\n❌ Tag update failed with status {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Error making request: {e}")
        return False
        
    return response.status_code == 200

if __name__ == "__main__":
    success = test_tag_update()
    sys.exit(0 if success else 1)