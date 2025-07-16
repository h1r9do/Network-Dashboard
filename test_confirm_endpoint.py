#!/usr/bin/env python3
"""Test the confirm endpoint to see what data it returns"""

import requests
import json

def test_confirm():
    print("=== Testing Confirm Endpoint ===\n")
    
    # Test CAL 24
    print("1. Testing CAL 24 confirm endpoint:")
    response = requests.post("http://localhost:5052/confirm/CAL%2024")
    if response.status_code == 200:
        data = response.json()
        print(f"  Success: {data.get('success')}")
        print(f"  WAN1 IP: {data.get('wan1_ip')}")
        print(f"  WAN2 IP: {data.get('wan2_ip')}")
        print(f"  WAN1 ARIN: {data.get('wan1_arin_provider')}")
        print(f"  WAN2 ARIN: {data.get('wan2_arin_provider')}")
    else:
        print(f"  Error: {response.status_code}")
        print(f"  Response: {response.text}")

if __name__ == "__main__":
    test_confirm()