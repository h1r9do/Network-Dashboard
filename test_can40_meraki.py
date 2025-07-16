#!/usr/bin/env python3
"""
Test script to check CAN 40 Meraki data collection
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Add the test directory to path for imports
sys.path.append('/usr/local/bin/test')

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
BASE_URL = "https://api.meraki.com/api/v1"
ORG_NAME = "DTC-Store-Inventory-All"
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

def get_organization_id():
    """Get the Organization ID for the specified organization."""
    url = f"{BASE_URL}/organizations"
    orgs = make_api_request(url)
    if not orgs:
        raise ValueError("Failed to retrieve organizations")
    
    for org in orgs:
        if org.get("name") == ORG_NAME:
            return org.get("id")
    raise ValueError(f"Organization '{ORG_NAME}' not found")

def main():
    print("Testing CAN 40 Meraki data...")
    
    try:
        org_id = get_organization_id()
        print(f"Organization ID: {org_id}")
        
        # Get uplink statuses
        url = f"{BASE_URL}/organizations/{org_id}/appliance/uplink/statuses"
        print(f"\nFetching uplink statuses...")
        statuses = make_api_request(url)
        
        if statuses:
            # Find CAN 40
            can40_found = False
            for status in statuses:
                network_name = status.get('networkName', '')
                if 'CAN 40' in network_name:
                    can40_found = True
                    print(f"\nFound CAN 40 uplink data:")
                    print(f"Network: {network_name}")
                    print(f"Serial: {status.get('serial')}")
                    print(f"Model: {status.get('model')}")
                    
                    uplinks = status.get('uplinks', [])
                    for uplink in uplinks:
                        interface = uplink.get('interface')
                        ip = uplink.get('ip')
                        status_val = uplink.get('status')
                        assignment = uplink.get('ipAssignedBy')
                        print(f"\n{interface}:")
                        print(f"  IP: {ip}")
                        print(f"  Status: {status_val}")
                        print(f"  Assignment: {assignment}")
                    break
            
            if not can40_found:
                print("\nCAN 40 not found in uplink statuses")
                
                # Search in all networks
                print("\nSearching all networks...")
                networks_url = f"{BASE_URL}/organizations/{org_id}/networks"
                networks = make_api_request(networks_url)
                
                if networks:
                    for net in networks:
                        if 'CAN 40' in net.get('name', ''):
                            print(f"\nFound CAN 40 network:")
                            print(f"Name: {net.get('name')}")
                            print(f"ID: {net.get('id')}")
                            
                            # Get devices in this network
                            devices_url = f"{BASE_URL}/networks/{net['id']}/devices"
                            devices = make_api_request(devices_url)
                            
                            if devices:
                                for device in devices:
                                    if device.get('model', '').startswith('MX'):
                                        print(f"\nMX Device found:")
                                        print(f"Serial: {device.get('serial')}")
                                        print(f"Model: {device.get('model')}")
                                        print(f"Name: {device.get('name')}")
                                        print(f"Notes: {device.get('notes', 'No notes')}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()