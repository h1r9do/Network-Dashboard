#!/usr/bin/env python3
"""
Fix import issues in nightly scripts by updating config import path
"""

import os
import re

def fix_config_import(file_path):
    """Fix the config import in a file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to find the problematic import section
    patterns = [
        (r'sys\.path\.append\(\'/usr/local/bin/test\'\)\nfrom config import Config',
         '# Add parent directory to path for config import\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\nfrom config import Config'),
        (r'sys\.path\.insert\(0, os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)\nfrom config import Config',
         '# Add parent directory to path for config import\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\nfrom config import Config'),
        # Handle case where config is imported without path modification
        (r'from config import Config',
         '# Add parent directory to path for config import\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\nfrom config import Config')
    ]
    
    fixed = False
    for old_pattern, new_text in patterns:
        if re.search(old_pattern, content):
            content = re.sub(old_pattern, new_text, content)
            fixed = True
            break
    
    # If no pattern matched but "from config import Config" exists, we need to add the path
    if not fixed and 'from config import Config' in content:
        # Find the line with the import
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'from config import Config' in line and not any('sys.path' in lines[j] for j in range(max(0, i-5), i)):
                # Insert the path setup before the import
                lines.insert(i, '# Add parent directory to path for config import')
                lines.insert(i+1, 'sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))')
                content = '\n'.join(lines)
                fixed = True
                break
    
    if fixed:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Fixed imports in {file_path}")
        return True
    else:
        print(f"No changes needed in {file_path}")
        return False

# Fix the nightly scripts
scripts_to_fix = [
    '/usr/local/bin/Main/nightly/nightly_meraki_db.py',
    '/usr/local/bin/Main/nightly/nightly_enriched_db.py'
]

print("Fixing config imports in nightly scripts...")
for script in scripts_to_fix:
    if os.path.exists(script):
        fix_config_import(script)
    else:
        print(f"Script not found: {script}")

print("\nDone!")