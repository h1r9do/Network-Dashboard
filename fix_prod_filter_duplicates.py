#!/usr/bin/env python3
"""
Fix the duplicate provider issue in production filters
"""

print("=== FIXING PRODUCTION FILTER DUPLICATES ===\n")

with open('/usr/local/bin/Main/templates/dsrcircuits.html', 'r') as f:
    content = f.read()

# The issue is in the dropdown HTML - it's showing the provider name twice
# Let's check what's in the filter dropdowns
import re

# Find and fix the WAN1 provider dropdown
wan1_dropdown = re.search(r'<select id="wan1ProviderFilter">.*?</select>', content, re.DOTALL)
if wan1_dropdown:
    dropdown_content = wan1_dropdown.group(0)
    print("Current WAN1 dropdown:")
    print(dropdown_content[:200] + "...")
    
    # Check if it has the problematic pattern where value and text are duplicated
    if '">All WAN1 Providers</option>' in dropdown_content:
        # Replace with clean dropdown from production
        clean_dropdown = '''<select id="wan1ProviderFilter">
                    <option value="">All WAN1 Providers</option>
                </select>'''
        content = content.replace(dropdown_content, clean_dropdown)
        print("✅ Cleaned WAN1 provider dropdown")

# Same for WAN2
wan2_dropdown = re.search(r'<select id="wan2ProviderFilter">.*?</select>', content, re.DOTALL)
if wan2_dropdown:
    dropdown_content = wan2_dropdown.group(0)
    # Replace with clean dropdown
    clean_dropdown = '''<select id="wan2ProviderFilter">
                    <option value="">All WAN2 Providers</option>
                </select>'''
    content = content.replace(dropdown_content, clean_dropdown)
    print("✅ Cleaned WAN2 provider dropdown")

# Now make sure the JavaScript populates them correctly
# Find the initProviderFilter function
provider_filter_pattern = r'function initProviderFilter\(columnIndex, selector\).*?\n\s*\}'
provider_filter_match = re.search(provider_filter_pattern, content, re.DOTALL)

if provider_filter_match:
    # Replace with the correct production version
    correct_provider_filter = '''function initProviderFilter(columnIndex, selector) {
            var column = table.column(columnIndex);
            var select = $(selector)
                .empty()
                .append('<option value="">All WAN ' + (columnIndex === 1 ? '1' : '2') + ' Providers</option>')
                .on('change', function() {
                    var val = $(this).val();
                    column.search(val).draw();
                });
            
            var providers = column.data().unique().sort().filter(function(d) {
                return d && d !== 'N/A' && d !== 'null';
            });
            
            providers.each(function(d, j) {
                select.append('<option value="' + d + '">' + d + '</option>');
            });
            
            $(selector).select2({
                placeholder: "Select or type a provider",
                allowClear: true,
                width: '100%'
            });
        }'''
    
    content = re.sub(provider_filter_pattern, correct_provider_filter, content, flags=re.DOTALL)
    print("✅ Fixed initProviderFilter function")

# Write the fixed content
with open('/usr/local/bin/Main/templates/dsrcircuits.html', 'w') as f:
    f.write(content)

print("\n✅ Fixed duplicate provider issue!")
print("Dropdowns now start empty and populate from DataTable column data")