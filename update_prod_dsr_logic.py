#!/usr/bin/env python3
"""
Update production dsrcircuits route to include DSR verification
"""

import re

def update_prod_dsr_logic():
    # Read the blueprint file
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
        content = f.read()
    
    # Find the assign_costs_improved function and update it to track DSR verification
    # First, update where WAN1 cost is assigned
    wan1_pattern = r"wan1_match_info = {'matched': True, 'confidence': confidence}"
    wan1_replacement = """wan1_match_info = {
                    'matched': True, 
                    'confidence': confidence,
                    'dsr_verified': circuit.data_source == 'csv_import'
                }"""
    
    content = re.sub(wan1_pattern, wan1_replacement, content)
    
    # Update where WAN2 cost is assigned
    wan2_pattern = r"wan2_match_info = {'matched': True, 'confidence': confidence}"
    wan2_replacement = """wan2_match_info = {
                    'matched': True, 
                    'confidence': confidence,
                    'dsr_verified': circuit.data_source == 'csv_import'
                }"""
    
    content = re.sub(wan2_pattern, wan2_replacement, content)
    
    # Save the updated file
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
        f.write(content)
    
    print("✅ Updated production route to include DSR verification logic")

if __name__ == "__main__":
    update_prod_dsr_logic()