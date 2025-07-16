#!/usr/bin/env python3
"""
Update test route to use test template
"""

# Read the blueprint file
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    content = f.read()

# Update the test route to use the test template
old_template = "return render_template('dsrcircuits.html', grouped_data=grouped_data)"
new_template = "return render_template('dsrcircuits_test.html', grouped_data=grouped_data)"

# Find and replace in the test route only
test_route_start = content.find("@dsrcircuits_bp.route('/dsrcircuits-test')")
test_route_end = content.find("@dsrcircuits_bp.route('/api/circuits/data')")

if test_route_start != -1 and test_route_end != -1:
    test_route_section = content[test_route_start:test_route_end]
    updated_test_section = test_route_section.replace(old_template, new_template)
    
    new_content = content[:test_route_start] + updated_test_section + content[test_route_end:]
    
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Updated test route to use dsrcircuits_test.html template")
else:
    print("❌ Could not find test route section")