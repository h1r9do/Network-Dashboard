#!/usr/bin/env python3
"""
Add Site column to the template as the first column
"""
import re

template_file = '/usr/local/bin/templates/inventory_final_4tabs.html'

# Read the template
with open(template_file, 'r') as f:
    content = f.read()

# Find the datacenter table headers and add Site as first column
old_headers = '''<tr>
                            <th style="white-space: nowrap;">Hostname</th>'''

new_headers = '''<tr>
                            <th style="white-space: nowrap;">Site</th>
                            <th style="white-space: nowrap;">Hostname</th>'''

content = content.replace(old_headers, new_headers)

# Update the tbody to include site column
old_tbody = '''<tr>
                            <td style="text-align: left;">{{ row.parent_hostname or row.hostname }}</td>'''

new_tbody = '''<tr>
                            <td style="text-align: left;">{{ row.site }}</td>
                            <td style="text-align: left;">{{ row.parent_hostname or row.hostname }}</td>'''

content = content.replace(old_tbody, new_tbody)

# Update the no data colspan from 11 to 12
content = content.replace('colspan="11"', 'colspan="12"')

# Write back
with open(template_file, 'w') as f:
    f.write(content)

# Also update Main templates
with open('/usr/local/bin/Main/templates/inventory_final_4tabs.html', 'w') as f:
    f.write(content)

print("Added Site column to template as first column")