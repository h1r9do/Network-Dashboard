#!/usr/bin/env python3
"""
Replace fuzzywuzzy imports with thefuzz in nightly scripts
"""

import os

scripts = [
    '/usr/local/bin/Main/nightly/nightly_meraki_db.py',
    '/usr/local/bin/Main/nightly/nightly_enriched_db.py'
]

for script_path in scripts:
    if not os.path.exists(script_path):
        print(f"Script not found: {script_path}")
        continue
        
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Replace imports
    content = content.replace('from fuzzywuzzy import fuzz', 'from thefuzz import fuzz')
    
    with open(script_path, 'w') as f:
        f.write(content)
    
    print(f"Updated imports in {script_path}")

print("Done!")