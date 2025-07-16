#!/usr/bin/env python3
"""
Remove WAN Role columns from the main dsrcircuits page completely
Keep them visible only in the modal
"""

import re
import os

def remove_role_columns():
    # Read the current template
    input_file = '/usr/local/bin/Main/templates/dsrcircuits_beta.html'
    output_file = '/usr/local/bin/Main/templates/dsrcircuits_beta_no_roles.html'
    
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Count changes for reporting
    changes = []
    
    # 1. Remove the table headers for WAN Role
    original = content
    content = re.sub(r'<th>WAN 1 Role</th>\s*', '', content)
    if content != original:
        changes.append("Removed WAN 1 Role header")
    
    original = content
    content = re.sub(r'<th>WAN 2 Role</th>\s*', '', content)
    if content != original:
        changes.append("Removed WAN 2 Role header")
    
    # 2. Remove the role filter dropdowns completely including their containers
    # Find and remove the entire filter div for WAN1 Role
    content = re.sub(
        r'<div class="filter-group">\s*<label[^>]*>WAN1 Role[^<]*</label>\s*<select id="wan1RoleFilter"[^>]*>.*?</select>\s*</div>',
        '',
        content,
        flags=re.DOTALL
    )
    changes.append("Removed WAN1 Role filter dropdown")
    
    # Find and remove the entire filter div for WAN2 Role
    content = re.sub(
        r'<div class="filter-group">\s*<label[^>]*>WAN2 Role[^<]*</label>\s*<select id="wan2RoleFilter"[^>]*>.*?</select>\s*</div>',
        '',
        content,
        flags=re.DOTALL
    )
    changes.append("Removed WAN2 Role filter dropdown")
    
    # 3. Remove the table data cells for roles in the Jinja2 template
    # Remove the WAN1 role cell
    content = re.sub(
        r'<td data-role="{{ entry\.wan1\.circuit_role }}">{{ entry\.wan1\.circuit_role if entry\.wan1\.circuit_role else \'null\' }}</td>\s*',
        '',
        content
    )
    changes.append("Removed WAN1 role data cell")
    
    # Remove the WAN2 role cell
    content = re.sub(
        r'<td data-role="{{ entry\.wan2\.circuit_role }}">{{ entry\.wan2\.circuit_role if entry\.wan2\.circuit_role else \'null\' }}</td>\s*',
        '',
        content
    )
    changes.append("Removed WAN2 role data cell")
    
    # 4. Also need to remove role cells from any JavaScript that creates table rows
    # Look for patterns like <td>${wan1.circuit_role || 'N/A'}</td>
    content = re.sub(
        r'<td[^>]*>\$\{[^}]*wan1[^}]*circuit_role[^}]*\}</td>\s*',
        '',
        content
    )
    
    content = re.sub(
        r'<td[^>]*>\$\{[^}]*wan2[^}]*circuit_role[^}]*\}</td>\s*',
        '',
        content
    )
    changes.append("Removed role cells from JavaScript table generation")
    
    # 5. Update any column index references in JavaScript
    # The role columns were at positions 4 and 8, so we need to adjust filtering logic
    # This is more complex and might need manual review
    
    # Save the modified content
    with open(output_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Modified template saved to: {output_file}")
    print(f"\n📝 Changes made ({len(changes)}):")
    for change in changes:
        print(f"   - {change}")
    
    print("\n⚠️  Note: The role information will still be visible in the modal popup")
    print("⚠️  You may need to adjust JavaScript column indexes if there's sorting/filtering by column number")
    
    # To apply to production:
    print(f"\n🚀 To apply changes:")
    print(f"   sudo cp {output_file} {input_file}")
    print(f"   sudo systemctl restart meraki-dsrcircuits.service")

if __name__ == "__main__":
    remove_role_columns()