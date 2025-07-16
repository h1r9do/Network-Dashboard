#!/usr/bin/env python3
"""
Check current TST 01 firewall rules to identify duplicate default rules
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
HEADERS = {'X-Cisco-Meraki-API-Key': API_KEY}

def get_tst01_rules():
    """Get current TST 01 firewall rules"""
    tst01_id = 'L_3790904986339115852'
    url = f'https://api.meraki.com/api/v1/networks/{tst01_id}/appliance/firewall/l3FirewallRules'
    
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()['rules']

def main():
    print('🔍 Current TST 01 Firewall Rules Analysis')
    print('=' * 60)
    
    rules = get_tst01_rules()
    print(f'Total rules: {len(rules)}')
    
    print('\nLast 5 rules:')
    for i, rule in enumerate(rules[-5:], start=len(rules)-4):
        print(f'Rule {i}: [{rule.get("policy", "unknown").upper()}] {rule.get("comment", "No comment")}')
        print(f'        Protocol: {rule.get("protocol", "unknown")}')
        print(f'        SRC: {rule.get("srcCidr", "Any")[:50]}')
        print(f'        DST: {rule.get("destCidr", "Any")[:50]}')
        print()
    
    # Find all default rules
    default_rules = []
    for i, rule in enumerate(rules):
        if rule.get('comment') == 'Default rule':
            default_rules.append((i, rule))
    
    print(f'Found {len(default_rules)} "Default rule" entries:')
    for i, (index, rule) in enumerate(default_rules):
        print(f'  Rule {index + 1}: protocol="{rule.get("protocol")}", policy="{rule.get("policy")}"')
    
    if len(default_rules) > 1:
        print(f'\n⚠️  Found {len(default_rules)} duplicate default rules!')
        print('Differences:')
        for i in range(1, len(default_rules)):
            rule1 = default_rules[0][1]
            rule2 = default_rules[i][1]
            for key in rule1.keys():
                if rule1[key] != rule2[key]:
                    print(f'  {key}: "{rule1[key]}" vs "{rule2[key]}"')

if __name__ == '__main__':
    main()