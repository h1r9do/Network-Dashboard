#!/usr/bin/env python3
"""
Apply Filtered AZP 30 Firewall Rules to TST 01
Filters out VLAN references that don't exist in TST 01
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

# VLANs that exist in TST 01
TST01_VLANS = [1, 101, 201, 300, 301, 800, 801, 803, 900]

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
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            log(f"Response: {e.response.text}", "ERROR")
        return None

def filter_vlan_references(cidr_string):
    """Filter out VLAN references that don't exist in TST 01"""
    if not cidr_string or cidr_string == "Any":
        return cidr_string
    
    # Split by comma and process each part
    parts = cidr_string.split(',')
    valid_parts = []
    
    for part in parts:
        part = part.strip()
        
        # Check if this part references a VLAN
        vlan_match = re.search(r'VLAN\((\d+)\)', part)
        if vlan_match:
            vlan_id = int(vlan_match.group(1))
            if vlan_id in TST01_VLANS:
                valid_parts.append(part)
            else:
                log(f"    Filtering out VLAN({vlan_id}) reference (not in TST 01)", "DEBUG")
        else:
            # Not a VLAN reference, keep it
            valid_parts.append(part)
    
    if not valid_parts:
        return "Any"  # If all VLAN references were filtered out
    
    return ','.join(valid_parts)

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

def apply_filtered_firewall():
    """Apply filtered AZP 30 firewall rules to TST 01"""
    tst01_id = "L_3790904986339115852"
    
    log("="*60)
    log("APPLYING FILTERED AZP 30 FIREWALL RULES TO TST 01")
    log("="*60)
    log(f"TST 01 VLANs: {TST01_VLANS}")
    
    # Load AZP 30 firewall rules
    try:
        with open('azp_30_original_firewall_rules.json', 'r') as f:
            azp30_fw = json.load(f)
        
        firewall_rules = azp30_fw['rules']
        log(f"Loaded {len(firewall_rules)} firewall rules from AZP 30")
        
        # Process and filter rules
        filtered_rules = []
        skipped_count = 0
        
        for rule in firewall_rules:
            new_rule = rule.copy()
            rule_comment = rule.get('comment', 'No comment')
            
            # Update and filter source CIDR
            if 'srcCidr' in new_rule and new_rule['srcCidr']:
                src = new_rule['srcCidr']
                # Convert AZP 30 IPs to TST 01 test IPs
                src = src.replace('10.24.', '10.255.255.')
                src = src.replace('10.25.', '10.255.255.')
                src = src.replace('10.26.', '10.255.255.')
                # Filter VLAN references
                src = filter_vlan_references(src)
                # Simplify policy object references
                src = simplify_policy_references(src)
                new_rule['srcCidr'] = src
            
            # Update and filter destination CIDR
            if 'destCidr' in new_rule and new_rule['destCidr']:
                dst = new_rule['destCidr']
                # Convert AZP 30 IPs to TST 01 test IPs
                dst = dst.replace('10.24.', '10.255.255.')
                dst = dst.replace('10.25.', '10.255.255.')
                dst = dst.replace('10.26.', '10.255.255.')
                # Filter VLAN references
                dst = filter_vlan_references(dst)
                # Simplify policy object references
                dst = simplify_policy_references(dst)
                new_rule['destCidr'] = dst
            
            # Skip rules that still have unresolved policy references
            src_check = str(new_rule.get('srcCidr', ''))
            dst_check = str(new_rule.get('destCidr', ''))
            if 'GRP(' in src_check + dst_check or 'OBJ(' in src_check + dst_check:
                log(f"  Skipping rule with unresolved policy objects: {rule_comment}")
                skipped_count += 1
                continue
            
            # Skip rules that became meaningless (e.g., Any -> Any allow rules)
            if (new_rule.get('srcCidr') == 'Any' and 
                new_rule.get('destCidr') == 'Any' and 
                new_rule.get('policy') == 'allow' and
                'default' not in rule_comment.lower()):
                log(f"  Skipping meaningless rule: {rule_comment}")
                skipped_count += 1
                continue
            
            filtered_rules.append(new_rule)
        
        log(f"Processed {len(filtered_rules)} rules ({skipped_count} skipped)")
        
        # Apply firewall rules to TST 01
        log(f"Applying {len(filtered_rules)} filtered firewall rules to TST 01...")
        url = f"{BASE_URL}/networks/{tst01_id}/appliance/firewall/l3FirewallRules"
        result = make_api_request(url, method='PUT', data={'rules': filtered_rules})
        
        if result:
            log(f"✓ Successfully applied {len(filtered_rules)} firewall rules to TST 01")
            
            # Show sample of applied rules
            log("\\nSample of applied rules with legacy VLAN references:")
            vlan_rules_shown = 0
            for i, rule in enumerate(filtered_rules):
                comment = rule.get('comment', 'No comment')
                policy = rule.get('policy', 'allow')
                src = rule.get('srcCidr', 'Any')
                dst = rule.get('destCidr', 'Any')
                
                if 'VLAN(' in src or 'VLAN(' in dst:
                    log(f"  {vlan_rules_shown+1}. [{policy.upper()}] {comment}")
                    log(f"     {src} → {dst}")
                    vlan_rules_shown += 1
                    if vlan_rules_shown >= 8:
                        break
            
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
    log("🔥 Filtered AZP 30 Firewall Rules → TST 01")
    log("This will apply AZP 30's firewall rules filtered for TST 01's VLAN configuration")
    
    if not os.getenv('SKIP_CONFIRMATION'):
        confirm = input("Proceed with applying filtered AZP 30 firewall rules to TST 01? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Operation cancelled.")
            sys.exit(0)
    else:
        print("Skipping confirmation (SKIP_CONFIRMATION set)")
    
    success = apply_filtered_firewall()
    
    if success:
        log("="*60)
        log("✅ FILTERED AZP 30 FIREWALL RULES APPLIED TO TST 01!")
        log("="*60)
        log("TST 01 now has production-complexity firewall rules with legacy VLAN references")
        log("Ready for comprehensive VLAN migration testing")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()