#!/usr/bin/env python3
"""
Remove speed filters to isolate the issue
"""

print("=== REMOVING SPEED FILTERS ===\n")

with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# Replace speed dropdowns with simple text inputs
import re

# Find and replace WAN1 Speed filter
wan1_speed_pattern = r'<select id="wan1SpeedFilter">.*?</select>'
wan1_speed_replacement = '<input type="text" id="wan1SpeedFilter" placeholder="Filter WAN1 Speed...">'
content = re.sub(wan1_speed_pattern, wan1_speed_replacement, content, flags=re.DOTALL)
print("✅ Replaced WAN1 speed dropdown with text input")

# Find and replace WAN2 Speed filter
wan2_speed_pattern = r'<select id="wan2SpeedFilter">.*?</select>'
wan2_speed_replacement = '<input type="text" id="wan2SpeedFilter" placeholder="Filter WAN2 Speed...">'
content = re.sub(wan2_speed_pattern, wan2_speed_replacement, content, flags=re.DOTALL)
print("✅ Replaced WAN2 speed dropdown with text input")

# Update the JavaScript to use text search for speeds
old_speed_handlers = '''            // Speeds
            $('#wan1SpeedFilter').on('change', function() {
                table.column(2).search(this.value).draw();
            });
            
            $('#wan2SpeedFilter').on('change', function() {
                table.column(5).search(this.value).draw();
            });'''

new_speed_handlers = '''            // Speed text filters
            $('#wan1SpeedFilter').on('keyup', function() {
                table.column(2).search(this.value).draw();
            });
            
            $('#wan2SpeedFilter').on('keyup', function() {
                table.column(5).search(this.value).draw();
            });'''

content = content.replace(old_speed_handlers, new_speed_handlers)
print("✅ Updated speed filter handlers to use keyup")

# Write the updated content
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("\n✅ Removed speed dropdowns - using text inputs instead")
print("This eliminates any Jinja2 issues with speed filters")