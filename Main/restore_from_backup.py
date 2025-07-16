#!/usr/bin/env python3
"""
Restore network from backup
"""

import json
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')
BASE_URL = 'https://api.meraki.com/api/v1'
headers = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

network_id = 'L_3790904986339115852'

# Load backup
with open('complete_vlan_backup_L_3790904986339115852_20250710_073451.json', 'r') as f:
    backup = json.load(f)

# First, clear firewall rules
print('Clearing firewall rules...')
url = f'{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules'
requests.put(url, headers=headers, json={'rules': []})

# Delete all existing VLANs except management
print('Getting current VLANs...')
url = f'{BASE_URL}/networks/{network_id}/appliance/vlans'
current_vlans = requests.get(url, headers=headers).json()

for vlan in current_vlans:
    if vlan['id'] != 900:  # Keep management VLAN
        print(f'Deleting VLAN {vlan["id"]}...')
        url = f'{BASE_URL}/networks/{network_id}/appliance/vlans/{vlan["id"]}'
        requests.delete(url, headers=headers)
        time.sleep(1)

# Restore VLANs from backup
print('\nRestoring VLANs...')
for vlan in backup['vlans']:
    if vlan['id'] != 900:  # Skip management VLAN
        print(f'Creating VLAN {vlan["id"]}...')
        url = f'{BASE_URL}/networks/{network_id}/appliance/vlans'
        # Remove interfaceId if present
        vlan_data = {k: v for k, v in vlan.items() if k != 'interfaceId'}
        requests.post(url, headers=headers, json=vlan_data)
        time.sleep(1)

print('\nRestore complete!')