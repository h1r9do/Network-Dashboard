#!/usr/bin/env python3
"""
Check TST 01 firewall rules - specifically the last few rules
"""
import os
import sys
import requests
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Meraki API configuration
API_KEY = "5174c907a7d57dea6a0788617287c985cc80b3c1"
BASE_URL = 'https://api.meraki.com/api/v1'
NETWORK_ID = 'L_3790904986339115852'

def get_firewall_rules():
    """Get current L3 firewall rules for the network"""
    headers = {
        'X-Cisco-Meraki-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    url = f"{BASE_URL}/networks/{NETWORK_ID}/appliance/firewall/l3FirewallRules"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching rules: {e}")
        return None

def analyze_rules(rules_data):
    """Analyze the firewall rules, focusing on the last few"""
    if not rules_data or 'rules' not in rules_data:
        print("No rules data found")
        return
    
    rules = rules_data['rules']
    total_rules = len(rules)
    
    print(f"\nTST 01 Firewall Rules Analysis")
    print(f"Total rules: {total_rules}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "="*80)
    
    # Show the last 10 rules
    print("\nLast 10 rules:")
    print("-" * 80)
    
    start_idx = max(0, total_rules - 10)
    for i in range(start_idx, total_rules):
        rule = rules[i]
        print(f"\nRule {i+1}:")
        print(f"  Policy: {rule.get('policy', 'N/A')}")
        print(f"  Protocol: {rule.get('protocol', 'N/A')}")
        print(f"  Src Port: {rule.get('srcPort', 'N/A')}")
        print(f"  Src CIDR: {rule.get('srcCidr', 'N/A')}")
        print(f"  Dest Port: {rule.get('destPort', 'N/A')}")
        print(f"  Dest CIDR: {rule.get('destCidr', 'N/A')}")
        print(f"  Comment: {rule.get('comment', 'N/A')}")
        print(f"  Syslog: {rule.get('syslogEnabled', False)}")
    
    # Check for duplicates in the last few rules
    print("\n" + "="*80)
    print("\nChecking for duplicate rules in positions 50-56:")
    print("-" * 80)
    
    if total_rules >= 50:
        for i in range(49, min(total_rules, 56)):
            rule1 = rules[i]
            # Check against all subsequent rules
            for j in range(i+1, min(total_rules, 56)):
                rule2 = rules[j]
                if (rule1.get('policy') == rule2.get('policy') and
                    rule1.get('protocol') == rule2.get('protocol') and
                    rule1.get('srcPort') == rule2.get('srcPort') and
                    rule1.get('srcCidr') == rule2.get('srcCidr') and
                    rule1.get('destPort') == rule2.get('destPort') and
                    rule1.get('destCidr') == rule2.get('destCidr')):
                    print(f"\nDUPLICATE FOUND!")
                    print(f"  Rule {i+1} and Rule {j+1} are identical")
                    print(f"  Details: {rule1.get('protocol')} from {rule1.get('srcCidr')}:{rule1.get('srcPort')} to {rule1.get('destCidr')}:{rule1.get('destPort')}")
    
    # Save the full rules to a file for detailed analysis
    output_file = f"/usr/local/bin/tst01_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(rules_data, f, indent=2)
    print(f"\n\nFull rules saved to: {output_file}")

def main():
    """Main function"""
    print("Checking TST 01 firewall rules...")
    
    rules_data = get_firewall_rules()
    if rules_data:
        analyze_rules(rules_data)
    else:
        print("Failed to fetch firewall rules")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())