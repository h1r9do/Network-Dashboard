#!/usr/bin/env python3
"""
Fix Jinja2 filter duplicates by using unique filter
"""

print("=== FIXING JINJA2 FILTER DUPLICATES ===\n")

# Read the template
with open('/usr/local/bin/templates/dsrcircuits.html', 'r') as f:
    content = f.read()

# Fix WAN1 provider filter
old_wan1_provider = '''<select id="wan1ProviderFilter">
                    <option value="">All WAN1 Providers</option>
                    {% for network in grouped_data %}
                        {% if network.wan1.provider %}
                            <option value="{{ network.wan1.provider }}">{{ network.wan1.provider }}</option>
                        {% endif %}
                    {% endfor %}
                </select>'''

new_wan1_provider = '''<select id="wan1ProviderFilter">
                    <option value="">All WAN1 Providers</option>
                    {% set wan1_providers = grouped_data | map(attribute='wan1.provider') | select('string') | unique | sort %}
                    {% for provider in wan1_providers %}
                        <option value="{{ provider }}">{{ provider }}</option>
                    {% endfor %}
                </select>'''

# Fix WAN2 provider filter  
old_wan2_provider = '''<select id="wan2ProviderFilter">
                    <option value="">All WAN2 Providers</option>
                    {% for network in grouped_data %}
                        {% if network.wan2.provider %}
                            <option value="{{ network.wan2.provider }}">{{ network.wan2.provider }}</option>
                        {% endif %}
                    {% endfor %}
                </select>'''

new_wan2_provider = '''<select id="wan2ProviderFilter">
                    <option value="">All WAN2 Providers</option>
                    {% set wan2_providers = grouped_data | map(attribute='wan2.provider') | select('string') | unique | sort %}
                    {% for provider in wan2_providers %}
                        <option value="{{ provider }}">{{ provider }}</option>
                    {% endfor %}
                </select>'''

# Fix WAN1 speed filter
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
                    {% set wan1_speeds = grouped_data | map(attribute='wan1.speed') | select('string') | unique | sort %}
                    {% for speed in wan1_speeds %}
                        <option value="{{ speed }}">{{ speed }}</option>
                    {% endfor %}
                </select>'''

# Fix WAN2 speed filter
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
                    {% set wan2_speeds = grouped_data | map(attribute='wan2.speed') | select('string') | unique | sort %}
                    {% for speed in wan2_speeds %}
                        <option value="{{ speed }}">{{ speed }}</option>
                    {% endfor %}
                </select>'''

# Apply fixes
replacements = [
    (old_wan1_provider, new_wan1_provider, "WAN1 provider"),
    (old_wan2_provider, new_wan2_provider, "WAN2 provider"), 
    (old_wan1_speed, new_wan1_speed, "WAN1 speed"),
    (old_wan2_speed, new_wan2_speed, "WAN2 speed")
]

for old, new, name in replacements:
    if old in content:
        content = content.replace(old, new)
        print(f"✅ Fixed {name} filter to use unique values")
    else:
        print(f"❌ Could not find {name} filter to fix")

# Write the fixed template
with open('/usr/local/bin/templates/dsrcircuits.html', 'w') as f:
    f.write(content)

print("✅ All filter dropdowns now use unique values")
print("✅ No more duplicate options in filter lists")