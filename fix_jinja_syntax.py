#!/usr/bin/env python3
"""
Fix Jinja2 syntax in filter initialization
"""

print("=== FIXING JINJA2 TEMPLATE SYNTAX ===\n")

with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# Find the filter initialization with Jinja2 loops
import re

# Look for the initFilters function
init_filters_match = re.search(r'function initFilters\(\)\s*{.*?(?=function|\Z)', content, re.DOTALL)

if init_filters_match:
    init_filters_content = init_filters_match.group(0)
    
    # The issue is likely with the Jinja2 loops generating JavaScript
    # Need to properly escape the provider names in JavaScript
    
    old_provider_loop = '''{% for network in grouped_data %}
                {% if network.wan1.provider and network.wan1.provider != 'N/A' %}
                    if (!seenProviders1["{{ network.wan1.provider }}"]) {
                        providers1.push("{{ network.wan1.provider }}");
                        seenProviders1["{{ network.wan1.provider }}"] = true;
                    }
                {% endif %}'''
    
    new_provider_loop = '''{% for network in grouped_data %}
                {% if network.wan1.provider and network.wan1.provider != 'N/A' %}
                    if (!seenProviders1[{{ network.wan1.provider|tojson }}]) {
                        providers1.push({{ network.wan1.provider|tojson }});
                        seenProviders1[{{ network.wan1.provider|tojson }}] = true;
                    }
                {% endif %}'''
    
    if old_provider_loop in content:
        content = content.replace(old_provider_loop, new_provider_loop)
        print("✅ Fixed WAN1 provider loop to use tojson filter")
    
    # Fix all similar loops
    patterns_to_fix = [
        ('"{{ network.wan1.provider }}"', '{{ network.wan1.provider|tojson }}'),
        ('"{{ network.wan2.provider }}"', '{{ network.wan2.provider|tojson }}'),
        ('"{{ network.wan1.speed }}"', '{{ network.wan1.speed|tojson }}'),
        ('"{{ network.wan2.speed }}"', '{{ network.wan2.speed|tojson }}')
    ]
    
    for old, new in patterns_to_fix:
        if old in content:
            content = content.replace(old, new)
            print(f"✅ Replaced {old} with {new}")

# Write the fixed content
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("\n✅ Fixed Jinja2 template syntax")
print("Provider names with quotes or special characters will now be properly escaped")