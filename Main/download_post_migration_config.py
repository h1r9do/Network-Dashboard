#!/usr/bin/env python3
"""
Download Post-Migration Configuration
Downloads TST 01 configuration after VLAN migration for comparison
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

def download_post_migration_configs():
    print('📥 Downloading Post-Migration Configurations...')
    print('=' * 60)
    
    # Download TST 01 post-migration config
    tst01_id = 'L_3790904986339115852'
    neo07_id = 'L_3790904986339115847'
    
    configs = {}
    
    for network_name, network_id in [('TST 01', tst01_id), ('NEO 07', neo07_id)]:
        print(f'\\nDownloading {network_name} configuration...')
        
        config_data = {
            'download_date': datetime.now().isoformat(),
            'network_id': network_id,
            'network_name': network_name,
            'description': f'{network_name} configuration for post-migration comparison'
        }
        
        # Get network info
        url = f'{BASE_URL}/networks/{network_id}'
        config_data['network'] = make_api_request(url)
        if config_data['network']:
            print(f'  ✓ Network info: {config_data["network"]["name"]}')
        
        # Get VLANs
        url = f'{BASE_URL}/networks/{network_id}/appliance/vlans'
        config_data['vlans'] = make_api_request(url)
        if config_data['vlans']:
            print(f'  ✓ VLANs: {len(config_data["vlans"])} total')
        
        # Get firewall rules
        url = f'{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules'
        config_data['firewall_rules'] = make_api_request(url)
        if config_data['firewall_rules']:
            print(f'  ✓ Firewall rules: {len(config_data["firewall_rules"]["rules"])} total')
        
        # Get devices
        url = f'{BASE_URL}/networks/{network_id}/devices'
        config_data['devices'] = make_api_request(url)
        if config_data['devices']:
            print(f'  ✓ Devices: {len(config_data["devices"])} total')
        
        # Get MX ports
        url = f'{BASE_URL}/networks/{network_id}/appliance/ports'
        config_data['mx_ports'] = make_api_request(url)
        if config_data['mx_ports']:
            print(f'  ✓ MX ports: {len(config_data["mx_ports"])} total')
        
        configs[network_name] = config_data
    
    # Save configurations
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    tst01_filename = f'tst01_post_migration_config_{timestamp}.json'
    with open(tst01_filename, 'w') as f:
        json.dump(configs['TST 01'], f, indent=2)
    print(f'\\n✅ TST 01 post-migration config saved: {tst01_filename}')
    
    neo07_filename = f'neo07_config_{timestamp}.json'
    with open(neo07_filename, 'w') as f:
        json.dump(configs['NEO 07'], f, indent=2)
    print(f'✅ NEO 07 config saved: {neo07_filename}')
    
    return tst01_filename, neo07_filename, configs

if __name__ == '__main__':
    download_post_migration_configs()