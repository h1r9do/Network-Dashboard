#!/usr/bin/env python3
"""
Add last updated timestamp below row count
"""

print("=== ADDING LAST UPDATED TIMESTAMP ===\n")

# First, update the test route to pass the current timestamp
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    blueprint_content = f.read()

# Find the test route return and add current timestamp
old_return = '''        # Use the test template with badge counts
        return render_template('dsrcircuits_test.html', grouped_data=grouped_data, badge_counts=badge_counts)'''

new_return = '''        # Get current timestamp for last updated display
        from datetime import datetime
        last_updated = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        # Use the test template with badge counts and timestamp
        return render_template('dsrcircuits_test.html', grouped_data=grouped_data, badge_counts=badge_counts, last_updated=last_updated)'''

if old_return in blueprint_content:
    blueprint_content = blueprint_content.replace(old_return, new_return)
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
        f.write(blueprint_content)
    print("✅ Added timestamp to test route")
else:
    print("❌ Could not find test route return statement")

# Now update the template to display the last updated timestamp
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    template_content = f.read()

# Find the row count div and add last updated below it
old_row_count = '''        <div class="row-count" id="rowCount">Showing 0 of 0 rows</div>
    </div>'''

new_row_count = '''        <div class="row-count" id="rowCount">Showing 0 of 0 rows</div>
        {% if last_updated %}
        <div style="position: absolute; top: 45px; right: 15px; font-size: 12px; color: #bdc3c7; font-style: italic;">
            Last updated: {{ last_updated }}
        </div>
        {% endif %}
    </div>'''

if old_row_count in template_content:
    template_content = template_content.replace(old_row_count, new_row_count)
    with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
        f.write(template_content)
    print("✅ Added last updated timestamp to template")
else:
    print("❌ Could not find row count div in template")

print("\nLast updated timestamp added!")
print("Format: 'Last updated: July 09, 2025 at 07:32 PM'")
print("Location: Below row count on the right side")