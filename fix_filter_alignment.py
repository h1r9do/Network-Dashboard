#!/usr/bin/env python3
"""
Fix the filter grid alignment after removing role columns
"""

import re

def fix_filter_alignment():
    # Read the template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'r') as f:
        content = f.read()
    
    # Fix the grid-template-columns to match the 8 columns we now have
    # Site Name, WAN1 Provider, WAN1 Speed, WAN1 Cost, WAN2 Provider, WAN2 Speed, WAN2 Cost, Action
    content = re.sub(
        r'grid-template-columns: repeat\(10, 1fr\);',
        'grid-template-columns: repeat(8, 1fr);',
        content
    )
    
    # Find the filter controls section and rebuild it properly
    # Look for the existing filter controls
    filter_start = content.find('<div class="filter-controls">')
    filter_end = content.find('</div>', filter_start) + 6
    
    new_filters = '''<div class="filter-controls">
            <div class="filter-control">
                <input type="text" id="siteFilter" placeholder="Filter Site Name...">
            </div>
            <div class="filter-control">
                <select id="wan1ProviderFilter">
                    <option value="">All WAN1 Providers</option>
                </select>
            </div>
            <div class="filter-control">
                <select id="wan1SpeedFilter">
                    <option value="">All WAN1 Speeds</option>
                </select>
            </div>
            <div class="filter-control">
                <input type="text" id="wan1CostFilter" placeholder="Filter WAN1 Cost...">
            </div>
            <div class="filter-control">
                <select id="wan2ProviderFilter">
                    <option value="">All WAN2 Providers</option>
                </select>
            </div>
            <div class="filter-control">
                <select id="wan2SpeedFilter">
                    <option value="">All WAN2 Speeds</option>
                </select>
            </div>
            <div class="filter-control">
                <input type="text" id="wan2CostFilter" placeholder="Filter WAN2 Cost...">
            </div>
            <div class="filter-control">
                <!-- Empty for Action column -->
            </div>
        </div>'''
    
    # Replace the filter controls section
    content = content[:filter_start] + new_filters + content[filter_end:]
    
    # Update the JavaScript filter initialization to use correct column indexes
    # After removing columns 4 and 8, the new column indexes are:
    # 0: Site Name, 1: WAN1 Provider, 2: WAN1 Speed, 3: WAN1 Cost, 4: WAN2 Provider, 5: WAN2 Speed, 6: WAN2 Cost, 7: Action
    
    # Update the initFilters function
    content = re.sub(
        r'initProviderFilter\(1, \'#wan1ProviderFilter\'\);',
        'initProviderFilter(1, \'#wan1ProviderFilter\');',
        content
    )
    
    content = re.sub(
        r'initProviderFilter\(5, \'#wan2ProviderFilter\'\);',
        'initProviderFilter(4, \'#wan2ProviderFilter\');',
        content
    )
    
    # Save the fixed template
    with open('/usr/local/bin/templates/dsrcircuits_beta_no_roles.html', 'w') as f:
        f.write(content)
    
    print("✅ Fixed filter alignment for 8-column layout")

if __name__ == "__main__":
    fix_filter_alignment()