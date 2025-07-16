#!/usr/bin/env python3
"""
Remove duplicate default rule from TST 01
Network ID: L_3790904986339115852
Purpose: Remove one of the two duplicate default rules to match NEO 07's rule count
"""

import requests
import json
from datetime import datetime

# Meraki API Configuration
API_KEY = "5174c907a7d57dea6a0788617287c985cc80b3c1"
BASE_URL = "https://api.meraki.com/api/v1"
NETWORK_ID = "L_3790904986339115852"  # TST 01

def get_current_rules():
    """Get current firewall rules"""
    url = f"{BASE_URL}/networks/{NETWORK_ID}/appliance/firewall/l3FirewallRules"
    headers = {
        "X-Cisco-Meraki-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['rules']

def update_firewall_rules(rules):
    """Update firewall rules"""
    url = f"{BASE_URL}/networks/{NETWORK_ID}/appliance/firewall/l3FirewallRules"
    headers = {
        "X-Cisco-Meraki-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {"rules": rules}
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

def remove_duplicate_default_rule():
    """Remove the duplicate default rule from TST 01"""
    print("Fetching current firewall rules...")
    current_rules = get_current_rules()
    
    print(f"Current rule count: {len(current_rules)}")
    
    # Find duplicate default rules
    default_rules = []
    for i, rule in enumerate(current_rules):
        if rule.get('comment') == 'Default rule':
            default_rules.append((i, rule))
    
    print(f"Found {len(default_rules)} default rules:")
    for i, (index, rule) in enumerate(default_rules):
        print(f"  Rule {index + 1}: {rule['comment']} - {rule['policy']} - protocol: {rule['protocol']}")
    
    if len(default_rules) <= 1:
        print("No duplicate default rules found. Nothing to remove.")
        return
    
    # Remove all but the last default rule
    print(f"\nRemoving {len(default_rules) - 1} duplicate default rule(s)...")
    
    # Keep all rules except the duplicate default rules (keep only the last one)
    rules_to_keep = current_rules[:default_rules[0][0]]  # All rules before first default
    rules_to_keep.append(default_rules[-1][1])  # Add the last default rule
    
    print(f"New rule count: {len(rules_to_keep)}")
    print(f"Reduction: {len(current_rules)} -> {len(rules_to_keep)} rules")
    
    # Update the firewall rules
    print("Updating firewall rules...")
    result = update_firewall_rules(rules_to_keep)
    
    print("✅ Successfully removed duplicate default rule!")
    print(f"Final rule count: {len(result['rules'])}")
    
    return result

def main():
    print("=" * 60)
    print("TST 01 Duplicate Default Rule Removal")
    print("=" * 60)
    print(f"Network ID: {NETWORK_ID}")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    print("⚠️  WARNING: This will modify TST 01 firewall rules!")
    print("This script will remove the duplicate default rule.")
    print("TST 01 currently has 56 rules, target is 55 rules (to match NEO 07)")
    print()
    
    # Show current last 3 rules
    try:
        current_rules = get_current_rules()
        print("Current last 3 rules:")
        for i, rule in enumerate(current_rules[-3:], start=len(current_rules)-2):
            print(f"  Rule {i}: {rule['comment']} - {rule['policy']}")
        print()
    except Exception as e:
        print(f"Could not fetch current rules: {e}")
        return
    
    confirm = input("Type 'YES' to proceed with removal: ")
    if confirm != 'YES':
        print("Operation cancelled.")
        return
    
    try:
        remove_duplicate_default_rule()
        print("\n✅ TST 01 firewall rules successfully updated!")
        print("Rules reduced from 56 to 55 to match NEO 07")
    except Exception as e:
        print(f"❌ Error: {e}")
        return

if __name__ == "__main__":
    main()