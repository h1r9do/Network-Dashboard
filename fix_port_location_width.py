#!/usr/bin/env python3
"""
Give Port Location much more space and reduce Vendor to minimal
"""
import re

template_file = '/usr/local/bin/templates/inventory_final_4tabs.html'

# Read the template
with open(template_file, 'r') as f:
    content = f.read()

# Replace the column widths - give Port Location 20% and Vendor only 1%
old_widths = '''<th style="width: 15%;">Port Location</th>
                            <th style="width: 2.5%;">Vendor</th>'''

new_widths = '''<th style="width: 20%;">Port Location</th>
                            <th style="width: 1%;">Vendor</th>'''

# Also need to adjust other columns to make room
# Current total: 15+8+10+8+12+10+15+2.5+5+7.5+7.5 = 100.5%
# New total: 15+8+10+8+12+10+20+1+5+7.5+7.5 = 104%
# Need to reduce something - let's reduce Notes to 2%

old_notes = '''<th style="width: 5%;">Notes</th>'''
new_notes = '''<th style="width: 2%;">Notes</th>'''

# Replace all widths
content = content.replace(old_widths, new_widths)
content = content.replace(old_notes, new_notes)

# Write back
with open(template_file, 'w') as f:
    f.write(content)

# Also update Main templates
with open('/usr/local/bin/Main/templates/inventory_final_4tabs.html', 'w') as f:
    f.write(content)

print("Updated column widths: Port Location: 20%, Vendor: 1%, Notes: 2%")