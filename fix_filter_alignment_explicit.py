#!/usr/bin/env python3
"""
Fix filter alignment by moving filters directly above the table headers
"""

import re

def fix_filter_alignment():
    # Read the template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'r') as f:
        content = f.read()
    
    # Find the table and move filters right above it
    table_start = content.find('<table id="circuitTable"')
    if table_start == -1:
        print("❌ Could not find table")
        return
    
    # Find the current filter-controls section
    filter_start = content.find('<div class="filter-controls">')
    if filter_start == -1:
        print("❌ Could not find filter-controls")
        return
    
    # Find the end of the filter controls
    filter_end = content.find('</div>', filter_start)
    brace_count = 1
    pos = filter_start + len('<div class="filter-controls">')
    
    while pos < len(content) and brace_count > 0:
        if content[pos:pos+5] == '<div ':
            brace_count += 1
        elif content[pos:pos+6] == '</div>':
            brace_count -= 1
            if brace_count == 0:
                filter_end = pos + 6
                break
        pos += 1
    
    # Extract the filter section
    filter_section = content[filter_start:filter_end]
    
    # Remove the old filter section
    content = content[:filter_start] + content[filter_end:]
    
    # Update the table start position after removal
    table_start = content.find('<table id="circuitTable"')
    
    # Insert the filters right before the table
    new_content = content[:table_start] + filter_section + '\n\n        ' + content[table_start:]
    
    # Update the CSS to use flexbox for better alignment
    css_replacement = '''        .filter-controls {
            display: flex;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-bottom: none;
            background: #f8f9fa;
        }
        .filter-control {
            flex: 1;
            padding: 5px;
            border-right: 1px solid #ddd;
        }
        .filter-control:last-child {
            border-right: none;
        }'''
    
    new_content = re.sub(
        r'\.filter-controls\s*\{[^}]*\}',
        css_replacement,
        new_content,
        flags=re.DOTALL
    )
    
    # Save the updated template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'w') as f:
        f.write(new_content)
    
    print("✅ Moved filters directly above table")
    print("✅ Updated to use flexbox for perfect column alignment")

if __name__ == "__main__":
    fix_filter_alignment()