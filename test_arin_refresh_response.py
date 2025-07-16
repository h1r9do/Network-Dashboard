#!/usr/bin/env python3
"""Test what the ARIN refresh endpoint actually returns"""

import requests
import json

def test_arin_refresh():
    print("=== Testing ARIN Refresh Response ===\n")
    
    # Test CAL 24
    print("1. Testing CAL 24:")
    response = requests.post("http://localhost:5052/refresh-arin/CAL%2024")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")
    
    # Test CAN 24 for comparison
    print("\n2. Testing CAN 24:")
    response = requests.post("http://localhost:5052/refresh-arin/CAN%2024")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    test_arin_refresh()