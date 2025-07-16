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

# Test rule 12 (index 11) - Outbound EPX
test_rule = template['rules'][11]
print(f'Testing rule: {test_rule.get("comment", "")}')
print(f'Original dest: {test_rule.get("destCidr", "")}')

# Update the rule
updated_rule = test_rule.copy()
updated_rule.pop('ruleNumber', None)

# Update destination CIDR references
dst = test_rule.get('destCidr', '')
if 'GRP(' in dst:
    for old_id, new_id in group_mappings.items():
        dst = dst.replace(f'GRP({old_id})', f'GRP({new_id})')
    updated_rule['destCidr'] = dst

print(f'Updated dest: {updated_rule.get("destCidr", "")}')

# Create a simple ruleset with just this rule
test_rules = [
    {
        'comment': 'Default allow',
        'srcCidr': 'Any',
        'srcPort': 'Any', 
        'destCidr': 'Any',
        'destPort': 'Any',
        'protocol': 'any',
        'policy': 'allow',
        'syslogEnabled': False
    },
    updated_rule
]

# Try to apply
url = f'{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules'
data = {'rules': test_rules}

response = requests.put(url, headers=HEADERS, json=data, timeout=30)
print(f'\nAPI Response: {response.status_code}')
if response.status_code != 200:
    print(f'Error: {response.text}')
else:
    print('✓ Rule with group reference applied successfully')