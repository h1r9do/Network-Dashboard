#!/usr/bin/env python3
"""
Restore original column sizing and adjust filters to match
"""

import re

def restore_original_layout():
    # Read the template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'r') as f:
        content = f.read()
    
    # Restore the original table CSS (remove table-layout: fixed)
    table_css = r'\.circuit-table\s*\{[^}]*\}'
    original_table_css = '''        .circuit-table {
            width: 100%;
            border-collapse: collapse;
        }'''
    
    content = re.sub(table_css, original_table_css, content, flags=re.DOTALL)
    
    # Restore the original filter controls to use grid layout with 8 columns
    filter_css = r'\.filter-controls\s*\{[^}]*\}'
    original_filter_css = '''        .filter-controls {
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            gap: 5px;
            margin-bottom: 10px;
        }'''
    
    content = re.sub(filter_css, original_filter_css, content, flags=re.DOTALL)
    
    # Update the filter-control CSS to the original style
    filter_control_css = r'\.filter-control\s*\{[^}]*\}'
    original_filter_control_css = '''        .filter-control {
            padding: 5px;
        }'''
    
    content = re.sub(filter_control_css, original_filter_control_css, content, flags=re.DOTALL)
    
    # Save the updated template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'w') as f:
        f.write(content)
    
    print("✅ Restored original column sizing")
    print("✅ Updated filters to use 8-column grid layout to match table")

if __name__ == "__main__":
    restore_original_layout()