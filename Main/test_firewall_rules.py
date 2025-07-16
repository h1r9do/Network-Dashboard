#!/usr/bin/env python3

import json
import os
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')
BASE_URL = 'https://api.meraki.com/api/v1'
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

network_id = 'L_3790904986339115852'  # TST 01

# Load firewall template and mappings
with open('firewall_rules_template.json', 'r') as f:
    template = json.load(f)

with open('migration_mappings_L_3790904986339115852_20250709_141518.json', 'r') as f:
    mappings = json.load(f)

object_mappings = mappings['object_mappings']
group_mappings = mappings['group_mappings']

# Update just the first 5 rules to test
test_rules = template['rules'][:5]
updated_rules = []

for rule in test_rules:
    updated_rule = rule.copy()
    updated_rule.pop('ruleNumber', None)
    
    # Update destination CIDR references
    dst = rule.get('destCidr', '')
    if 'OBJ(' in dst:
        for old_id, new_id in object_mappings.items():
            dst = dst.replace(f'OBJ({old_id})', f'OBJ({new_id})')
        updated_rule['destCidr'] = dst
    elif 'GRP(' in dst:
        for old_id, new_id in group_mappings.items():
            dst = dst.replace(f'GRP({old_id})', f'GRP({new_id})')
        updated_rule['destCidr'] = dst
    
    updated_rules.append(updated_rule)

print('Testing first 5 firewall rules...')
for i, rule in enumerate(updated_rules):
    print(f'Rule {i+1}: {rule.get("comment", "")}')
    print(f'  Dest: {rule.get("destCidr", "")}')

# Try to apply just these 5 rules
url = f'{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules'
data = {'rules': updated_rules}

response = requests.put(url, headers=HEADERS, json=data, timeout=30)
print(f'\nAPI Response: {response.status_code}')
if response.status_code != 200:
    print(f'Error: {response.text}')
else:
    print('✓ First 5 rules applied successfully')