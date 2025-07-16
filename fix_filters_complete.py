#!/usr/bin/env python3
"""
Fix the broken filter section completely
"""

import re

def fix_filters_complete():
    # Read the template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'r') as f:
        content = f.read()
    
    # Find and replace the entire filter controls section
    filter_start = content.find('<div class="filter-controls">')
    if filter_start == -1:
        print("❌ Could not find filter-controls section")
        return
    
    # Find the end of the filter controls section
    filter_end = content.find('</div>', filter_start)
    temp_pos = filter_end + 6
    
    # Keep looking for the closing div that matches the opening
    brace_count = 1
    pos = filter_start + len('<div class="filter-controls">')
    
    while pos < len(content) and brace_count > 0:
        if content[pos:pos+5] == '<div ':
            brace_count += 1
        elif content[pos:pos+6] == '</div>':
            brace_count -= 1
            if brace_count == 0:
                filter_end = pos + 6
                break
        pos += 1
    
    # Create the complete filter controls section
    new_filters = '''<div class="filter-controls">
            <div class="filter-control">
                <input type="text" id="siteFilter" placeholder="Filter Site Name...">
            </div>
            <div class="filter-control">
                <select id="wan1ProviderFilter">
                    <option value="">All WAN1 Providers</option>
                    {% for network in grouped_data %}
                        {% if network.wan1.provider %}
                            <option value="{{ network.wan1.provider }}">{{ network.wan1.provider }}</option>
                        {% endif %}
                    {% endfor %}
                </select>
            </div>
            <div class="filter-control">
                <select id="wan1SpeedFilter">
                    <option value="">All WAN1 Speeds</option>
                    {% for network in grouped_data %}
                        {% if network.wan1.speed %}
                            <option value="{{ network.wan1.speed }}">{{ network.wan1.speed }}</option>
                        {% endif %}
                    {% endfor %}
                </select>
            </div>
            <div class="filter-control">
                <input type="text" id="wan1CostFilter" placeholder="Filter WAN1 Cost...">
            </div>
            <div class="filter-control">
                <select id="wan2ProviderFilter">
                    <option value="">All WAN2 Providers</option>
                    {% for network in grouped_data %}
                        {% if network.wan2.provider %}
                            <option value="{{ network.wan2.provider }}">{{ network.wan2.provider }}</option>
                        {% endif %}
                    {% endfor %}
                </select>
            </div>
            <div class="filter-control">
                <select id="wan2SpeedFilter">
                    <option value="">All WAN2 Speeds</option>
                    {% for network in grouped_data %}
                        {% if network.wan2.speed %}
                            <option value="{{ network.wan2.speed }}">{{ network.wan2.speed }}</option>
                        {% endif %}
                    {% endfor %}
                </select>
            </div>
            <div class="filter-control">
                <input type="text" id="wan2CostFilter" placeholder="Filter WAN2 Cost...">
            </div>
            <div class="filter-control">
                <!-- Empty for Action column -->
            </div>
        </div>'''
    
    # Replace the broken section
    content = content[:filter_start] + new_filters + content[filter_end:]
    
    # Save the fixed template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'w') as f:
        f.write(content)
    
    print("✅ Fixed complete filter section with 8 properly aligned controls")

if __name__ == "__main__":
    fix_filters_complete()