#!/usr/bin/env python3
"""
Update Tab 4 to display as a proper table with new format
"""
import re

template_file = '/usr/local/bin/templates/inventory_final_4tabs.html'

# Read the template
with open(template_file, 'r') as f:
    content = f.read()

# Find and replace the Tab 4 content
pattern = r'(<div style="background-color: #f5f5f5.*?</pre>\s*</div>)'
replacement = '''<table id="datacenterTable" class="inventory-table" style="font-size: 11px;">
                    <thead>
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
                    </thead>
                    <tbody>
                        {% if datacenter_data and datacenter_data.inventory %}
                        {% for row in datacenter_data.inventory %}
                        <tr>
                            <td style="text-align: left;">{{ row.parent_hostname or row.hostname }}</td>
                            <td style="text-align: center;">{{ row.relationship }}</td>
                            <td style="font-family: monospace; font-size: 10px;">{{ row.ip_address }}</td>
                            <td style="text-align: center;">{{ row.position }}</td>
                            <td style="text-align: left;">{{ row.model }}</td>
                            <td style="font-family: monospace; font-size: 10px;">{{ row.serial_number }}</td>
                            <td style="text-align: left; font-size: 10px;">{{ row.port_location }}</td>
                            <td style="text-align: center;">{{ row.vendor }}</td>
                            <td style="text-align: left; font-size: 10px;">{{ row.notes }}</td>
                            <td style="text-align: center; font-size: 10px;">{{ row.end_of_support.strftime('%Y-%m-%d') if row.end_of_support else '' }}</td>
                        </tr>
                        {% endfor %}
                        {% else %}
                        <tr>
                            <td colspan="10" style="text-align: center; padding: 20px; color: #666;">No inventory data available</td>
                        </tr>
                        {% endif %}
                    </tbody>
                </table>'''

# Replace the content
content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write back
with open(template_file, 'w') as f:
    f.write(content)

# Also update Main templates
with open('/usr/local/bin/Main/templates/inventory_final_4tabs.html', 'w') as f:
    f.write(content)

print("Updated Tab 4 to table format with new structure")