#!/usr/bin/env python3
"""
Synchronize table column widths with filter widths
"""

import re

def sync_table_filter_widths():
    # Read the template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'r') as f:
        content = f.read()
    
    # Update the table CSS to use table-layout: fixed and match filter structure
    table_css = r'\.circuit-table\s*\{[^}]*\}'
    new_table_css = '''        .circuit-table {
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
        }
        .circuit-table th, .circuit-table td {
            width: 12.5%; /* 100% / 8 columns = 12.5% each */
            text-align: left;
            padding: 8px;
            border: 1px solid #ddd;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }'''
    
    content = re.sub(table_css, new_table_css, content, flags=re.DOTALL)
    
    # Also ensure the filters use the same percentage widths
    filter_css = r'\.filter-controls\s*\{[^}]*\}'
    new_filter_css = '''        .filter-controls {
            display: table;
            width: 100%;
            table-layout: fixed;
            margin-bottom: 0;
            border: 1px solid #ddd;
            border-bottom: none;
            background: #f8f9fa;
        }'''
    
    content = re.sub(filter_css, new_filter_css, content, flags=re.DOTALL)
    
    # Update filter-control CSS
    filter_control_css = r'\.filter-control\s*\{[^}]*\}'
    new_filter_control_css = '''        .filter-control {
            display: table-cell;
            width: 12.5%;
            padding: 5px;
            border-right: 1px solid #ddd;
            vertical-align: top;
        }'''
    
    content = re.sub(filter_control_css, new_filter_control_css, content, flags=re.DOTALL)
    
    # Save the updated template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'w') as f:
        f.write(content)
    
    print("✅ Synchronized table and filter widths to 12.5% each")
    print("✅ Both use table-layout: fixed for perfect alignment")

if __name__ == "__main__":
    sync_table_filter_widths()