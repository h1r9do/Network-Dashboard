#!/usr/bin/env python3
"""
Fix provider filter dropdown issues - remove duplicates and clean up
"""

print("=== FIXING PROVIDER FILTER DROPDOWNS ===\n")

# Read the template file
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# Fix WAN1 provider filter to use unique providers
old_wan1_filter = '''                <select id="wan1ProviderFilter">
                    <option value="">All WAN1 Providers</option>
                    {% for network in grouped_data %}
                        {% if network.wan1.provider %}
                            <option value="{{ network.wan1.provider }}">{{ network.wan1.provider }}</option>
                        {% endif %}
                    {% endfor %}
                </select>'''

new_wan1_filter = '''                <select id="wan1ProviderFilter">
                    <option value="">All WAN1 Providers</option>
                    {% set wan1_providers = [] %}
                    {% for network in grouped_data %}
                        {% if network.wan1.provider and network.wan1.provider not in wan1_providers %}
                            {% set _ = wan1_providers.append(network.wan1.provider) %}
                        {% endif %}
                    {% endfor %}
                    {% for provider in wan1_providers|sort %}
                        <option value="{{ provider }}">{{ provider }}</option>
                    {% endfor %}
                </select>'''

if old_wan1_filter in content:
    content = content.replace(old_wan1_filter, new_wan1_filter)
    print("✅ Fixed WAN1 provider filter - removed duplicates and sorted")
else:
    print("❌ Could not find WAN1 provider filter")

# Fix WAN2 provider filter to use unique providers
old_wan2_filter = '''                <select id="wan2ProviderFilter">
                    <option value="">All WAN2 Providers</option>
                    {% for network in grouped_data %}
                        {% if network.wan2.provider %}
                            <option value="{{ network.wan2.provider }}">{{ network.wan2.provider }}</option>
                        {% endif %}
                    {% endfor %}
                </select>'''

new_wan2_filter = '''                <select id="wan2ProviderFilter">
                    <option value="">All WAN2 Providers</option>
                    {% set wan2_providers = [] %}
                    {% for network in grouped_data %}
                        {% if network.wan2.provider and network.wan2.provider not in wan2_providers %}
                            {% set _ = wan2_providers.append(network.wan2.provider) %}
                        {% endif %}
                    {% endfor %}
                    {% for provider in wan2_providers|sort %}
                        <option value="{{ provider }}">{{ provider }}</option>
                    {% endfor %}
                </select>'''

if old_wan2_filter in content:
    content = content.replace(old_wan2_filter, new_wan2_filter)
    print("✅ Fixed WAN2 provider filter - removed duplicates and sorted")
else:
    print("❌ Could not find WAN2 provider filter")

# Check for any duplicate CSS that might be causing issues
css_duplicates = content.count('.filter-control:nth-child(2) { width: 32.34375%; }')
if css_duplicates > 1:
    print(f"⚠️ Found {css_duplicates} duplicate CSS rules for filter controls")
    
    # Remove duplicate CSS blocks
    # Find and remove the second occurrence of the filter control CSS block
    import re
    css_pattern = r'\.filter-control \{\s+display: table-cell;\s+padding: 5px;\s+border-right: 1px solid #ddd;\s+vertical-align: top;\s+\}.*?\.filter-control:last-child \{\s+border-right: none;\s+\}'
    matches = list(re.finditer(css_pattern, content, re.DOTALL))
    
    if len(matches) > 1:
        # Remove the second match (keep the first one)
        start, end = matches[1].span()
        content = content[:start] + content[end:]
        print("✅ Removed duplicate CSS block")

# Write the cleaned content
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("\nProvider filters updated:")
print("- Removed duplicate provider entries")
print("- Sorted providers alphabetically") 
print("- Cleaned up any duplicate CSS")
print("\nThis should fix the 'weird text' in provider filters!")