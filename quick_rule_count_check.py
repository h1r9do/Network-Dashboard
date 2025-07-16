#!/usr/bin/env python3
"""
Quick check of TST 01 rule count
"""

import requests
import json
from datetime import datetime

API_KEY = "5174c907a7d57dea6a0788617287c985cc80b3c1"
BASE_URL = "https://api.meraki.com/api/v1"
NETWORK_ID = "L_3790904986339115852"

def check_rule_count():
    """Get current rule count"""
    headers = {
        "X-Cisco-Meraki-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    url = f"{BASE_URL}/networks/{NETWORK_ID}/appliance/firewall/l3FirewallRules"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        rules = data['rules']
        
        print(f"Current TST 01 rule count: {len(rules)}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show last 3 rules
        print("\nLast 3 rules:")
        for i in range(max(0, len(rules) - 3), len(rules)):
            rule = rules[i]
            print(f"Rule {i+1}: '{rule.get('comment', '')}' - Protocol: '{rule.get('protocol', '')}'")
        
        return len(rules)
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching rules: {e}")
        return None

if __name__ == "__main__":
    check_rule_count()