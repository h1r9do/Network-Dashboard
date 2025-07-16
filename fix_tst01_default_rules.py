#!/usr/bin/env python3
"""
Fix TST 01 default rules by making one distinct before removal
Strategy: Change one duplicate to have a unique comment, then remove it
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

def fix_default_rules():
    """Fix default rules by making one unique then removing it"""
    
    # Get current rules
    print("Fetching current rules...")
    rules_data = get_current_rules()
    if not rules_data:
        print("Failed to fetch current rules")
        return False
    
    rules = rules_data['rules']
    print(f"Current rule count: {len(rules)}")
    
    # Show the last few rules
    print("\nLast 3 rules:")
    for i in range(max(0, len(rules) - 3), len(rules)):
        rule = rules[i]
        print(f"Rule {i+1}: '{rule.get('comment', '')}' - Protocol: '{rule.get('protocol', '')}'")
    
    # Strategy 1: Try to modify the last rule to make it distinct, then remove it
    print(f"\nStep 1: Making rule {len(rules)} unique...")
    
    # Modify the last rule to have a unique comment
    modified_rules = rules.copy()
    modified_rules[-1] = modified_rules[-1].copy()  # Make a copy to avoid modifying original
    modified_rules[-1]['comment'] = 'TEMP DUPLICATE FOR REMOVAL'
    
    # Update with the modified rules (making the duplicate distinct)
    url = f"{BASE_URL}/networks/{NETWORK_ID}/appliance/firewall/l3FirewallRules"
    headers = {
        "X-Cisco-Meraki-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {"rules": modified_rules}
    
    try:
        print("Updating last rule to make it distinct...")
        response = requests.put(url, headers=headers, json=payload)
        response.raise_for_status()
        print("✅ Successfully made last rule distinct")
        
        # Now remove the last rule (which is now unique)
        print("\nStep 2: Removing the now-unique last rule...")
        final_rules = modified_rules[:-1]  # Remove the last rule
        
        final_payload = {"rules": final_rules}
        
        response = requests.put(url, headers=headers, json=final_payload)
        response.raise_for_status()
        
        print(f"✅ Successfully removed duplicate rule")
        print(f"Rules count: {len(rules)} -> {len(final_rules)}")
        
        # Save the final rules for verification
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"/usr/local/bin/tst01_rules_fixed_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(final_rules, f, indent=2)
        print(f"Final rules saved to: {output_file}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error during rule modification: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return False

def verify_fix():
    """Verify the fix worked"""
    print("\nVerifying the fix...")
    rules_data = get_current_rules()
    if rules_data:
        rules = rules_data['rules']
        print(f"Current rule count after fix: {len(rules)}")
        
        # Show last 3 rules
        print("\nLast 3 rules after fix:")
        for i in range(max(0, len(rules) - 3), len(rules)):
            rule = rules[i]
            print(f"Rule {i+1}: '{rule.get('comment', '')}' - Protocol: '{rule.get('protocol', '')}'")
        
        # Check for duplicates
        last_3_comments = [rules[i].get('comment', '') for i in range(max(0, len(rules) - 3), len(rules))]
        if 'Default rule' in last_3_comments:
            count = last_3_comments.count('Default rule')
            if count > 1:
                print(f"❌ Still have {count} 'Default rule' entries")
                return False
            else:
                print("✅ Only one 'Default rule' entry remains")
                return True
        else:
            print("✅ No 'Default rule' duplicates found")
            return True
    
    return False

def main():
    """Main function"""
    print("TST 01 Default Rule Fix Tool")
    print("=" * 32)
    print("This script will:")
    print("1. Make the duplicate default rule unique")
    print("2. Remove the now-unique duplicate")
    print("3. Verify the fix worked")
    print()
    
    success = fix_default_rules()
    if success:
        verify_fix()
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit(main())