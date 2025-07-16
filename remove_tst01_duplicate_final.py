#!/usr/bin/env python3
"""
Remove duplicate default rule from TST 01 - Final corrected version
Fixed the API format issue - need to send {"rules": [...]} not just [...]
"""

import requests
import json
from datetime import datetime

API_KEY = "5174c907a7d57dea6a0788617287c985cc80b3c1"
BASE_URL = "https://api.meraki.com/api/v1"
NETWORK_ID = "L_3790904986339115852"

def get_current_rules():
    """Get current firewall rules"""
    headers = {
        "X-Cisco-Meraki-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    url = f"{BASE_URL}/networks/{NETWORK_ID}/appliance/firewall/l3FirewallRules"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching rules: {e}")
        return None

def normalize_rule_for_comparison(rule):
    """Normalize rule values for comparison (handle case sensitivity)"""
    normalized = rule.copy()
    
    # Normalize protocol field - both "any" and "Any" are equivalent
    if normalized.get('protocol', '').lower() == 'any':
        normalized['protocol'] = 'any'
    
    # Normalize other fields that might have case variations
    for field in ['policy', 'srcPort', 'srcCidr', 'destPort', 'destCidr']:
        if field in normalized and normalized[field]:
            if normalized[field].lower() == 'any':
                normalized[field] = 'Any'
    
    return normalized

def find_duplicate_rules(rules):
    """Find duplicate rules considering case-insensitive comparison"""
    duplicates = []
    
    for i, rule1 in enumerate(rules):
        for j, rule2 in enumerate(rules[i+1:], i+1):
            norm1 = normalize_rule_for_comparison(rule1)
            norm2 = normalize_rule_for_comparison(rule2)
            
            # Compare all relevant fields
            if (norm1.get('policy') == norm2.get('policy') and
                norm1.get('protocol') == norm2.get('protocol') and
                norm1.get('srcPort') == norm2.get('srcPort') and
                norm1.get('srcCidr') == norm2.get('srcCidr') and
                norm1.get('destPort') == norm2.get('destPort') and
                norm1.get('destCidr') == norm2.get('destCidr') and
                norm1.get('comment') == norm2.get('comment')):
                
                duplicates.append((i, j))
    
    return duplicates

def remove_duplicate_default_rule():
    """Remove the duplicate default rule from TST 01"""
    
    # Get current rules
    print("Fetching current rules...")
    rules_data = get_current_rules()
    if not rules_data:
        print("Failed to fetch current rules")
        return False
    
    rules = rules_data['rules']
    print(f"Current rule count: {len(rules)}")
    
    # Find duplicates
    duplicates = find_duplicate_rules(rules)
    print(f"Found {len(duplicates)} duplicate rule pairs")
    
    if not duplicates:
        print("No duplicates found!")
        return True
    
    # Show duplicates
    for i, (idx1, idx2) in enumerate(duplicates):
        print(f"\nDuplicate pair {i+1}:")
        print(f"  Rule {idx1+1}: Comment='{rules[idx1].get('comment', '')}', Protocol='{rules[idx1].get('protocol', '')}'")
        print(f"  Rule {idx2+1}: Comment='{rules[idx2].get('comment', '')}', Protocol='{rules[idx2].get('protocol', '')}'")
    
    # Remove the last occurrence of each duplicate (keep the first one)
    rules_to_remove = []
    for idx1, idx2 in duplicates:
        rules_to_remove.append(idx2)  # Remove the second occurrence
    
    # Sort in reverse order to maintain correct indices when removing
    rules_to_remove.sort(reverse=True)
    
    # Create new rules list without duplicates
    updated_rules = []
    for i, rule in enumerate(rules):
        if i not in rules_to_remove:
            updated_rules.append(rule)
    
    print(f"\nRules after duplicate removal: {len(updated_rules)}")
    print(f"Removed {len(rules_to_remove)} duplicate rules at positions: {[r+1 for r in rules_to_remove]}")
    
    # Update the firewall rules - FIXED: Use proper API format
    url = f"{BASE_URL}/networks/{NETWORK_ID}/appliance/firewall/l3FirewallRules"
    headers = {
        "X-Cisco-Meraki-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # The API expects {"rules": [...]} format, not just [...]
    payload = {"rules": updated_rules}
    
    try:
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        
        print(f"\n✅ Successfully removed duplicate default rule(s)")
        print(f"Rules count: {len(rules)} -> {len(updated_rules)}")
        
        # Save the updated rules for verification
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"/usr/local/bin/tst01_rules_after_duplicate_removal_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(updated_rules, f, indent=2)
        print(f"Updated rules saved to: {output_file}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error removing duplicate rule: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return False

def main():
    """Main function"""
    print("TST 01 Duplicate Rule Removal - Final Version")
    print("=" * 47)
    print("This script will automatically:")
    print("1. Download current firewall rules")
    print("2. Find duplicate rules (case-insensitive comparison)")
    print("3. Remove duplicate occurrences")
    print("4. Update the firewall rules")
    print()
    
    # First, let's analyze what we'll be removing
    print("Analyzing current rules...")
    rules_data = get_current_rules()
    if not rules_data:
        print("Failed to fetch rules for analysis")
        return 1
    
    rules = rules_data['rules']
    duplicates = find_duplicate_rules(rules)
    
    if not duplicates:
        print("✅ No duplicates found - TST 01 rules are clean!")
        return 0
    
    print(f"Found {len(duplicates)} duplicate rule pair(s):")
    for i, (idx1, idx2) in enumerate(duplicates):
        print(f"\nDuplicate {i+1}:")
        print(f"  Rule {idx1+1}: '{rules[idx1].get('comment', 'No comment')}' - Protocol: '{rules[idx1].get('protocol', 'N/A')}'")
        print(f"  Rule {idx2+1}: '{rules[idx2].get('comment', 'No comment')}' - Protocol: '{rules[idx2].get('protocol', 'N/A')}'")
    
    print(f"\nProceeding with automatic duplicate removal...")
    print(f"Rules count: {len(rules)} -> {len(rules) - len(duplicates)}")
    
    success = remove_duplicate_default_rule()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())