#!/usr/bin/env python3
"""
Create 54-rule template by removing the default rule from clean template
This lets Meraki auto-add the final default rule to get exactly 55 rules
"""

import json
from datetime import datetime

def create_54_rule_template():
    """Create template with 54 rules (no default rule)"""
    print('📝 Creating 54-rule NEO 07 template (no default rule)')
    print('=' * 60)
    
    # Load the clean 55-rule template
    with open('neo07_clean_template_20250710_102140.json', 'r') as f:
        clean_template = json.load(f)
    
    rules = clean_template['rules']
    print(f'Original template: {len(rules)} rules')
    print(f'Last rule: {rules[-1]["comment"]} - {rules[-1]["policy"]}')
    
    # Remove the last rule (Default rule)
    if rules[-1]['comment'] == 'Default rule':
        rules = rules[:-1]
        print(f'Removed default rule. New count: {len(rules)} rules')
    else:
        print('⚠️  Last rule is not a default rule!')
        return None
    
    # Create new template
    new_template = {
        'creation_date': datetime.now().isoformat(),
        'source': 'NEO 07 clean template with default rule removed',
        'description': 'NEO 07 firewall template without default rule (54 rules) - lets Meraki auto-add final default',
        'total_rules': len(rules),
        'rules': rules
    }
    
    # Save template
    filename = f'neo07_54_rule_template_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(filename, 'w') as f:
        json.dump(new_template, f, indent=2)
    
    print(f'✅ Created 54-rule template: {filename}')
    print(f'Rules: {len(rules)} (Meraki will auto-add default rule to make 55)')
    
    return filename

if __name__ == '__main__':
    create_54_rule_template()