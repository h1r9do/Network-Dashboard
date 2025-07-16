#!/usr/bin/env python3
"""
Fix table overflow issues - remove nowrap and add specific styling for port location
"""
import re

template_file = '/usr/local/bin/templates/inventory_final_4tabs.html'

# Read the template
with open(template_file, 'r') as f:
    content = f.read()

# Remove white-space: nowrap from inventory-table td
old_td_style = '''white-space: nowrap;'''
new_td_style = '''white-space: normal;
            word-wrap: break-word;'''

content = content.replace(old_td_style, new_td_style)

# Add specific styling for port location cells to handle long text
old_port_td = '''<td style="text-align: left; font-size: 10px;">{{ row.port_location }}</td>'''
new_port_td = '''<td style="text-align: left; font-size: 10px; white-space: normal; word-wrap: break-word; max-width: 200px;">{{ row.port_location }}</td>'''

content = content.replace(old_port_td, new_port_td)

# Write back
with open(template_file, 'w') as f:
    f.write(content)

# Also update Main templates
with open('/usr/local/bin/Main/templates/inventory_final_4tabs.html', 'w') as f:
    f.write(content)

print("Fixed table overflow - removed nowrap and added word-wrap for port location")