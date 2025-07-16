#!/usr/bin/env python3
"""
Debug version to understand why the rule update is failing
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

def test_rule_update():
    """Test updating rules to identify the issue"""
    
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
        print(f"Rule {i+1}: {rule}")
    
    # Create a simple test - just remove the last rule
    print(f"\nTesting removal of rule {len(rules)} (last rule)")
    test_rules = rules[:-1]  # Remove the last rule
    
    print(f"Original rules: {len(rules)}")
    print(f"Test rules: {len(test_rules)}")
    
    # Try to update with the test rules
    url = f"{BASE_URL}/networks/{NETWORK_ID}/appliance/firewall/l3FirewallRules"
    headers = {
        "X-Cisco-Meraki-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        print("\nAttempting to update rules...")
        response = requests.put(url, headers=headers, json=test_rules)
        
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
        
        if response.status_code != 200:
            print(f"❌ Update failed with status {response.status_code}")
            
            # Try to parse the error message
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print("Could not parse error response as JSON")
                
            return False
        else:
            print("✅ Test update succeeded!")
            
            # Immediately restore the original rules
            print("Restoring original rules...")
            restore_response = requests.put(url, headers=headers, json=rules)
            if restore_response.status_code == 200:
                print("✅ Original rules restored")
            else:
                print(f"❌ Failed to restore original rules: {restore_response.status_code}")
                
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error during test update: {e}")
        return False

def main():
    """Main function"""
    print("TST 01 Rule Update Debug Tool")
    print("=" * 35)
    print("This script will:")
    print("1. Download current firewall rules")
    print("2. Test a simple rule removal")
    print("3. Show detailed error information if it fails")
    print("4. Restore original rules if test succeeds")
    print()
    
    success = test_rule_update()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())