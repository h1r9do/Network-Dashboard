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

with open('migration_mappings_L_3790904986339115852_20250709_142121.json', 'r') as f:
    mappings = json.load(f)

object_mappings = mappings['object_mappings']
group_mappings = mappings['group_mappings']

print(f'Testing full firewall deployment with {len(template["rules"])} rules...')
print(f'Object mappings: {len(object_mappings)}')
print(f'Group mappings: {len(group_mappings)}')

# Update all rules with new object/group IDs
updated_rules = []
for i, rule in enumerate(template['rules']):
    updated_rule = rule.copy()
    updated_rule.pop('ruleNumber', None)  # Will be auto-assigned
    
    # Update source CIDR references
    src = rule.get('srcCidr', '')
    if 'OBJ(' in src:
        original_src = src
        for old_id, new_id in object_mappings.items():
            src = src.replace(f'OBJ({old_id})', f'OBJ({new_id})')
        updated_rule['srcCidr'] = src
        if original_src != src:
            print(f'  Rule {i+1}: Updated source {original_src} → {src}')
    elif 'GRP(' in src:
        original_src = src
        for old_id, new_id in group_mappings.items():
            src = src.replace(f'GRP({old_id})', f'GRP({new_id})')
        updated_rule['srcCidr'] = src
        if original_src != src:
            print(f'  Rule {i+1}: Updated source {original_src} → {src}')
    
    # Update destination CIDR references
    dst = rule.get('destCidr', '')
    if 'OBJ(' in dst:
        original_dst = dst
        for old_id, new_id in object_mappings.items():
            dst = dst.replace(f'OBJ({old_id})', f'OBJ({new_id})')
        updated_rule['destCidr'] = dst
        if original_dst != dst:
            print(f'  Rule {i+1}: Updated dest {original_dst} → {dst}')
    elif 'GRP(' in dst:
        original_dst = dst
        for old_id, new_id in group_mappings.items():
            dst = dst.replace(f'GRP({old_id})', f'GRP({new_id})')
        updated_rule['destCidr'] = dst
        if original_dst != dst:
            print(f'  Rule {i+1}: Updated dest {original_dst} → {dst}')
    
    updated_rules.append(updated_rule)

print(f'\nApplying all {len(updated_rules)} rules...')

# Apply all rules
url = f'{BASE_URL}/networks/{network_id}/appliance/firewall/l3FirewallRules'
data = {'rules': updated_rules}

response = requests.put(url, headers=HEADERS, json=data, timeout=30)
print(f'API Response: {response.status_code}')

if response.status_code == 200:
    result = response.json()
    actual_count = len(result.get('rules', []))
    print(f'✅ SUCCESS! Applied {actual_count} firewall rules')
    
    # Count rules with object/group references
    obj_rules = 0
    grp_rules = 0
    for rule in result.get('rules', []):
        dst = rule.get('destCidr', '')
        src = rule.get('srcCidr', '')
        if 'OBJ(' in dst or 'OBJ(' in src:
            obj_rules += 1
        if 'GRP(' in dst or 'GRP(' in src:
            grp_rules += 1
    
    print(f'  📦 Rules with policy objects: {obj_rules}')
    print(f'  📋 Rules with policy groups: {grp_rules}')
    print(f'  🎯 Total rules with policy references: {obj_rules + grp_rules}')
else:
    print(f'❌ FAILED: {response.text}')
    
    # Try to identify which rule is causing the issue
    print('\n🔍 Debugging: Testing rules in smaller batches...')
    
    # Test rules in batches of 10
    for start in range(0, len(updated_rules), 10):
        end = min(start + 10, len(updated_rules))
        batch = updated_rules[start:end]
        
        batch_response = requests.put(url, headers=HEADERS, json={'rules': batch}, timeout=30)
        if batch_response.status_code == 200:
            print(f'  ✅ Batch {start//10 + 1} (rules {start+1}-{end}): OK')
        else:
            print(f'  ❌ Batch {start//10 + 1} (rules {start+1}-{end}): FAILED')
            print(f'      Error: {batch_response.text}')