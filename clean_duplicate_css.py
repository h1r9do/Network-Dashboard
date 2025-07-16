#!/usr/bin/env python3
"""
Clean up duplicate CSS definitions in the template
"""

import re

def clean_duplicate_css():
    # Read the template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'r') as f:
        content = f.read()
    
    # Find all .filter-control CSS definitions and remove duplicates
    # Keep only the first complete definition
    
    # First, let's find the complete style section
    style_start = content.find('<style>')
    style_end = content.find('</style>') + 8
    style_section = content[style_start:style_end]
    
    # Clean up duplicate .filter-control definitions
    # Remove any isolated .filter-control { padding: 5px; } blocks
    cleaned_style = re.sub(r'\s*\.filter-control\s*\{\s*padding:\s*5px;\s*\}\s*', '', style_section)
    
    # Ensure we have one proper filter-control definition
    if '.filter-control {' not in cleaned_style:
        # Add it after filter-controls
        cleaned_style = cleaned_style.replace(
            'margin-bottom: 10px;\n        }',
            'margin-bottom: 10px;\n        }\n        .filter-control {\n            padding: 5px;\n        }'
        )
    
    # Replace the style section
    content = content[:style_start] + cleaned_style + content[style_end:]
    
    # Save the cleaned template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'w') as f:
        f.write(content)
    
    print("✅ Cleaned up duplicate CSS definitions")

if __name__ == "__main__":
    clean_duplicate_css()