#!/usr/bin/env python3
"""
Fix Tab 4 columns - reduce vendor width and add EoS column
"""
import re

template_file = '/usr/local/bin/templates/inventory_final_4tabs.html'

# Read the template
with open(template_file, 'r') as f:
    content = f.read()

# Find and replace the table headers and column widths
old_headers = '''<thead>
                        <tr>
                            <th style="width: 15%;">Hostname</th>
                            <th style="width: 8%;">Relationship</th>
                            <th style="width: 10%;">IP Address</th>
                            <th style="width: 8%;">Position</th>
                            <th style="width: 12%;">Model</th>
                            <th style="width: 10%;">Serial Number</th>
                            <th style="width: 15%;">Port Location</th>
                            <th style="width: 8%;">Vendor</th>
                            <th style="width: 6%;">Notes</th>
                            <th style="width: 8%;">End of Life</th>
                        </tr>
                    </thead>'''

new_headers = '''<thead>
                        <tr>
                            <th style="width: 15%;">Hostname</th>
                            <th style="width: 8%;">Relationship</th>
                            <th style="width: 10%;">IP Address</th>
                            <th style="width: 8%;">Position</th>
                            <th style="width: 12%;">Model</th>
                            <th style="width: 10%;">Serial Number</th>
                            <th style="width: 12%;">Port Location</th>
                            <th style="width: 5%;">Vendor</th>
                            <th style="width: 5%;">Notes</th>
                            <th style="width: 7.5%;">End of Sale</th>
                            <th style="width: 7.5%;">End of Life</th>
                        </tr>
                    </thead>'''

# Replace headers
content = content.replace(old_headers, new_headers)

# Fix the tbody to include EoS column
old_row = '''<td style="text-align: center;">{{ row.vendor }}</td>
                            <td style="text-align: left; font-size: 10px;">{{ row.notes }}</td>
                            <td style="text-align: center; font-size: 10px;">{{ row.end_of_support.strftime('%Y-%m-%d') if row.end_of_support else '' }}</td>'''

new_row = '''<td style="text-align: center;">{{ row.vendor }}</td>
                            <td style="text-align: left; font-size: 10px;">{{ row.notes }}</td>
                            <td style="text-align: center; font-size: 10px;">{{ row.end_of_sale.strftime('%Y-%m-%d') if row.end_of_sale else '' }}</td>
                            <td style="text-align: center; font-size: 10px;">{{ row.end_of_support.strftime('%Y-%m-%d') if row.end_of_support else '' }}</td>'''

content = content.replace(old_row, new_row)

# Fix the no data colspan
content = content.replace('colspan="10"', 'colspan="11"')

# Write back
with open(template_file, 'w') as f:
    f.write(content)

# Also update Main templates
with open('/usr/local/bin/Main/templates/inventory_final_4tabs.html', 'w') as f:
    f.write(content)

print("Fixed Tab 4 columns - reduced vendor width and added End of Sale column")