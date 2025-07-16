#!/usr/bin/env python3
"""
Apply AZP 30 Firewall Rules to TST 01
Copies the complete production firewall rules from AZP 30 to TST 01
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def log(message, level="INFO"):
    """Log a message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def make_api_request(url, method='GET', data=None):
    """Make API request with error handling"""
    try:
        if method == 'GET':
            response = requests.get(url, headers=HEADERS, timeout=30)
        elif method == 'PUT':
            response = requests.put(url, headers=HEADERS, json=data, timeout=30)
        
        response.raise_for_status()
        return response.json() if response.text else None
    except requests.exceptions.RequestException as e:
        log(f"API Error: {e}", "ERROR")
        return None

def apply_azp30_firewall_to_tst01():
    """Apply AZP 30 firewall rules to TST 01"""
    tst01_id = "L_3790904986339115852"
    
    log("="*60)
    log("APPLYING AZP 30 FIREWALL RULES TO TST 01")
    log("="*60)
    
    # Load AZP 30 firewall rules
    try:
        with open('azp_30_original_firewall_rules.json', 'r') as f:
            azp30_fw = json.load(f)
        
        firewall_rules = azp30_fw['rules']
        log(f"Loaded {len(firewall_rules)} firewall rules from AZP 30")
        
        # Update rules for TST 01 IP ranges (10.255.255.x instead of 10.24.XX.x)
        updated_rules = []
        for rule in firewall_rules:
            new_rule = rule.copy()
            
            # Update source CIDR for TST 01 IP ranges
            if 'srcCidr' in new_rule and new_rule['srcCidr']:
                src = new_rule['srcCidr']
                # Convert AZP 30 IPs to TST 01 test IPs
                src = src.replace('10.24.', '10.255.255.')
                src = src.replace('10.25.', '10.255.255.')
                src = src.replace('10.26.', '10.255.255.')
                new_rule['srcCidr'] = src
            
            # Update destination CIDR for TST 01 IP ranges
            if 'destCidr' in new_rule and new_rule['destCidr']:
                dst = new_rule['destCidr']
                # Convert AZP 30 IPs to TST 01 test IPs
                dst = dst.replace('10.24.', '10.255.255.')
                dst = dst.replace('10.25.', '10.255.255.')
                dst = dst.replace('10.26.', '10.255.255.')
                new_rule['destCidr'] = dst
            
            updated_rules.append(new_rule)
        
        # Apply firewall rules to TST 01
        log(f"Applying {len(updated_rules)} firewall rules to TST 01...")
        url = f"{BASE_URL}/networks/{tst01_id}/appliance/firewall/l3FirewallRules"
        result = make_api_request(url, method='PUT', data={'rules': updated_rules})
        
        if result:
            log(f"✓ Successfully applied {len(updated_rules)} firewall rules to TST 01")
            
            # Show sample of applied rules
            log("\\nSample of applied rules:")
            for i, rule in enumerate(updated_rules[:5]):
                comment = rule.get('comment', 'No comment')
                policy = rule.get('policy', 'allow')
                src = rule.get('srcCidr', 'Any')
                dst = rule.get('destCidr', 'Any')
                log(f"  {i+1}. [{policy.upper()}] {comment}")
                log(f"     {src} → {dst}")
            
            return True
        else:
            log("✗ Failed to apply firewall rules", "ERROR")
            return False
            
    except FileNotFoundError:
        log("AZP 30 firewall rules file not found", "ERROR")
        return False
    except Exception as e:
        log(f"Error applying firewall rules: {e}", "ERROR")
        return False

def main():
    log("🔥 AZP 30 Firewall Rules → TST 01")
    log("This will replace TST 01's firewall rules with AZP 30's production rules")
    
    if not os.getenv('SKIP_CONFIRMATION'):
        confirm = input("Proceed with applying AZP 30 firewall rules to TST 01? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Operation cancelled.")
            sys.exit(0)
    else:
        print("Skipping confirmation (SKIP_CONFIRMATION set)")
    
    success = apply_azp30_firewall_to_tst01()
    
    if success:
        log("="*60)
        log("✅ AZP 30 FIREWALL RULES APPLIED TO TST 01!")
        log("="*60)
        log("TST 01 now has complete production firewall rules for testing")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()