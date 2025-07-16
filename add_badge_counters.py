#!/usr/bin/env python3
"""
Add badge counters to the test page header
"""

print("=== ADDING BADGE COUNTERS TO TEST PAGE ===\n")

# First, update the test route to calculate badge counts
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    blueprint_content = f.read()

# Find the test route and add badge counting logic
old_return = '''        # Use the same template as production
        return render_template('dsrcircuits_test.html', grouped_data=grouped_data)'''

new_return = '''        # Calculate badge counts for header display
        dsr_count = vzw_count = att_count = starlink_count = 0
        
        for entry in grouped_data:
            # Count DSR badges
            if entry['wan1']['match_info'] and entry['wan1']['match_info'].dsr_verified:
                dsr_count += 1
            if entry['wan2']['match_info'] and entry['wan2']['match_info'].dsr_verified:
                dsr_count += 1
                
            # Count wireless badges
            if entry['wan1'].get('wireless_badge'):
                if entry['wan1']['wireless_badge'] == 'VZW':
                    vzw_count += 1
                elif entry['wan1']['wireless_badge'] == 'ATT':
                    att_count += 1
                elif entry['wan1']['wireless_badge'] == 'STARLINK':
                    starlink_count += 1
                    
            if entry['wan2'].get('wireless_badge'):
                if entry['wan2']['wireless_badge'] == 'VZW':
                    vzw_count += 1
                elif entry['wan2']['wireless_badge'] == 'ATT':
                    att_count += 1
                elif entry['wan2']['wireless_badge'] == 'STARLINK':
                    starlink_count += 1
        
        badge_counts = {
            'dsr': dsr_count,
            'vzw': vzw_count, 
            'att': att_count,
            'starlink': starlink_count
        }
        
        # Use the test template with badge counts
        return render_template('dsrcircuits_test.html', grouped_data=grouped_data, badge_counts=badge_counts)'''

if old_return in blueprint_content:
    blueprint_content = blueprint_content.replace(old_return, new_return)
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
        f.write(blueprint_content)
    print("✅ Added badge counting logic to test route")
else:
    print("❌ Could not find test route return statement")

# Now update the template to display badge counters
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    template_content = f.read()

# Find the row count div and add badge counters before it
old_header = '''    <div class="header-container">
        <h1>Discount Tire Active Circuit Master List</h1>
        <div class="row-count" id="rowCount">Showing 0 of 0 rows</div>
    </div>'''

new_header = '''    <div class="header-container">
        <h1>Discount Tire Active Circuit Master List</h1>
        <div style="position: absolute; top: 15px; right: 200px; font-size: 12px; display: flex; gap: 15px; align-items: center;">
            {% if badge_counts %}
            <span style="display: flex; align-items: center; gap: 3px;">
                <span class="dsr-badge" style="display: inline-flex; align-items: center; background: #2ecc71; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold; border: 1px solid #27ae60;">DSR</span>
                <span style="color: #ecf0f1;">{{ badge_counts.dsr }}</span>
            </span>
            <span style="display: flex; align-items: center; gap: 3px;">
                <span class="wireless-badge vzw" style="display: inline-flex; align-items: center; background: #e74c3c; color: white; padding: 2px 6px; border-radius: 3px; font-size: 9px; font-weight: bold; border: 1px solid #c0392b;">📶 VZW</span>
                <span style="color: #ecf0f1;">{{ badge_counts.vzw }}</span>
            </span>
            <span style="display: flex; align-items: center; gap: 3px;">
                <span class="wireless-badge att" style="display: inline-flex; align-items: center; background: #3498db; color: white; padding: 2px 6px; border-radius: 3px; font-size: 9px; font-weight: bold; border: 1px solid #2980b9;">📶 AT&T</span>
                <span style="color: #ecf0f1;">{{ badge_counts.att }}</span>
            </span>
            <span style="display: flex; align-items: center; gap: 3px;">
                <span class="wireless-badge starlink" style="display: inline-flex; align-items: center; background: #9b59b6; color: white; padding: 2px 6px; border-radius: 3px; font-size: 9px; font-weight: bold; border: 1px solid #8e44ad;">🛰️ STAR</span>
                <span style="color: #ecf0f1;">{{ badge_counts.starlink }}</span>
            </span>
            {% endif %}
        </div>
        <div class="row-count" id="rowCount">Showing 0 of 0 rows</div>
    </div>'''

if old_header in template_content:
    template_content = template_content.replace(old_header, new_header)
    with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
        f.write(template_content)
    print("✅ Added badge counters to test template header")
else:
    print("❌ Could not find header container in template")

print("\nBadge counters added to test page header!")
print("Format: [DSR Badge] Count [VZW Badge] Count [AT&T Badge] Count [STARLINK Badge] Count")
print("Location: Top right, left of the row count")