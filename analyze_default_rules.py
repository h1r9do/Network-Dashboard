#!/usr/bin/env python3
"""
Deep analysis of the default rules to understand why they can't be removed
"""

import requests
import json
from datetime import datetime

API_KEY = "5174c907a7d57dea6a0788617287c985cc80b3c1"
BASE_URL = "https://api.meraki.com/api/v1"
NETWORK_ID = "L_3790904986339115852"

def get_current_rules():
    """Get current firewall rules with full response"""
    headers = {
        "X-Cisco-Meraki-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    url = f"{BASE_URL}/networks/{NETWORK_ID}/appliance/firewall/l3FirewallRules"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json(), response.headers
    except requests.exceptions.RequestException as e:
        print(f"Error fetching rules: {e}")
        return None, None

def analyze_rules():
    """Analyze the firewall rules structure"""
    
    print("Analyzing TST 01 firewall rules structure...")
    rules_data, headers = get_current_rules()
    
    if not rules_data:
        print("Failed to fetch rules")
        return
    
    print(f"Response headers: {dict(headers)}")
    print(f"Response keys: {list(rules_data.keys())}")
    
    rules = rules_data['rules']
    print(f"Total rules: {len(rules)}")
    
    # Check if there are any special fields in the response
    if 'syslogDefaultRule' in rules_data:
        print(f"syslogDefaultRule present: {rules_data['syslogDefaultRule']}")
    
    # Analyze the last few rules in detail
    print("\nDetailed analysis of last 5 rules:")
    print("=" * 80)
    
    for i in range(max(0, len(rules) - 5), len(rules)):
        rule = rules[i]
        print(f"\nRule {i+1}:")
        print(f"  Full rule data: {json.dumps(rule, indent=4)}")
        
        # Check if there are any hidden or special fields
        for key, value in rule.items():
            if key not in ['comment', 'policy', 'protocol', 'srcPort', 'srcCidr', 'destPort', 'destCidr', 'syslogEnabled']:
                print(f"  ⚠️  UNEXPECTED FIELD: {key} = {value}")
    
    # Check for any pattern in the duplicate rules
    print("\n" + "=" * 80)
    print("Duplicate rule analysis:")
    
    default_rules = []
    for i, rule in enumerate(rules):
        if rule.get('comment', '') == 'Default rule':
            default_rules.append((i, rule))
    
    print(f"Found {len(default_rules)} rules with comment 'Default rule':")
    for idx, (rule_num, rule) in enumerate(default_rules):
        print(f"\nDefault rule #{idx+1} (position {rule_num+1}):")
        print(f"  Protocol: '{rule.get('protocol', '')}'")
        print(f"  Policy: '{rule.get('policy', '')}'")
        print(f"  Src CIDR: '{rule.get('srcCidr', '')}'")
        print(f"  Dest CIDR: '{rule.get('destCidr', '')}'")
        print(f"  Src Port: '{rule.get('srcPort', '')}'")
        print(f"  Dest Port: '{rule.get('destPort', '')}'")
        print(f"  Syslog: {rule.get('syslogEnabled', False)}")
        
        # Check for any hidden differences
        other_fields = {k: v for k, v in rule.items() if k not in ['comment', 'policy', 'protocol', 'srcPort', 'srcCidr', 'destPort', 'destCidr', 'syslogEnabled']}
        if other_fields:
            print(f"  Other fields: {other_fields}")
    
    # Compare the two default rules byte by byte
    if len(default_rules) == 2:
        rule1 = default_rules[0][1]
        rule2 = default_rules[1][1]
        
        print(f"\nByte-by-byte comparison of default rules:")
        print(f"Rule 1 JSON: {json.dumps(rule1, sort_keys=True)}")
        print(f"Rule 2 JSON: {json.dumps(rule2, sort_keys=True)}")
        
        differences = []
        all_keys = set(rule1.keys()) | set(rule2.keys())
        for key in all_keys:
            val1 = rule1.get(key, '<MISSING>')
            val2 = rule2.get(key, '<MISSING>')
            if val1 != val2:
                differences.append(f"  {key}: '{val1}' vs '{val2}'")
        
        if differences:
            print(f"\nDifferences found:")
            for diff in differences:
                print(diff)
        else:
            print(f"\n✅ Rules are identical (except for potential encoding/case differences)")

def main():
    """Main function"""
    print("TST 01 Default Rule Deep Analysis")
    print("=" * 36)
    analyze_rules()

if __name__ == "__main__":
    main()