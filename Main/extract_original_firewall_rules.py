#!/usr/bin/env python3
"""
Extract Original Firewall Rules from NEO 07
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')
BASE_URL = 'https://api.meraki.com/api/v1'
HEADERS = {'X-Cisco-Meraki-API-Key': API_KEY, 'Content-Type': 'application/json'}

# NEO 07 network
network_id = 'L_3790904986339115847'

print(f'Extracting original firewall rules from NEO 07...')

url = f'{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules'
response = requests.get(url, headers=HEADERS)

if response.status_code == 200:
    result = response.json()
    rules = result.get('rules', [])
    
    # Save original rules
    with open('neo_07_original_firewall_rules.json', 'w') as f:
        json.dump({'rules': rules}, f, indent=2)
    
    print(f'✅ Extracted {len(rules)} firewall rules')
    
    # Check VLAN references
    vlan_refs = set()
    for rule in rules:
        src = rule.get('srcCidr', '')
        dst = rule.get('destCidr', '')
        
        # Find VLAN references
        import re
        vlan_pattern = r'VLAN\((\d+)\)'
        
        src_vlans = re.findall(vlan_pattern, src)
        dst_vlans = re.findall(vlan_pattern, dst)
        
        vlan_refs.update(src_vlans)
        vlan_refs.update(dst_vlans)
    
    print(f'VLAN references found: {sorted([int(v) for v in vlan_refs])}')
    
else:
    print(f'❌ Failed to get firewall rules: {response.status_code}')