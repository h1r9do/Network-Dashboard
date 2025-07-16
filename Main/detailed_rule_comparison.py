#!/usr/bin/env python3
"""
Detailed Rule-by-Rule Comparison
Compare TST 01 and NEO 07 firewall rules line by line
"""

import requests
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
HEADERS = {'X-Cisco-Meraki-API-Key': API_KEY}

def get_firewall_rules(network_id, network_name):
    """Get firewall rules for a network"""
    url = f'https://api.meraki.com/api/v1/networks/{network_id}/appliance/firewall/l3FirewallRules'
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()['rules']

def normalize_rule_for_comparison(rule, network_name):
    """Normalize rule for comparison by removing network-specific elements"""
    normalized = {
        'comment': rule.get('comment', 'No comment'),
        'policy': rule.get('policy', 'unknown'),
        'protocol': rule.get('protocol', 'any'),
        'srcPort': rule.get('srcPort', 'Any'),
        'destPort': rule.get('destPort', 'Any'),
        'srcCidr': rule.get('srcCidr', 'Any'),
        'destCidr': rule.get('destCidr', 'Any'),
        'syslogEnabled': rule.get('syslogEnabled', False)
    }
    
    # Normalize IP addresses for comparison
    if network_name == 'TST 01':
        # Convert TST 01 test IPs back to generic format
        if normalized['srcCidr']:
            normalized['srcCidr'] = normalized['srcCidr'].replace('10.1.32.', '10.X.X.')
        if normalized['destCidr']:
            normalized['destCidr'] = normalized['destCidr'].replace('10.1.32.', '10.X.X.')
    elif network_name == 'NEO 07':
        # Convert NEO 07 production IPs to generic format
        if normalized['srcCidr']:
            normalized['srcCidr'] = normalized['srcCidr'].replace('10.24.38.', '10.X.X.')
        if normalized['destCidr']:
            normalized['destCidr'] = normalized['destCidr'].replace('10.24.38.', '10.X.X.')
    
    return normalized

def compare_rules():
    """Compare firewall rules between TST 01 and NEO 07"""
    print('🔍 Detailed Rule-by-Rule Comparison: TST 01 vs NEO 07')
    print('=' * 80)
    
    # Get rules from both networks
    tst01_id = 'L_3790904986339115852'
    neo07_id = 'L_3790904986339115847'
    
    print('Downloading firewall rules...')
    tst01_rules = get_firewall_rules(tst01_id, 'TST 01')
    neo07_rules = get_firewall_rules(neo07_id, 'NEO 07')
    
    print(f'TST 01: {len(tst01_rules)} rules')
    print(f'NEO 07: {len(neo07_rules)} rules')
    
    # Normalize rules for comparison
    tst01_normalized = [normalize_rule_for_comparison(rule, 'TST 01') for rule in tst01_rules]
    neo07_normalized = [normalize_rule_for_comparison(rule, 'NEO 07') for rule in neo07_rules]
    
    print('\\n' + '=' * 80)
    print('RULE-BY-RULE COMPARISON')
    print('=' * 80)
    
    max_rules = max(len(tst01_rules), len(neo07_rules))
    matches = 0
    
    for i in range(max_rules):
        print(f'\\nRule {i+1}:')
        print('-' * 40)
        
        if i < len(tst01_rules):
            tst01_rule = tst01_rules[i]
            tst01_norm = tst01_normalized[i]
            print(f'TST 01: [{tst01_rule.get("policy", "unknown").upper()}] {tst01_rule.get("comment", "No comment")}')
            print(f'        SRC: {tst01_rule.get("srcCidr", "Any")[:60]}')
            print(f'        DST: {tst01_rule.get("destCidr", "Any")[:60]}')
        else:
            print('TST 01: MISSING')
            tst01_norm = None
        
        if i < len(neo07_rules):
            neo07_rule = neo07_rules[i]
            neo07_norm = neo07_normalized[i]
            print(f'NEO 07: [{neo07_rule.get("policy", "unknown").upper()}] {neo07_rule.get("comment", "No comment")}')
            print(f'        SRC: {neo07_rule.get("srcCidr", "Any")[:60]}')
            print(f'        DST: {neo07_rule.get("destCidr", "Any")[:60]}')
        else:
            print('NEO 07: MISSING')
            neo07_norm = None
        
        # Compare normalized rules
        if tst01_norm and neo07_norm:
            match = (tst01_norm['comment'] == neo07_norm['comment'] and 
                    tst01_norm['policy'] == neo07_norm['policy'])
            if match:
                matches += 1
                print('MATCH: ✓ Comment and policy match')
            else:
                print('DIFFER: ✗ Comment or policy differs')
                if tst01_norm['comment'] != neo07_norm['comment']:
                    print(f'  Comment diff: "{tst01_norm["comment"]}" vs "{neo07_norm["comment"]}"')
                if tst01_norm['policy'] != neo07_norm['policy']:
                    print(f'  Policy diff: "{tst01_norm["policy"]}" vs "{neo07_norm["policy"]}"')
        else:
            print('DIFFER: ✗ Rule missing in one network')
    
    print('\\n' + '=' * 80)
    print('COMPARISON SUMMARY')
    print('=' * 80)
    print(f'Total rules compared: {max_rules}')
    print(f'Exact matches: {matches}')
    print(f'Differences: {max_rules - matches}')
    print(f'Match percentage: {matches/max_rules*100:.1f}%')
    
    # Find rules that exist in one but not the other
    print('\\n' + '=' * 80)
    print('DETAILED ANALYSIS')
    print('=' * 80)
    
    # Create signatures for comparison
    tst01_signatures = set()
    neo07_signatures = set()
    
    for rule in tst01_normalized:
        sig = f"{rule['policy']}-{rule['comment']}"
        tst01_signatures.add(sig)
    
    for rule in neo07_normalized:
        sig = f"{rule['policy']}-{rule['comment']}"
        neo07_signatures.add(sig)
    
    tst01_only = tst01_signatures - neo07_signatures
    neo07_only = neo07_signatures - tst01_signatures
    
    if tst01_only:
        print(f'\\nRules ONLY in TST 01 ({len(tst01_only)}):')
        for i, sig in enumerate(tst01_only, 1):
            parts = sig.split('-', 1)
            policy = parts[0]
            comment = parts[1] if len(parts) > 1 else 'No comment'
            print(f'  {i}. [{policy.upper()}] {comment}')
    
    if neo07_only:
        print(f'\\nRules ONLY in NEO 07 ({len(neo07_only)}):')
        for i, sig in enumerate(neo07_only, 1):
            parts = sig.split('-', 1)
            policy = parts[0]
            comment = parts[1] if len(parts) > 1 else 'No comment'
            print(f'  {i}. [{policy.upper()}] {comment}')
    
    if not tst01_only and not neo07_only:
        print('\\n✅ All rule signatures match between networks!')
    else:
        print(f'\\n❌ Found {len(tst01_only)} unique TST 01 rules and {len(neo07_only)} unique NEO 07 rules')
    
    return matches == max_rules

if __name__ == '__main__':
    try:
        compare_rules()
    except Exception as e:
        print(f'Error: {e}')