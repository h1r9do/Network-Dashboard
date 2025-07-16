#!/usr/bin/env python3
"""
Find ALB networks in Meraki
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Configuration
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"

def make_api_request(url, api_key):
    """Make API request."""
    headers = {"X-Cisco-Meraki-API-Key": api_key}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error: {e}")
    return None

# Get organization
url = f"{BASE_URL}/organizations"
orgs = make_api_request(url, MERAKI_API_KEY)
org_id = None
if orgs:
    for org in orgs:
        if org['name'] == "DTC-Store-Inventory-All":
            org_id = org['id']
            break

if org_id:
    # Get all networks
    url = f"{BASE_URL}/organizations/{org_id}/networks"
    networks = make_api_request(url, MERAKI_API_KEY)
    
    print("Searching for ALB networks...")
    alb_networks = []
    if networks:
        for net in networks:
            name = net['name']
            # Try different patterns
            if 'ALB' in name.upper():
                alb_networks.append(name)
                print(f"  Found: {name}")
    
    if not alb_networks:
        print("No ALB networks found. Here are some sample network names:")
        if networks:
            for i, net in enumerate(networks[:20]):
                print(f"  {net['name']}")
            print(f"  ... ({len(networks)} total networks)")