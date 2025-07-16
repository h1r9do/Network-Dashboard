#!/usr/bin/env python3
"""
Apply Simplified AZP 30 Firewall Rules to TST 01
Applies firewall rules but removes policy object references that don't exist in test environment
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
import re

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

def simplify_policy_references(cidr_string):
    """Replace policy object references with simplified equivalents"""
    if not cidr_string or cidr_string == "Any":
        return cidr_string
    
    # Replace specific policy objects with generic equivalents for testing
    replacements = {
        # Replace policy groups with generic IP ranges
        'GRP(3790904986339115076)': '13.107.64.0/18,52.112.0.0/14',  # MS Teams/Office365
        'GRP(3790904986339115077)': '10.0.0.0/8',  # PBX systems  
        'GRP(3790904986339115118)': '199.71.106.0/20',  # Payment processing
        
        # Replace network objects with specific IPs
        'OBJ(3790904986339115064)': '74.125.224.0/19',  # Google services
        'OBJ(3790904986339115065)': '173.194.0.0/16',   # Google services
        'OBJ(3790904986339115066)': '108.177.8.0/21',   # Google services  
        'OBJ(3790904986339115067)': '142.250.0.0/15',   # Google services
        'OBJ(3790904986339115074)': 'time.windows.com',  # NTP servers
    }
    
    result = cidr_string
    for obj_ref, replacement in replacements.items():
        result = result.replace(obj_ref, replacement)
    
    return result

def apply_simplified_firewall():
    """Apply simplified AZP 30 firewall rules to TST 01"""
    tst01_id = "L_3790904986339115852"
    
    log("="*60)
    log("APPLYING SIMPLIFIED AZP 30 FIREWALL RULES TO TST 01")
    log("="*60)
    
    # Load AZP 30 firewall rules
    try:
        with open('azp_30_original_firewall_rules.json', 'r') as f:
            azp30_fw = json.load(f)
        
        firewall_rules = azp30_fw['rules']
        log(f"Loaded {len(firewall_rules)} firewall rules from AZP 30")
        
        # Process and simplify rules
        simplified_rules = []
        skipped_count = 0
        
        for rule in firewall_rules:
            new_rule = rule.copy()
            
            # Update source CIDR for TST 01 IP ranges and simplify policy objects
            if 'srcCidr' in new_rule and new_rule['srcCidr']:
                src = new_rule['srcCidr']
                # Convert AZP 30 IPs to TST 01 test IPs
                src = src.replace('10.24.', '10.255.255.')
                src = src.replace('10.25.', '10.255.255.')
                src = src.replace('10.26.', '10.255.255.')
                # Simplify policy object references
                src = simplify_policy_references(src)
                new_rule['srcCidr'] = src
            
            # Update destination CIDR for TST 01 IP ranges and simplify policy objects
            if 'destCidr' in new_rule and new_rule['destCidr']:
                dst = new_rule['destCidr']
                # Convert AZP 30 IPs to TST 01 test IPs
                dst = dst.replace('10.24.', '10.255.255.')
                dst = dst.replace('10.25.', '10.255.255.')
                dst = dst.replace('10.26.', '10.255.255.')
                # Simplify policy object references
                dst = simplify_policy_references(dst)
                new_rule['destCidr'] = dst
            
            # Skip rules that still have unresolved policy references
            src_check = str(new_rule.get('srcCidr', ''))
            dst_check = str(new_rule.get('destCidr', ''))
            if 'GRP(' in src_check + dst_check or 'OBJ(' in src_check + dst_check:
                log(f"  Skipping rule with unresolved policy objects: {rule.get('comment', 'No comment')}")
                skipped_count += 1
                continue
            
            simplified_rules.append(new_rule)
        
        log(f"Processed {len(simplified_rules)} rules ({skipped_count} skipped due to policy objects)")
        
        # Apply firewall rules to TST 01
        log(f"Applying {len(simplified_rules)} simplified firewall rules to TST 01...")
        url = f"{BASE_URL}/networks/{tst01_id}/appliance/firewall/l3FirewallRules"
        result = make_api_request(url, method='PUT', data={'rules': simplified_rules})
        
        if result:
            log(f"✓ Successfully applied {len(simplified_rules)} firewall rules to TST 01")
            
            # Show sample of applied rules
            log("\\nSample of applied rules with legacy VLAN references:")
            for i, rule in enumerate(simplified_rules[:10]):
                comment = rule.get('comment', 'No comment')
                policy = rule.get('policy', 'allow')
                src = rule.get('srcCidr', 'Any')
                dst = rule.get('destCidr', 'Any')
                log(f"  {i+1}. [{policy.upper()}] {comment}")
                if 'VLAN(' in src or 'VLAN(' in dst:
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
    log("🔥 Simplified AZP 30 Firewall Rules → TST 01")
    log("This will apply AZP 30's production firewall structure with simplified policy objects")
    
    if not os.getenv('SKIP_CONFIRMATION'):
        confirm = input("Proceed with applying simplified AZP 30 firewall rules to TST 01? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Operation cancelled.")
            sys.exit(0)
    else:
        print("Skipping confirmation (SKIP_CONFIRMATION set)")
    
    success = apply_simplified_firewall()
    
    if success:
        log("="*60)
        log("✅ SIMPLIFIED AZP 30 FIREWALL RULES APPLIED TO TST 01!")
        log("="*60)
        log("TST 01 now has production-like firewall rules with legacy VLAN references")
        log("Ready for VLAN migration testing with complex firewall rule updates")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()