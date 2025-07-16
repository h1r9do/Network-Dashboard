#!/usr/bin/env python3
"""
Test script to check CAN 40 device status and management interface
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")

def get_headers():
    return {
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "Content-Type": "application/json"
    }

def make_api_request(url):
    """Make a GET request to the Meraki API"""
    headers = get_headers()
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    print("Testing CAN 40 device status...")
    
    # CAN 40 device serial from previous test
    device_serial = "Q2QN-HC4S-PEL3"
    
    # Get device status
    status_url = f"{BASE_URL}/devices/{device_serial}/managementInterface"
    print(f"\nFetching management interface for {device_serial}...")
    mgmt_interface = make_api_request(status_url)
    
    if mgmt_interface:
        print("\nManagement Interface:")
        print(f"WAN1: {mgmt_interface.get('wan1', {})}")
        print(f"WAN2: {mgmt_interface.get('wan2', {})}")
    
    # Try device uplinks
    uplinks_url = f"{BASE_URL}/devices/{device_serial}/appliance/uplinks/settings"
    print(f"\nFetching uplink settings...")
    uplink_settings = make_api_request(uplinks_url)
    
    if uplink_settings:
        print("\nUplink Settings:")
        for interface in uplink_settings.get('interfaces', {}).values():
            print(f"\nInterface: {interface.get('wan', {}).get('interface', 'Unknown')}")
            print(f"  Enabled: {interface.get('enabled')}")
            print(f"  VLANs: {interface.get('vlanTagging', {})}")
            print(f"  SIMs: {interface.get('sims', [])}")
            print(f"  PPPoE: {interface.get('pppoe', {})}")
    
    # Try live tools to get IP
    print("\nChecking device connectivity status...")
    connectivity_url = f"{BASE_URL}/devices/{device_serial}/liveTools/connectivity"
    connectivity = make_api_request(connectivity_url)
    
    if connectivity:
        print("\nConnectivity Status:")
        print(connectivity)

if __name__ == "__main__":
    main()