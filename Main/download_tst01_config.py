#!/usr/bin/env python3
"""
Download TST 01 Configuration
Downloads complete TST 01 configuration for comparison with AZP 30
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def make_api_request(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json() if response.text else None
    except Exception as e:
        print(f'Error: {e}')
        return None

def download_tst01_config():
    tst01_id = 'L_3790904986339115852'
    
    config_data = {
        'download_date': datetime.now().isoformat(),
        'network_id': tst01_id,
        'network_name': 'TST 01 - Post Quick Restore',
        'description': 'TST 01 configuration after quick restore from production-ready backup'
    }
    
    print('📥 Downloading TST 01 Configuration...')
    print('=' * 50)
    
    # Get network info
    url = f'{BASE_URL}/networks/{tst01_id}'
    config_data['network'] = make_api_request(url)
    if config_data['network']:
        print(f'  ✓ Network info: {config_data["network"]["name"]}')
    
    # Get devices
    url = f'{BASE_URL}/networks/{tst01_id}/devices'
    config_data['devices'] = make_api_request(url)
    if config_data['devices']:
        print(f'  ✓ Devices: {len(config_data["devices"])} total')
    
    # Get VLANs
    url = f'{BASE_URL}/networks/{tst01_id}/appliance/vlans'
    config_data['vlans'] = make_api_request(url)
    if config_data['vlans']:
        print(f'  ✓ VLANs: {len(config_data["vlans"])} total')
    
    # Get firewall rules
    url = f'{BASE_URL}/networks/{tst01_id}/appliance/firewall/l3FirewallRules'
    config_data['firewall_rules'] = make_api_request(url)
    if config_data['firewall_rules']:
        print(f'  ✓ Firewall rules: {len(config_data["firewall_rules"]["rules"])} total')
    
    # Get MX ports
    url = f'{BASE_URL}/networks/{tst01_id}/appliance/ports'
    config_data['mx_ports'] = make_api_request(url)
    if config_data['mx_ports']:
        print(f'  ✓ MX ports: {len(config_data["mx_ports"])} total')
    
    # Get switch port configurations
    if config_data['devices']:
        switches = [d for d in config_data['devices'] if d['model'].startswith('MS')]
        config_data['switch_ports'] = {}
        
        for switch in switches:
            url = f'{BASE_URL}/devices/{switch["serial"]}/switch/ports'
            ports = make_api_request(url)
            if ports:
                config_data['switch_ports'][switch['serial']] = ports
                print(f'  ✓ Switch ports: {len(ports)} ports for {switch["name"]}')
    
    # Get group policies
    url = f'{BASE_URL}/networks/{tst01_id}/groupPolicies'
    config_data['group_policies'] = make_api_request(url)
    if config_data['group_policies']:
        print(f'  ✓ Group policies: {len(config_data["group_policies"])} total')
    
    # Save configuration
    filename = f'tst01_post_quick_restore_config_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(filename, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    print(f'\\n✅ TST 01 configuration downloaded: {filename}')
    return filename

if __name__ == '__main__':
    download_tst01_config()