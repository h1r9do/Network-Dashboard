#!/usr/bin/env python3
"""
Remove WAN Role columns from the main dsrcircuits page
Keep them visible in the modal only
"""

import re

def remove_role_columns():
    # Read the current template
    with open('/usr/local/bin/Main/templates/dsrcircuits.html', 'r') as f:
        content = f.read()
    
    # 1. Remove the table headers for WAN Role
    content = re.sub(r'<th>WAN 1 Role</th>\s*', '', content)
    content = re.sub(r'<th>WAN 2 Role</th>\s*', '', content)
    
    # 2. Remove the filter dropdowns for roles (but keep the containers for layout)
    # Replace the select elements with empty divs
    content = re.sub(
        r'<select id="wan1RoleFilter"[^>]*>.*?</select>',
        '<div style="height: 34px;"></div>',
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r'<select id="wan2RoleFilter"[^>]*>.*?</select>',
        '<div style="height: 34px;"></div>',
        content,
        flags=re.DOTALL
    )
    
    # 3. Find and remove the table data cells for roles
    # Look for the pattern where roles are displayed in the table body
    # This is typically something like <td>${wan1.circuit_role || 'N/A'}</td>
    
    # First, let's identify the exact pattern by looking at the table row structure
    # We need to find where the role data is inserted in the JavaScript
    
    # Save the modified content
    output_file = '/usr/local/bin/Main/templates/dsrcircuits_no_roles.html'
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"Modified template saved to: {output_file}")
    print("\nChanges made:")
    print("1. Removed WAN 1 Role and WAN 2 Role table headers")
    print("2. Replaced role filter dropdowns with empty spacers")
    print("\nNext step: Need to identify and remove the role data cells from the table rows")
    
    # Let's search for where the table rows are generated
    matches = re.findall(r'<td[^>]*>\$\{[^}]*circuit_role[^}]*\}</td>', content)
    if matches:
        print(f"\nFound {len(matches)} role cell patterns to remove:")
        for match in matches:
            print(f"  {match}")

if __name__ == "__main__":
    remove_role_columns()