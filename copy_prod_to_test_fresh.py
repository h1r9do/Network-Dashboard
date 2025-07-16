#!/usr/bin/env python3
"""
Copy production template to test and add only the new features
"""

print("=== STARTING FRESH - COPYING PRODUCTION TO TEST ===\n")

import shutil

# First, backup the current test template
shutil.copy('/usr/local/bin/templates/dsrcircuits_test.html', 
            '/usr/local/bin/templates/dsrcircuits_test.backup.html')
print("✅ Backed up current test template")

# Copy production template to test
shutil.copy('/usr/local/bin/Main/templates/dsrcircuits.html',
            '/usr/local/bin/templates/dsrcircuits_test.html')
print("✅ Copied production template to test")

# Now let's add ONLY the new features to the test template
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# 1. Add the wireless badge CSS after the DSR badge CSS
dsr_badge_css = '''.dsr-badge {
            display: inline-flex;
            align-items: center;
            background: #2ecc71;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
            border: 1px solid #27ae60;
            vertical-align: middle;
            float: right;
            margin-right: 5px;
        }'''

wireless_badge_css = '''
        .wireless-badge {
            display: inline-flex;
            align-items: center;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 9px;
            font-weight: bold;
            vertical-align: middle;
            float: right;
            margin-right: 3px;
            margin-left: 3px;
        }
        
        .wireless-badge.vzw {
            background: #e74c3c;
            border: 1px solid #c0392b;
        }
        
        .wireless-badge.att {
            background: #3498db;
            border: 1px solid #2980b9;
        }
        
        .wireless-badge.starlink {
            background: #9b59b6;
            border: 1px solid #8e44ad;
        }'''

if dsr_badge_css in content:
    content = content.replace(dsr_badge_css, dsr_badge_css + wireless_badge_css)
    print("✅ Added wireless badge CSS")

# 2. Add the badge display logic to provider cells
# Find the WAN1 provider cell
wan1_provider_cell = '''<td class="provider-cell">
                            <span class="provider-text">{{ entry.wan1.provider if entry.wan1.provider else 'N/A' }}</span>
                            {% if entry.wan1.match_info and entry.wan1.match_info.dsr_verified %}
                                <span class="dsr-badge">DSR</span>
                            {% endif %}
                        </td>'''

wan1_with_wireless = '''<td class="provider-cell">
                            <span class="provider-text">{{ entry.wan1.provider if entry.wan1.provider else 'N/A' }}</span>
                            {% if entry.wan1.wireless_badge %}
                                {% if entry.wan1.wireless_badge == 'VZW' %}
                                    <span class="wireless-badge vzw">📶 VZW</span>
                                {% elif entry.wan1.wireless_badge == 'ATT' %}
                                    <span class="wireless-badge att">📶 AT&T</span>
                                {% elif entry.wan1.wireless_badge == 'STARLINK' %}
                                    <span class="wireless-badge starlink">🛰️ STAR</span>
                                {% endif %}
                            {% endif %}
                            {% if entry.wan1.match_info and entry.wan1.match_info.dsr_verified %}
                                <span class="dsr-badge">DSR</span>
                            {% endif %}
                        </td>'''

content = content.replace(wan1_provider_cell, wan1_with_wireless)
print("✅ Added wireless badges to WAN1 provider cell")

# Same for WAN2
wan2_provider_cell = '''<td class="provider-cell">
                            <span class="provider-text">{{ entry.wan2.provider if entry.wan2.provider else 'N/A' }}</span>
                            {% if entry.wan2.match_info and entry.wan2.match_info.dsr_verified %}
                                <span class="dsr-badge">DSR</span>
                            {% endif %}
                        </td>'''

wan2_with_wireless = '''<td class="provider-cell">
                            <span class="provider-text">{{ entry.wan2.provider if entry.wan2.provider else 'N/A' }}</span>
                            {% if entry.wan2.wireless_badge %}
                                {% if entry.wan2.wireless_badge == 'VZW' %}
                                    <span class="wireless-badge vzw">📶 VZW</span>
                                {% elif entry.wan2.wireless_badge == 'ATT' %}
                                    <span class="wireless-badge att">📶 AT&T</span>
                                {% elif entry.wan2.wireless_badge == 'STARLINK' %}
                                    <span class="wireless-badge starlink">🛰️ STAR</span>
                                {% endif %}
                            {% endif %}
                            {% if entry.wan2.match_info and entry.wan2.match_info.dsr_verified %}
                                <span class="dsr-badge">DSR</span>
                            {% endif %}
                        </td>'''

content = content.replace(wan2_provider_cell, wan2_with_wireless)
print("✅ Added wireless badges to WAN2 provider cell")

# 3. Add badge counters to header
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
        {% if last_updated %}
        <div style="position: absolute; top: 45px; right: 15px; font-size: 12px; color: #bdc3c7; font-style: italic;">
            Last updated: {{ last_updated }}
        </div>
        {% endif %}
    </div>'''

content = content.replace(old_header, new_header)
print("✅ Added badge counters and last updated to header")

# Write the updated content
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("\n✅ Fresh start complete!")
print("The test template now has:")
print("  - All working production filters")
print("  - Wireless badges (VZW, AT&T, Starlink)")
print("  - Badge counters in header")
print("  - Last updated timestamp")
print("\nThe test route needs to pass: wireless_badge, badge_counts, and last_updated")