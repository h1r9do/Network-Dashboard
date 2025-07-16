#!/usr/bin/env python3
"""
Wipe TST 01 Configuration
Clears VLANs and firewall rules to prepare for restore
"""

import os
import sys
import requests
import time
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')
BASE_URL = 'https://api.meraki.com/api/v1'
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

def make_api_request(url, method='GET', data=None):
    try:
        if method == 'GET':
            response = requests.get(url, headers=HEADERS, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, headers=HEADERS, json=data, timeout=30)
        elif method == 'DELETE':
            response = requests.delete(url, headers=HEADERS, timeout=30)
        
        response.raise_for_status()
        return response.json() if response.text else None
    except Exception as e:
        print(f'Error: {e}')
        return None

def wipe_tst01():
    tst01_id = 'L_3790904986339115852'
    print('🧹 Wiping TST 01 Configuration...')
    print('=' * 50)
    
    # Clear firewall rules first
    print('Clearing firewall rules...')
    url = f'{BASE_URL}/networks/{tst01_id}/appliance/firewall/l3FirewallRules'
    result = make_api_request(url, method='PUT', data={'rules': []})
    if result:
        print('  ✓ Firewall rules cleared')
    
    # Delete VLANs (except management)
    print('Clearing VLANs...')
    url = f'{BASE_URL}/networks/{tst01_id}/appliance/vlans'
    current_vlans = make_api_request(url)
    
    if current_vlans:
        for vlan in current_vlans:
            if vlan['id'] != 900:  # Keep management VLAN
                print(f'  Deleting VLAN {vlan["id"]}...')
                delete_url = f'{BASE_URL}/networks/{tst01_id}/appliance/vlans/{vlan["id"]}'
                make_api_request(delete_url, method='DELETE')
                time.sleep(1)
    
    print('')
    print('✅ TST 01 configuration wiped successfully!')
    print('Ready for quick restore...')

if __name__ == '__main__':
    wipe_tst01()