#!/usr/bin/env python3
"""
Update beta route to properly check DSR verification
"""

import re

def update_beta_dsr_check():
    # Read the file
    with open('/usr/local/bin/Main/dsrcircuits_beta_combined.py', 'r') as f:
        content = f.read()
    
    # Find the part where we set match info for WAN1
    wan1_match_pattern = r"wan1_match_info = {'matched': True, 'confidence': confidence}"
    wan1_replacement = """wan1_match_info = {
                    'matched': True, 
                    'confidence': confidence,
                    'dsr_verified': circuit.data_source == 'csv_import'  # DSR data comes from CSV
                }"""
    
    content = re.sub(wan1_match_pattern, wan1_replacement, content)
    
    # Find the part where we set match info for WAN2
    wan2_match_pattern = r"wan2_match_info = {'matched': True, 'confidence': confidence}"
    wan2_replacement = """wan2_match_info = {
                    'matched': True, 
                    'confidence': confidence,
                    'dsr_verified': circuit.data_source == 'csv_import'  # DSR data comes from CSV
                }"""
    
    content = re.sub(wan2_match_pattern, wan2_replacement, content)
    
    # Save the file
    with open('/usr/local/bin/Main/dsrcircuits_beta_combined.py', 'w') as f:
        f.write(content)
    
    print("✅ Updated beta route to check DSR verification")

if __name__ == "__main__":
    update_beta_dsr_check()