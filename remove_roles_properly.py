#!/usr/bin/env python3
"""
Properly remove role columns while maintaining filter alignment
"""

import re

def remove_roles_properly():
    # Read the fresh template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'r') as f:
        content = f.read()
    
    print("Original template loaded")
    
    # 1. Remove role column headers
    content = re.sub(r'<th>WAN 1 Role</th>\s*', '', content)
    content = re.sub(r'<th>WAN 2 Role</th>\s*', '', content)
    print("✓ Removed role headers")
    
    # 2. Remove role filter controls (complete divs)
    content = re.sub(
        r'<div class="filter-control">\s*<select id="wan1RoleFilter">.*?</select>\s*</div>',
        '<div class="filter-control"><!-- WAN1 Role filter removed --></div>',
        content,
        flags=re.DOTALL
    )
    content = re.sub(
        r'<div class="filter-control">\s*<select id="wan2RoleFilter">.*?</select>\s*</div>',
        '<div class="filter-control"><!-- WAN2 Role filter removed --></div>',
        content,
        flags=re.DOTALL
    )
    print("✓ Removed role filter controls")
    
    # 3. Remove role data cells from table body
    # Find the table row template and remove role cells
    content = re.sub(
        r'<td data-role="\$\{entry\.wan1\.circuit_role\}">\$\{entry\.wan1\.circuit_role \|\| \'null\'\}</td>\s*',
        '',
        content
    )
    content = re.sub(
        r'<td data-role="\$\{entry\.wan2\.circuit_role\}">\$\{entry\.wan2\.circuit_role \|\| \'null\'\}</td>\s*',
        '',
        content
    )
    print("✓ Removed role data cells")
    
    # 4. Remove role filter JavaScript initialization
    content = re.sub(r"initRoleFilter\(4, '#wan1RoleFilter'\);\s*", '', content)
    content = re.sub(r"initRoleFilter\(8, '#wan2RoleFilter'\);\s*", '', content)
    print("✓ Removed role filter JavaScript")
    
    # 5. Update column indexes in remaining JavaScript
    # After removing columns 4 and 8, the remaining columns shift:
    # Original: 0=Site, 1=WAN1Prov, 2=WAN1Speed, 3=WAN1Cost, 4=WAN1Role, 5=WAN2Prov, 6=WAN2Speed, 7=WAN2Cost, 8=WAN2Role, 9=Action
    # New:      0=Site, 1=WAN1Prov, 2=WAN1Speed, 3=WAN1Cost,             4=WAN2Prov, 5=WAN2Speed, 6=WAN2Cost,             7=Action
    
    # Update WAN2 provider filter from column 5 to column 4
    content = re.sub(r"initProviderFilter\(5, '#wan2ProviderFilter'\);", "initProviderFilter(4, '#wan2ProviderFilter');", content)
    # Update WAN2 speed filter from column 6 to column 5  
    content = re.sub(r"initDropdownFilter\(6, '#wan2SpeedFilter'\);", "initDropdownFilter(5, '#wan2SpeedFilter');", content)
    print("✓ Updated JavaScript column indexes")
    
    # 6. Update grid template to 8 columns (was 10, remove 2 role columns)
    content = re.sub(r'grid-template-columns: repeat\(10, 1fr\);', 'grid-template-columns: repeat(8, 1fr);', content)
    print("✓ Updated grid to 8 columns")
    
    # Save the properly fixed template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'w') as f:
        f.write(content)
    
    print("\n✅ Template properly fixed!")
    print("Columns are now: Site, WAN1 Provider, WAN1 Speed, WAN1 Cost, WAN2 Provider, WAN2 Speed, WAN2 Cost, Action")

if __name__ == "__main__":
    remove_roles_properly()