#!/usr/bin/env python3
"""
Create Clean NEO 07 Template
Downloads current NEO 07 rules and creates a clean template with policy objects replaced
"""

import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv("MERAKI_API_KEY")
HEADERS = {'X-Cisco-Meraki-API-Key': API_KEY}

def download_neo07_rules():
    """Download current NEO 07 firewall rules"""
    neo07_id = 'L_3790904986339115847'
    url = f'https://api.meraki.com/api/v1/networks/{neo07_id}/appliance/firewall/l3FirewallRules'
    
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def create_clean_template():
    """Create clean template with policy objects resolved"""
    print('📥 Downloading current NEO 07 firewall rules...')
    
    neo07_data = download_neo07_rules()
    rules = neo07_data['rules']
    
    print(f'Downloaded {len(rules)} rules from NEO 07')
    
    # Policy object replacements
    policy_replacements = {
        'GRP(3790904986339115076)': '13.107.64.0/18,52.112.0.0/14',  # MS Teams/Office365
        'GRP(3790904986339115077)': '10.0.0.0/8',  # PBX systems
        'GRP(3790904986339115118)': '199.71.106.0/20',  # Payment processing
        'GRP(3790904986339115043)': '198.252.230.155/32',  # EPX specific
        'OBJ(3790904986339115064)': '74.125.224.0/19',  # Google services
        'OBJ(3790904986339115065)': '173.194.0.0/16',   # Google services
        'OBJ(3790904986339115066)': '108.177.8.0/21',   # Google services
        'OBJ(3790904986339115067)': '142.250.0.0/15',   # Google services
        'OBJ(3790904986339115074)': 'time.windows.com',  # NTP servers
    }
    
    print('🔧 Processing rules and replacing policy objects...')
    
    clean_rules = []
    skipped_count = 0
    replaced_count = 0
    
    for i, rule in enumerate(rules):
        clean_rule = rule.copy()
        rule_modified = False
        
        # Process source CIDR
        if 'srcCidr' in clean_rule and clean_rule['srcCidr']:
            original_src = clean_rule['srcCidr']
            for obj_ref, replacement in policy_replacements.items():
                if obj_ref in clean_rule['srcCidr']:
                    clean_rule['srcCidr'] = clean_rule['srcCidr'].replace(obj_ref, replacement)
                    rule_modified = True
        
        # Process destination CIDR
        if 'destCidr' in clean_rule and clean_rule['destCidr']:
            original_dst = clean_rule['destCidr']
            for obj_ref, replacement in policy_replacements.items():
                if obj_ref in clean_rule['destCidr']:
                    clean_rule['destCidr'] = clean_rule['destCidr'].replace(obj_ref, replacement)
                    rule_modified = True
        
        # Check if there are still unresolved policy objects
        src_check = str(clean_rule.get('srcCidr', ''))
        dst_check = str(clean_rule.get('destCidr', ''))
        
        if 'GRP(' in src_check + dst_check or 'OBJ(' in src_check + dst_check:
            print(f'  Skipping rule {i+1} with unresolved policy objects: {rule.get("comment", "No comment")}')
            skipped_count += 1
            continue
        
        if rule_modified:
            replaced_count += 1
            print(f'  Replaced policy objects in rule {i+1}: {rule.get("comment", "No comment")}')
        
        clean_rules.append(clean_rule)
    
    print(f'\\n✅ Processing complete:')
    print(f'  Original rules: {len(rules)}')
    print(f'  Clean rules: {len(clean_rules)}')
    print(f'  Policy objects replaced: {replaced_count}')
    print(f'  Rules skipped: {skipped_count}')
    
    # Create clean template
    clean_template = {
        'creation_date': datetime.now().isoformat(),
        'source': 'NEO 07 live rules with policy objects resolved',
        'description': 'Clean NEO 07 firewall template for migration use',
        'total_rules': len(clean_rules),
        'rules': clean_rules
    }
    
    # Save clean template
    filename = f'neo07_clean_template_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(filename, 'w') as f:
        json.dump(clean_template, f, indent=2)
    
    print(f'\\n📁 Clean template saved: {filename}')
    
    # Show first 5 rules for verification
    print(f'\\n📋 First 5 rules in clean template:')
    for i, rule in enumerate(clean_rules[:5]):
        print(f'{i+1}. [{rule.get("policy", "unknown").upper()}] {rule.get("comment", "No comment")}')
    
    return filename

if __name__ == '__main__':
    create_clean_template()