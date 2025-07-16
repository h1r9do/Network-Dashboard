#!/usr/bin/env python3
"""
TST 01 Firewall Rules Analysis Script
Purpose: Download and analyze firewall rules from TST 01 to identify duplicate default rule
Network ID: L_3790904986339115852
"""

import requests
import json
from datetime import datetime

# Meraki API Configuration
API_KEY = "5174c907a7d57dea6a0788617287c985cc80b3c1"
BASE_URL = "https://api.meraki.com/api/v1"
NETWORK_ID = "L_3790904986339115852"  # TST 01

def get_firewall_rules():
    """Fetch current firewall rules from TST 01"""
    url = f"{BASE_URL}/networks/{NETWORK_ID}/appliance/firewall/l3FirewallRules"
    headers = {
        "X-Cisco-Meraki-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        # Extract rules from the response
        rules = data.get('rules', [])
        print(f"Successfully fetched {len(rules)} firewall rules from TST 01")
        return rules
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching firewall rules: {e}")
        return None

def analyze_rules(rules):
    """Analyze rules to identify duplicate default rules"""
    if not rules:
        return
    
    print(f"\n=== TST 01 Firewall Rules Analysis ===")
    print(f"Total rules: {len(rules)}")
    print(f"Timestamp: {datetime.now()}")
    
    # Look for default rules (typically at the end)
    default_rules = []
    for i, rule in enumerate(rules):
        # Default rules typically have policy "deny" and comment "Default rule"
        if (rule.get('comment', '').lower() == 'default rule' or 
            rule.get('policy') == 'deny' and 
            rule.get('srcCidr') == 'any' and 
            rule.get('destCidr') == 'any'):
            default_rules.append((i, rule))
    
    print(f"\nFound {len(default_rules)} potential default rules:")
    for i, (index, rule) in enumerate(default_rules):
        print(f"  Rule {index + 1}: {rule}")
    
    # Show last 5 rules for context
    print(f"\nLast 5 rules (likely including default rules):")
    for i, rule in enumerate(rules[-5:], start=len(rules)-4):
        print(f"  Rule {i}: {rule}")
    
    return default_rules

def create_removal_script(rules, default_rules):
    """Create script to remove duplicate default rule"""
    if len(default_rules) <= 1:
        print("\nNo duplicate default rules found.")
        return
    
    print(f"\n=== Duplicate Default Rule Removal ===")
    print(f"Found {len(default_rules)} default rules - need to remove {len(default_rules) - 1}")
    
    # Create script to remove the extra default rule(s)
    # Keep the last default rule, remove earlier ones
    rules_to_remove = default_rules[:-1]  # All but the last one
    
    # Create updated rules list (remove all but the last default rule)
    updated_rules = rules[:-len(default_rules)] + [default_rules[-1][1]]
    
    script_content = f'''#!/usr/bin/env python3
"""
Remove duplicate default rule from TST 01
Generated on: {datetime.now()}
Rules: {len(rules)} -> {len(updated_rules)}
"""

import requests
import json

API_KEY = "{API_KEY}"
BASE_URL = "{BASE_URL}"
NETWORK_ID = "{NETWORK_ID}"

def remove_duplicate_default_rule():
    """Remove the duplicate default rule from TST 01"""
    # Updated rules with duplicate removed
    updated_rules = {json.dumps(updated_rules, indent=2)}
    
    url = f"{{BASE_URL}}/networks/{{NETWORK_ID}}/appliance/firewall/l3FirewallRules"
    headers = {{
        "X-Cisco-Meraki-API-Key": API_KEY,
        "Content-Type": "application/json"
    }}
    
    try:
        response = requests.put(url, headers=headers, json=updated_rules)
        response.raise_for_status()
        
        print("Successfully removed duplicate default rule")
        print(f"Rules count: {len(rules)} -> {{len(updated_rules)}}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error removing duplicate rule: {{e}}")
        return False

if __name__ == "__main__":
    print("WARNING: This will modify TST 01 firewall rules!")
    print("This will remove 1 duplicate default rule")
    print(f"Current rules: {len(rules)}")
    print(f"After removal: {len(updated_rules)}")
    confirm = input("Type 'YES' to proceed: ")
    if confirm == 'YES':
        remove_duplicate_default_rule()
    else:
        print("Operation cancelled.")
'''
    
    # Save the removal script
    with open('/usr/local/bin/remove_tst01_duplicate_rule.py', 'w') as f:
        f.write(script_content)
    
    print("Created removal script: /usr/local/bin/remove_tst01_duplicate_rule.py")
    print("Review the script before running it!")

def main():
    print("Fetching firewall rules from TST 01...")
    rules = get_firewall_rules()
    
    if rules:
        # Save full rules to file for reference
        with open('/usr/local/bin/tst01_firewall_rules.json', 'w') as f:
            json.dump(rules, f, indent=2)
        print(f"Saved complete rules to: /usr/local/bin/tst01_firewall_rules.json")
        
        # Analyze rules
        default_rules = analyze_rules(rules)
        
        # Create removal script if needed
        if default_rules:
            create_removal_script(rules, default_rules)
    
    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()