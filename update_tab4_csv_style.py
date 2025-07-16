#!/usr/bin/env python3
"""
Update Tab 4 to display as plain CSV
"""
import re

template_file = '/usr/local/bin/templates/inventory_final_4tabs.html'

# Read the template
with open(template_file, 'r') as f:
    content = f.read()

# Find the datacenterTable section and replace it with CSV style
# Look for the table with id="datacenterTable"
pattern = r'(<table id="datacenterTable".*?>.*?</table>)'
replacement = '''<div style="background-color: #f5f5f5; padding: 10px; border: 1px solid #ddd; font-family: monospace; font-size: 12px; overflow-x: auto;">
<pre style="margin: 0;">hostname,ip_address,position,model,serial_number,port_location,vendor,notes
{% if datacenter_data and datacenter_data.inventory %}{% for row in datacenter_data.inventory %}{{ row.hostname }},{{ row.ip_address }},{{ row.position }},{{ row.model }},{{ row.serial_number }},{{ row.port_location }},{{ row.vendor }},{{ row.notes }}
{% endfor %}{% endif %}</pre>
</div>'''

# Replace the table with pre-formatted CSV
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open(template_file, 'w') as f:
    f.write(content)

print("Updated Tab 4 to CSV style display")