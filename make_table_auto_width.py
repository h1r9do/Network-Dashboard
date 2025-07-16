#!/usr/bin/env python3
"""
Change table to auto-size columns based on content
"""
import re

template_file = '/usr/local/bin/templates/inventory_final_4tabs.html'

# Read the template
with open(template_file, 'r') as f:
    content = f.read()

# Change table-layout from fixed to auto
content = content.replace('table-layout: fixed;', 'table-layout: auto;')

# Remove all width styles from the datacenter table headers
# We'll keep white-space: nowrap to prevent wrapping
pattern = r'<th style="width: \d+\.?\d*%;">([^<]+)</th>'
replacement = r'<th style="white-space: nowrap;">\1</th>'

# Apply to the datacenter table section
start_marker = '<table id="datacenterTable"'
end_marker = '</thead>'

# Find the section
start_idx = content.find(start_marker)
if start_idx != -1:
    end_idx = content.find(end_marker, start_idx)
    if end_idx != -1:
        # Extract the section
        section = content[start_idx:end_idx + len(end_marker)]
        # Replace all th width styles in this section
        new_section = re.sub(pattern, replacement, section)
        # Replace in content
        content = content[:start_idx] + new_section + content[end_idx + len(end_marker):]

# Also ensure td cells don't wrap
content = content.replace('white-space: normal;', 'white-space: nowrap;')

# Write back
with open(template_file, 'w') as f:
    f.write(content)

# Also update Main templates
with open('/usr/local/bin/Main/templates/inventory_final_4tabs.html', 'w') as f:
    f.write(content)

print("Changed table to auto-width - columns will size based on content")