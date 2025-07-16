#!/usr/bin/env python3
"""
Completely remove WAN Role filters from beta template
"""

import re

def remove_all_role_references():
    # Read the template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'r') as f:
        content = f.read()
    
    # Remove the entire filter-control divs for roles
    content = re.sub(
        r'<div class="filter-control">\s*<select id="wan1RoleFilter">.*?</select>\s*</div>',
        '',
        content,
        flags=re.DOTALL
    )
    
    content = re.sub(
        r'<div class="filter-control">\s*<select id="wan2RoleFilter">.*?</select>\s*</div>',
        '',
        content,
        flags=re.DOTALL
    )
    
    # Remove the JavaScript initialization for role filters
    content = re.sub(r"initRoleFilter\(4, '#wan1RoleFilter'\);?\s*", '', content)
    content = re.sub(r"initRoleFilter\(8, '#wan2RoleFilter'\);?\s*", '', content)
    
    # Remove any remaining references to role filters in JavaScript
    content = re.sub(r"\$\('#wan1RoleFilter'\)\.val\(\).*?;?\s*", '', content)
    content = re.sub(r"\$\('#wan2RoleFilter'\)\.val\(\).*?;?\s*", '', content)
    
    # Save the cleaned template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'w') as f:
        f.write(content)
    
    print("✅ Removed all role filter references from beta template")

if __name__ == "__main__":
    remove_all_role_references()