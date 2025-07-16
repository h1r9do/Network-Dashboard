#!/usr/bin/env python3
"""
Fix the two failing nightly scripts:
1. Fix config import path to look in parent directory
2. Replace fuzzywuzzy with thefuzz
"""

import os
import re

def fix_script(script_path):
    """Fix imports and dependencies in a script"""
    print(f"\nProcessing: {script_path}")
    
    with open(script_path, 'r') as f:
        content = f.read()
    
    changes_made = []
    
    # 1. Fix the config import path
    # Look for the current sys.path manipulation and config import
    if 'sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))' in content:
        old_pattern = r'sys\.path\.insert\(0, os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)'
        new_line = 'sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))'
        content = re.sub(old_pattern, new_line, content)
        changes_made.append("Fixed sys.path to look in parent directory")
    
    # Also check for sys.path.append patterns
    if "sys.path.append('/usr/local/bin/test')" in content:
        content = content.replace(
            "sys.path.append('/usr/local/bin/test')",
            "sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))"
        )
        changes_made.append("Replaced test path with parent directory path")
    
    # 2. Replace fuzzywuzzy with thefuzz
    if 'from fuzzywuzzy import fuzz' in content:
        content = content.replace('from fuzzywuzzy import fuzz', 'from thefuzz import fuzz')
        changes_made.append("Replaced fuzzywuzzy import with thefuzz")
    
    # Write the fixed content
    if changes_made:
        with open(script_path, 'w') as f:
            f.write(content)
        print(f"  ✓ Applied {len(changes_made)} fixes:")
        for change in changes_made:
            print(f"    - {change}")
    else:
        print("  ✓ No changes needed")
    
    return len(changes_made) > 0

# Fix both scripts
scripts_to_fix = [
    '/usr/local/bin/Main/nightly/nightly_meraki_db.py',
    '/usr/local/bin/Main/nightly/nightly_enriched_db.py'
]

print("Fixing nightly scripts...")
print("=" * 50)

fixed_count = 0
for script in scripts_to_fix:
    if os.path.exists(script):
        if fix_script(script):
            fixed_count += 1
    else:
        print(f"\n✗ Script not found: {script}")

print("\n" + "=" * 50)
print(f"Summary: Fixed {fixed_count} scripts")

# Also ensure thefuzz is installed
print("\nChecking thefuzz installation...")
try:
    import thefuzz
    print("✓ thefuzz is installed")
except ImportError:
    print("✗ thefuzz is not installed - please run: sudo python3 -m pip install thefuzz")