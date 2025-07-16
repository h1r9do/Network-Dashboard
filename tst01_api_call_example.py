#!/usr/bin/env python3
"""
TST 01 Firewall API Call Example
Shows the exact API calls needed to remove the duplicate default rule
"""

import requests
import json

# Configuration
API_KEY = "5174c907a7d57dea6a0788617287c985cc80b3c1"
BASE_URL = "https://api.meraki.com/api/v1"
NETWORK_ID = "L_3790904986339115852"  # TST 01

# Headers for API calls
headers = {
    "X-Cisco-Meraki-API-Key": API_KEY,
    "Content-Type": "application/json"
}

print("TST 01 Firewall Rules API Calls")
print("=" * 50)

# 1. GET current rules
print("1. GET current rules:")
get_url = f"{BASE_URL}/networks/{NETWORK_ID}/appliance/firewall/l3FirewallRules"
print(f"   URL: {get_url}")
print(f"   Headers: {headers}")
print()

# 2. PUT updated rules (example)
print("2. PUT updated rules (to remove duplicate):")
put_url = f"{BASE_URL}/networks/{NETWORK_ID}/appliance/firewall/l3FirewallRules"
print(f"   URL: {put_url}")
print(f"   Headers: {headers}")
print("   Body: {'rules': [array of 55 rules with duplicate removed]}")
print()

# Show the specific duplicate rules identified
print("3. Duplicate Default Rules Found:")
print("   Rule 55: {'comment': 'Default rule', 'policy': 'allow', 'protocol': 'any', ...}")
print("   Rule 56: {'comment': 'Default rule', 'policy': 'allow', 'protocol': 'Any', ...}")
print("   ^^ Only difference is protocol case: 'any' vs 'Any'")
print()

print("4. Action Required:")
print("   - Remove Rule 55 (keep Rule 56)")
print("   - Final count: 56 -> 55 rules")
print("   - This will match NEO 07's rule count")
print()

# Manual curl example
print("5. Manual curl command (if preferred):")
print("   curl -X PUT \\")
print(f"     '{put_url}' \\")
print(f"     -H 'X-Cisco-Meraki-API-Key: {API_KEY}' \\")
print("     -H 'Content-Type: application/json' \\")
print("     -d '{\"rules\": [... array of 55 rules ...]}' ")
print()

print("Use the main removal script: /usr/local/bin/remove_tst01_duplicate_default_rule.py")
print("Or run this to see the exact API calls needed.")