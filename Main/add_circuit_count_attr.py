#!/usr/bin/env python3
"""Add circuit count data attribute to table rows"""

# Read the template file
with open('/usr/local/bin/templates/dsrallcircuits.html', 'r') as f:
    content = f.read()

# Replace the table row to include data-circuit-count attribute
old_row = '<tr class="circuit-row">'
new_row = '<tr class="circuit-row" data-circuit-count="{{ circuit.circuit_count }}">'

content = content.replace(old_row, new_row)

# Write the updated content
with open('/usr/local/bin/templates/dsrallcircuits.html', 'w') as f:
    f.write(content)

print("✅ Successfully added circuit count data attribute to table rows")