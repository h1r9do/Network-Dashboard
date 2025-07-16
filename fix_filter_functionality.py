#!/usr/bin/env python3
"""
Fix filter functionality to actually filter the DataTable
"""

print("=== FIXING FILTER FUNCTIONALITY ===\n")

with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# The issue is that the column search needs to search the actual text content, not the HTML
# We need to use custom search functions that check the provider text specifically

# Find and replace the provider filter handlers
old_wan1_handler = '''            // Provider filter handlers
            $('#wan1ProviderFilter').on('change', function() {
                var val = $(this).val();
                table.column(1).search(val ? '^' + $.fn.dataTable.util.escapeRegex(val) + '$' : '', true, false).draw();
            });'''

new_wan1_handler = '''            // Provider filter handlers - custom search for provider text
            $('#wan1ProviderFilter').on('change', function() {
                var val = $(this).val();
                
                // Remove any previous custom search
                $.fn.dataTable.ext.search = $.fn.dataTable.ext.search.filter(function(func) {
                    return func.name !== 'wan1ProviderSearch';
                });
                
                if (val) {
                    // Add custom search function
                    function wan1ProviderSearch(settings, data, dataIndex) {
                        var row = table.row(dataIndex).node();
                        var cell = $(row).find('td').eq(1); // WAN1 Provider column
                        var provider = cell.attr('data-provider') || cell.find('.provider-text').text().trim();
                        return provider === val;
                    }
                    $.fn.dataTable.ext.search.push(wan1ProviderSearch);
                }
                
                table.draw();
            });'''

if old_wan1_handler in content:
    content = content.replace(old_wan1_handler, new_wan1_handler)
    print("✅ Fixed WAN1 provider filter handler")

old_wan2_handler = '''            $('#wan2ProviderFilter').on('change', function() {
                var val = $(this).val();
                table.column(4).search(val ? '^' + $.fn.dataTable.util.escapeRegex(val) + '$' : '', true, false).draw();
            });'''

new_wan2_handler = '''            $('#wan2ProviderFilter').on('change', function() {
                var val = $(this).val();
                
                // Remove any previous custom search
                $.fn.dataTable.ext.search = $.fn.dataTable.ext.search.filter(function(func) {
                    return func.name !== 'wan2ProviderSearch';
                });
                
                if (val) {
                    // Add custom search function
                    function wan2ProviderSearch(settings, data, dataIndex) {
                        var row = table.row(dataIndex).node();
                        var cell = $(row).find('td').eq(4); // WAN2 Provider column
                        var provider = cell.attr('data-provider') || cell.find('.provider-text').text().trim();
                        return provider === val;
                    }
                    $.fn.dataTable.ext.search.push(wan2ProviderSearch);
                }
                
                table.draw();
            });'''

if old_wan2_handler in content:
    content = content.replace(old_wan2_handler, new_wan2_handler)
    print("✅ Fixed WAN2 provider filter handler")

# Also need to update the clear filters function to clear custom searches
old_clear = '''            $('#clearFilters').on('click', function() {
                $('#siteFilter').val('');
                $('#wan1ProviderFilter').val('').trigger('change');
                $('#wan2ProviderFilter').val('').trigger('change');
                $('#wan1SpeedFilter').val('').trigger('change');
                $('#wan2SpeedFilter').val('').trigger('change');
                $('#wan1CostFilter').val('');
                $('#wan2CostFilter').val('');
                table.search('').columns().search('').draw();
            });'''

new_clear = '''            // Clear filters button
            $('#clearFilters').on('click', function() {
                $('#siteFilter').val('');
                $('#wan1ProviderFilter').val('').trigger('change');
                $('#wan2ProviderFilter').val('').trigger('change');
                $('#wan1SpeedFilter').val('').trigger('change');
                $('#wan2SpeedFilter').val('').trigger('change');
                $('#wan1CostFilter').val('');
                $('#wan2CostFilter').val('');
                
                // Clear all custom searches
                $.fn.dataTable.ext.search = [];
                
                table.search('').columns().search('').draw();
            });'''

# Find the clear filters handler and replace it
import re
clear_match = re.search(r"\$\('#clearFilters'\)\.on\('click'.*?\}\);", content, re.DOTALL)
if clear_match:
    content = content.replace(clear_match.group(0), new_clear)
    print("✅ Updated clear filters to remove custom searches")

# Write the updated content
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("\nFilter functionality fixed:")
print("- Provider filters use custom search functions")
print("- Searches actual provider text, not HTML")
print("- Clear filters removes all custom searches")
print("- Filters should now properly filter the table!")