#!/usr/bin/env python3
"""Check current status of TST 01"""

import os
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("API_KEY") or os.getenv("MERAKI_API_KEY")

headers = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

network_id = 'L_3790904986339115852'

# Get VLANs
print("Checking TST 01 VLANs...")
vlans_url = f"https://api.meraki.com/api/v1/networks/{network_id}/appliance/vlans"
vlans_response = requests.get(vlans_url, headers=headers)

if vlans_response.status_code == 200:
    vlans = vlans_response.json()
    print(f"Found {len(vlans)} VLANs:")
    for vlan in vlans:
        print(f"  - VLAN {vlan['id']}: {vlan['name']}")
else:
    print(f"Error getting VLANs: {vlans_response.status_code}")

# Get firewall rules
print("\nChecking TST 01 Firewall Rules...")
fw_url = f"https://api.meraki.com/api/v1/networks/{network_id}/appliance/firewall/l3FirewallRules"
fw_response = requests.get(fw_url, headers=headers)

if fw_response.status_code == 200:
    rules = fw_response.json()
    rule_count = len(rules.get('rules', []))
    print(f"Found {rule_count} firewall rules")
else:
    print(f"Error getting firewall rules: {fw_response.status_code}")

# Check for legacy VLANs
if vlans_response.status_code == 200:
    legacy_vlan_ids = ['1', '101', '201', '801']
    legacy_vlans = [v for v in vlans if v['id'] in legacy_vlan_ids]

    print(f"\nLegacy VLANs present: {len(legacy_vlans)}")
    for v in legacy_vlans:
        print(f"  - VLAN {v['id']}")

    print(f"\nNeeds migration: {len(legacy_vlans) > 0}")