#!/usr/bin/env python3
"""
Prepare NEO 07 Firewall Template for VLAN Migration
===================================================

This script extracts firewall rules from NEO 07 and creates a template
with updated VLAN references for use after VLAN number migration.

Usage:
    python3 prepare_neo07_firewall_template.py [--output-file <filename>]

Author: Claude
Date: July 2025
"""

import os
import json
import requests
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv('/usr/local/bin/meraki.env')
API_KEY = os.getenv('MERAKI_API_KEY')
BASE_URL = 'https://api.meraki.com/api/v1'
HEADERS = {'X-Cisco-Meraki-API-Key': API_KEY, 'Content-Type': 'application/json'}

# NEO 07 network ID
NEO_07_NETWORK_ID = 'L_3790904986339115847'

# VLAN mapping
VLAN_MAPPING = {
    1: 100,    # Data
    101: 200,  # Voice
    201: 400,  # Credit Card
    301: 410,  # Scanner
    # These remain the same:
    300: 300,  # AP Mgmt
    800: 800,  # Guest
    801: 801,  # IOT
    802: 802,  # IoT Network
    803: 803,  # IoT Wireless
}

def extract_neo07_rules():
    """Extract firewall rules from NEO 07"""
    print(f"Extracting firewall rules from NEO 07...")
    
    url = f"{BASE_URL}/networks/{NEO_07_NETWORK_ID}/appliance/firewall/l3FirewallRules"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        result = response.json()
        rules = result.get('rules', [])
        print(f"✅ Extracted {len(rules)} firewall rules from NEO 07")
        return rules
    else:
        print(f"❌ Failed to get firewall rules: {response.status_code}")
        return None

def update_vlan_references(rules):
    """Update VLAN references in firewall rules"""
    print("\nUpdating VLAN references...")
    
    updated_rules = []
    changes_made = 0
    
    for i, rule in enumerate(rules):
        new_rule = rule.copy()
        rule_changed = False
        
        # Update source VLAN references
        if 'srcCidr' in new_rule:
            original_src = new_rule['srcCidr']
            src = original_src
            
            for old_id, new_id in VLAN_MAPPING.items():
                if old_id != new_id:
                    old_pattern = f'VLAN({old_id}).'
                    new_pattern = f'VLAN({new_id}).'
                    if old_pattern in src:
                        src = src.replace(old_pattern, new_pattern)
                        rule_changed = True
            
            new_rule['srcCidr'] = src
            
            if rule_changed and original_src != src:
                print(f"  Rule {i+1}: Updated source")
                print(f"    From: {original_src}")
                print(f"    To:   {src}")
        
        # Update destination VLAN references
        if 'destCidr' in new_rule:
            original_dst = new_rule['destCidr']
            dst = original_dst
            
            for old_id, new_id in VLAN_MAPPING.items():
                if old_id != new_id:
                    old_pattern = f'VLAN({old_id}).'
                    new_pattern = f'VLAN({new_id}).'
                    if old_pattern in dst:
                        dst = dst.replace(old_pattern, new_pattern)
                        rule_changed = True
            
            new_rule['destCidr'] = dst
            
            if rule_changed and original_dst != dst:
                print(f"  Rule {i+1}: Updated destination")
                print(f"    From: {original_dst}")
                print(f"    To:   {dst}")
        
        if rule_changed:
            changes_made += 1
        
        updated_rules.append(new_rule)
    
    print(f"\n✅ Updated {changes_made} rules with new VLAN references")
    return updated_rules

def analyze_vlan_usage(rules):
    """Analyze VLAN usage in firewall rules"""
    print("\nAnalyzing VLAN usage in firewall rules...")
    
    vlan_usage = {}
    
    for rule in rules:
        # Check source
        src = rule.get('srcCidr', '')
        for vlan_id in VLAN_MAPPING.keys():
            if f'VLAN({vlan_id}).' in src:
                vlan_usage[vlan_id] = vlan_usage.get(vlan_id, 0) + 1
        
        # Check destination
        dst = rule.get('destCidr', '')
        for vlan_id in VLAN_MAPPING.keys():
            if f'VLAN({vlan_id}).' in dst:
                vlan_usage[vlan_id] = vlan_usage.get(vlan_id, 0) + 1
    
    print("\nVLAN usage in firewall rules:")
    for vlan_id in sorted(vlan_usage.keys()):
        new_id = VLAN_MAPPING.get(vlan_id, vlan_id)
        change = f" → {new_id}" if vlan_id != new_id else " (no change)"
        print(f"  VLAN {vlan_id}{change}: {vlan_usage[vlan_id]} references")

def save_templates(original_rules, updated_rules, output_file):
    """Save both original and updated firewall templates"""
    # Save original rules
    original_file = output_file.replace('.json', '_original.json')
    with open(original_file, 'w') as f:
        json.dump({'rules': original_rules}, f, indent=2)
    print(f"\n✅ Original rules saved to: {original_file}")
    
    # Save updated rules
    with open(output_file, 'w') as f:
        json.dump({'rules': updated_rules}, f, indent=2)
    print(f"✅ Updated rules saved to: {output_file}")
    
    # Create documentation
    doc_file = output_file.replace('.json', '_documentation.md')
    with open(doc_file, 'w') as f:
        f.write(f"""# NEO 07 Firewall Template Documentation

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Source Network:** NEO 07 ({NEO_07_NETWORK_ID})  
**Total Rules:** {len(original_rules)}

## VLAN Mapping Applied

| Original VLAN | New VLAN | Purpose |
|--------------|----------|---------|
| 1 | 100 | Data |
| 101 | 200 | Voice |
| 201 | 400 | Credit Card |
| 301 | 410 | Scanner |
| 300 | 300 | AP Mgmt (no change) |
| 800-803 | 800-803 | Guest/IoT (no change) |

## Files Generated

1. **{original_file}** - Original NEO 07 firewall rules
2. **{output_file}** - Updated rules with new VLAN IDs
3. **{doc_file}** - This documentation

## Usage

After completing VLAN migration, apply the updated firewall rules:

```bash
# Apply updated firewall rules
curl -X PUT \\
  https://api.meraki.com/api/v1/networks/YOUR_NETWORK_ID/appliance/firewall/l3FirewallRules \\
  -H 'X-Cisco-Meraki-API-Key: YOUR_API_KEY' \\
  -H 'Content-Type: application/json' \\
  -d @{output_file}
```

## Important Notes

- These rules are from NEO 07 and represent the standard store firewall configuration
- Apply these rules AFTER completing VLAN number migration
- The rules maintain all original policies, just with updated VLAN references
""")
    print(f"✅ Documentation saved to: {doc_file}")

def main():
    parser = argparse.ArgumentParser(description='Prepare NEO 07 firewall template')
    parser.add_argument('--output-file', 
                       default=f'neo07_firewall_template_{datetime.now().strftime("%Y%m%d")}.json',
                       help='Output filename for updated rules')
    
    args = parser.parse_args()
    
    print("🔧 NEO 07 Firewall Template Preparation")
    print("=" * 60)
    
    # Extract rules
    original_rules = extract_neo07_rules()
    if not original_rules:
        return
    
    # Analyze usage
    analyze_vlan_usage(original_rules)
    
    # Update VLAN references
    updated_rules = update_vlan_references(original_rules)
    
    # Save templates
    save_templates(original_rules, updated_rules, args.output_file)
    
    print("\n✅ Firewall template preparation complete!")
    print("\nNext steps:")
    print("1. Complete VLAN number migration")
    print("2. Apply the updated firewall rules")

if __name__ == "__main__":
    main()