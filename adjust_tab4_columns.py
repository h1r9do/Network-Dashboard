#!/usr/bin/env python3
"""
Adjust Tab 4 columns - widen Port Location to 15%, narrow Vendor to 2.5%
"""
import re

template_file = '/usr/local/bin/templates/inventory_final_4tabs.html'

# Read the template
with open(template_file, 'r') as f:
    content = f.read()

# Find and replace the column widths in headers
old_widths = '''<th style="width: 12%;">Port Location</th>
                            <th style="width: 5%;">Vendor</th>'''

new_widths = '''<th style="width: 15%;">Port Location</th>
                            <th style="width: 2.5%;">Vendor</th>'''

# Replace headers
content = content.replace(old_widths, new_widths)

# Write back
with open(template_file, 'w') as f:
    f.write(content)

# Also update Main templates
with open('/usr/local/bin/Main/templates/inventory_final_4tabs.html', 'w') as f:
    f.write(content)

print("Adjusted Tab 4 columns - Port Location: 15%, Vendor: 2.5%")