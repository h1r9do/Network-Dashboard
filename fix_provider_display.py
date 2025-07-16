#!/usr/bin/env python3
"""
Fix for the provider display issue in the dsrcircuits confirm modal.

The issue: The modal is showing "Unknown" for providers because it's displaying
the ARIN provider lookup result instead of the actual circuit provider.

The fix: Update the confirm_site function to return ARIN data with different
key names to avoid conflicts with the circuit provider data.
"""

import os
import shutil
from datetime import datetime

def fix_confirm_site():
    """Fix the confirm_site function to use different keys for ARIN data"""
    
    # Backup the original file
    source_file = '/usr/local/bin/Main/confirm_meraki_notes_db_fixed.py'
    backup_file = f'{source_file}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    print(f"Creating backup: {backup_file}")
    shutil.copy2(source_file, backup_file)
    
    # Read the file
    with open(source_file, 'r') as f:
        content = f.read()
    
    # Find and replace the problematic section
    # Change the return keys in get_arin_data function
    old_arin_return = """return {
                'wan1_ip': meraki_data[0] or 'N/A',
                'wan1_provider': meraki_data[1] or 'N/A',
                'wan2_ip': meraki_data[2] or 'N/A', 
                'wan2_provider': meraki_data[3] or 'N/A'
            }"""
    
    new_arin_return = """return {
                'wan1_ip': meraki_data[0] or 'N/A',
                'wan1_arin_provider': meraki_data[1] or 'N/A',
                'wan2_ip': meraki_data[2] or 'N/A', 
                'wan2_arin_provider': meraki_data[3] or 'N/A'
            }"""
    
    content = content.replace(old_arin_return, new_arin_return)
    
    # Also fix the fallback return
    old_fallback = """arin_data = {
                'wan1_ip': 'N/A',
                'wan1_provider': 'N/A', 
                'wan2_ip': 'N/A',
                'wan2_provider': 'N/A'
            }"""
    
    new_fallback = """arin_data = {
                'wan1_ip': 'N/A',
                'wan1_arin_provider': 'N/A', 
                'wan2_ip': 'N/A',
                'wan2_arin_provider': 'N/A'
            }"""
    
    content = content.replace(old_fallback, new_fallback)
    
    # Fix the assignments in the loop
    content = content.replace(
        "arin_data['wan1_provider'] = provider or 'N/A'",
        "arin_data['wan1_arin_provider'] = provider or 'N/A'"
    )
    content = content.replace(
        "arin_data['wan2_provider'] = provider or 'N/A'",
        "arin_data['wan2_arin_provider'] = provider or 'N/A'"
    )
    
    # Fix the error return
    old_error_return = """return {
            'wan1_ip': 'N/A',
            'wan1_provider': 'N/A',
            'wan2_ip': 'N/A', 
            'wan2_provider': 'N/A'
        }"""
    
    new_error_return = """return {
            'wan1_ip': 'N/A',
            'wan1_arin_provider': 'N/A',
            'wan2_ip': 'N/A', 
            'wan2_arin_provider': 'N/A'
        }"""
    
    content = content.replace(old_error_return, new_error_return)
    
    # Write the fixed content
    with open(source_file, 'w') as f:
        f.write(content)
    
    print("✅ Fixed confirm_meraki_notes_db_fixed.py")
    
    # Now fix the template to use the correct keys
    template_file = '/usr/local/bin/templates/dsrcircuits.html'
    template_backup = f'{template_file}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    print(f"Creating template backup: {template_backup}")
    shutil.copy2(template_file, template_backup)
    
    with open(template_file, 'r') as f:
        template_content = f.read()
    
    # Fix the ARIN display to use the new keys
    template_content = template_content.replace(
        "(response.wan1_provider || 'N/A')",
        "(response.wan1_arin_provider || 'N/A')"
    )
    template_content = template_content.replace(
        "(response.wan2_provider || 'N/A')",
        "(response.wan2_arin_provider || 'N/A')"
    )
    
    with open(template_file, 'w') as f:
        f.write(template_content)
    
    print("✅ Fixed dsrcircuits.html template")
    
    return True

if __name__ == "__main__":
    if fix_confirm_site():
        print("\n✅ Provider display issue has been fixed!")
        print("The modal will now show:")
        print("  - Circuit provider from enriched_circuits table (not ARIN lookup)")
        print("  - ARIN provider in the ARIN/IP Information section")
        print("\nTest with AZN 02 to verify the fix.")
    else:
        print("\n❌ Failed to fix provider display issue")