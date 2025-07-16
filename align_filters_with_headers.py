#!/usr/bin/env python3
"""
Align filter controls with their corresponding table column headers
"""

import re

def align_filters_with_headers():
    # Read the template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'r') as f:
        content = f.read()
    
    # Replace the filter-controls CSS to align with table columns
    # Instead of equal grid, we'll use the same width structure as the table
    old_css = r'\.filter-controls\s*\{[^}]*\}'
    new_css = '''        .filter-controls {
            display: table;
            table-layout: fixed;
            width: 100%;
            margin-bottom: 10px;
        }
        .filter-control {
            display: table-cell;
            padding: 5px;
            vertical-align: top;
        }'''
    
    content = re.sub(old_css, new_css, content, flags=re.DOTALL)
    
    # Also ensure the table has fixed layout to match
    table_css = r'\.circuit-table\s*\{[^}]*\}'
    new_table_css = '''        .circuit-table {
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
        }'''
    
    content = re.sub(table_css, new_table_css, content, flags=re.DOTALL)
    
    # Save the updated template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'w') as f:
        f.write(content)
    
    print("✅ Updated filter controls to align with table column headers")
    print("✅ Both filters and table now use table-layout: fixed for perfect alignment")

if __name__ == "__main__":
    align_filters_with_headers()