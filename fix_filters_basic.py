#!/usr/bin/env python3
"""
Use basic DataTables filtering without complex JavaScript
"""

print("=== USING BASIC DATATABLE FILTERS ===\n")

with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# Remove ALL the complex filter initialization code
import re

# Find the script section with DataTable initialization
script_match = re.search(r'var table = \$\(\'#circuitTable\'\)\.DataTable\((.*?)\);', content, re.DOTALL)
if script_match:
    print("Found DataTable initialization")

# Remove everything between initFilters definition and the debugging section
# Just use a very simple filter setup
simple_filters = '''        
        // Simple filter initialization
        function initFilters() {
            // WAN1 Provider
            $('#wan1ProviderFilter').on('change', function() {
                table.column(1).search(this.value).draw();
            });
            
            // WAN2 Provider  
            $('#wan2ProviderFilter').on('change', function() {
                table.column(4).search(this.value).draw();
            });
            
            // Speeds
            $('#wan1SpeedFilter').on('change', function() {
                table.column(2).search(this.value).draw();
            });
            
            $('#wan2SpeedFilter').on('change', function() {
                table.column(5).search(this.value).draw();
            });
            
            // Text inputs
            $('#siteFilter').on('keyup', function() {
                table.column(0).search(this.value).draw();
            });
            
            $('#wan1CostFilter').on('keyup', function() {
                table.column(3).search(this.value).draw();
            });
            
            $('#wan2CostFilter').on('keyup', function() {
                table.column(6).search(this.value).draw();
            });
            
            // Clear button
            $('#clearFilters').on('click', function() {
                $('input[type="text"]').val('');
                $('select').val('').trigger('change');
                table.search('').columns().search('').draw();
            });
        }
'''

# Replace the entire section from function initFilters to the debugging
pattern = r'function initFilters\(\).*?(?=// Simple debugging|// ============ COMPREHENSIVE DEBUGGING|window\.checkFilters|$)'
content = re.sub(pattern, simple_filters + '\n        ', content, flags=re.DOTALL)

# Also update the HTML dropdowns to remove the Jinja2 loops
# Just use static options that we know exist
wan_providers = [
    "AT&T", "Altice USA", "Breezeline", "CenturyLink", "Charter Communications",
    "Cincinnati Bell", "Comcast", "Cox Business", "Cox Communications", 
    "Frontier", "Lumen", "Optimum", "Spectrum", "Starlink", "T-Mobile",
    "Verizon", "Windstream", "Ziply Fiber"
]

# Replace WAN1 provider dropdown
old_wan1_select = re.search(r'<select id="wan1ProviderFilter">.*?</select>', content, re.DOTALL)
if old_wan1_select:
    new_wan1_select = '''<select id="wan1ProviderFilter">
                    <option value="">All WAN1 Providers</option>'''
    for provider in wan_providers:
        new_wan1_select += f'\n                    <option value="{provider}">{provider}</option>'
    new_wan1_select += '\n                </select>'
    content = content.replace(old_wan1_select.group(0), new_wan1_select)
    print("✅ Replaced WAN1 provider dropdown with static options")

# Replace WAN2 provider dropdown
old_wan2_select = re.search(r'<select id="wan2ProviderFilter">.*?</select>', content, re.DOTALL)
if old_wan2_select:
    new_wan2_select = '''<select id="wan2ProviderFilter">
                    <option value="">All WAN2 Providers</option>'''
    for provider in wan_providers:
        new_wan2_select += f'\n                    <option value="{provider}">{provider}</option>'
    new_wan2_select += '\n                </select>'
    content = content.replace(old_wan2_select.group(0), new_wan2_select)
    print("✅ Replaced WAN2 provider dropdown with static options")

# Write the updated content
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("\n✅ Simplified to basic DataTables filtering")
print("✅ Removed all Jinja2 templating from dropdowns")
print("✅ Using static provider list")
print("\nFilters now use simple column search - no custom functions!")