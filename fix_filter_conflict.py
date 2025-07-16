#!/usr/bin/env python3
"""
Fix the filter conflict between Jinja2 and JavaScript population
"""

print("=== FIXING FILTER POPULATION CONFLICT ===\n")

# Read the template
with open('/usr/local/bin/templates/dsrcircuits.html', 'r') as f:
    content = f.read()

# Replace the WAN1 provider filter with clean version
old_wan1_filter = '''<select id="wan1ProviderFilter">
                    <option value="">All WAN1 Providers</option>
                    {% for network in grouped_data %}
                        {% if network.wan1.provider %}
                            <option value="{{ network.wan1.provider }}">{{ network.wan1.provider }}</option>
                        {% endif %}
                    {% endfor %}
                </select>'''

new_wan1_filter = '''<select id="wan1ProviderFilter">
                    <option value="">All WAN1 Providers</option>
                </select>'''

if old_wan1_filter in content:
    content = content.replace(old_wan1_filter, new_wan1_filter)
    print("✅ Cleaned WAN1 provider filter")

# Replace the WAN2 provider filter with clean version
old_wan2_filter = '''<select id="wan2ProviderFilter">
                    <option value="">All WAN2 Providers</option>
                    {% for network in grouped_data %}
                        {% if network.wan2.provider %}
                            <option value="{{ network.wan2.provider }}">{{ network.wan2.provider }}</option>
                        {% endif %}
                    {% endfor %}
                </select>'''

new_wan2_filter = '''<select id="wan2ProviderFilter">
                    <option value="">All WAN2 Providers</option>
                </select>'''

if old_wan2_filter in content:
    content = content.replace(old_wan2_filter, new_wan2_filter)
    print("✅ Cleaned WAN2 provider filter")

# Replace the WAN1 speed filter with clean version  
old_wan1_speed = '''<select id="wan1SpeedFilter">
                    <option value="">All WAN1 Speeds</option>
                    {% for network in grouped_data %}
                        {% if network.wan1.speed %}
                            <option value="{{ network.wan1.speed }}">{{ network.wan1.speed }}</option>
                        {% endif %}
                    {% endfor %}
                </select>'''

new_wan1_speed = '''<select id="wan1SpeedFilter">
                    <option value="">All WAN1 Speeds</option>
                </select>'''

if old_wan1_speed in content:
    content = content.replace(old_wan1_speed, new_wan1_speed)
    print("✅ Cleaned WAN1 speed filter")

# Replace the WAN2 speed filter with clean version
old_wan2_speed = '''<select id="wan2SpeedFilter">
                    <option value="">All WAN2 Speeds</option>
                    {% for network in grouped_data %}
                        {% if network.wan2.speed %}
                            <option value="{{ network.wan2.speed }}">{{ network.wan2.speed }}</option>
                        {% endif %}
                    {% endfor %}
                </select>'''

new_wan2_speed = '''<select id="wan2SpeedFilter">
                    <option value="">All WAN2 Speeds</option>
                </select>'''

if old_wan2_speed in content:
    content = content.replace(old_wan2_speed, new_wan2_speed)
    print("✅ Cleaned WAN2 speed filter")

# Write the fixed template
with open('/usr/local/bin/templates/dsrcircuits.html', 'w') as f:
    f.write(content)

print("✅ Removed Jinja2 filter population - JavaScript will now handle it")
print("✅ Filters should now work properly")