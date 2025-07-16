#!/usr/bin/env python3
"""
Add wireless badges to the test template
"""

# Read the test template
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

print("=== ADDING WIRELESS BADGES TO TEST TEMPLATE ===\n")

# Add wireless badge CSS after the DSR badge CSS
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

# Insert wireless CSS after DSR CSS
if dsr_badge_css in content:
    content = content.replace(dsr_badge_css, dsr_badge_css + wireless_badge_css)
    print("✅ Added wireless badge CSS")
else:
    print("❌ Could not find DSR badge CSS")

# Update the provider cells to include wireless badges
wan1_provider_old = '''<td class="provider-cell">
                            <span class="provider-text">{{ entry.wan1.provider if entry.wan1.provider else 'N/A' }}</span>
                            {% if entry.wan1.match_info and entry.wan1.match_info.dsr_verified %}
                                <span class="dsr-badge">DSR</span>
                            {% endif %}
                        </td>'''

wan1_provider_new = '''<td class="provider-cell">
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

wan2_provider_old = '''<td class="provider-cell">
                            <span class="provider-text">{{ entry.wan2.provider if entry.wan2.provider else 'N/A' }}</span>
                            {% if entry.wan2.match_info and entry.wan2.match_info.dsr_verified %}
                                <span class="dsr-badge">DSR</span>
                            {% endif %}
                        </td>'''

wan2_provider_new = '''<td class="provider-cell">
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

# Update WAN1 provider cell
if wan1_provider_old in content:
    content = content.replace(wan1_provider_old, wan1_provider_new)
    print("✅ Added wireless badges to WAN1 provider column")
else:
    print("❌ Could not find WAN1 provider cell")

# Update WAN2 provider cell  
if wan2_provider_old in content:
    content = content.replace(wan2_provider_old, wan2_provider_new)
    print("✅ Added wireless badges to WAN2 provider column")
else:
    print("❌ Could not find WAN2 provider cell")

# Write the updated template
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("\nTemplate updated with wireless badges!")
print("Badges:")
print("  📶 VZW (red) - Verizon Wireless")
print("  📶 AT&T (blue) - AT&T Wireless") 
print("  🛰️ STAR (purple) - Starlink")