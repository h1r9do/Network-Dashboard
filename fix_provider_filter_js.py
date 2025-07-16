#!/usr/bin/env python3
"""
Fix provider filter JavaScript to extract clean text without badges
"""

print("=== FIXING PROVIDER FILTER JAVASCRIPT ===\n")

with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# Replace the initProviderFilter function to properly extract provider text
old_provider_filter = '''        // Provider filter
        function initProviderFilter(columnIndex, selector) {
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

new_provider_filter = '''        // Provider filter - extract clean text without badges
        function initProviderFilter(columnIndex, selector) {
            var column = table.column(columnIndex);
            var select = $(selector)
                .empty()
                .append('<option value="">All WAN ' + (columnIndex === 1 ? '1' : '2') + ' Providers</option>')
                .on('change', function() {
                    var val = $(this).val();
                    column.search(val).draw();
                });
            
            // Get unique providers from data attributes or clean text
            var providers = [];
            column.nodes().each(function() {
                var cell = $(this);
                var provider = cell.attr('data-provider') || cell.find('.provider-text').text().trim();
                if (provider && provider !== 'N/A' && provider !== 'null' && providers.indexOf(provider) === -1) {
                    providers.push(provider);
                }
            });
            
            // Sort and add to dropdown
            providers.sort().forEach(function(d) {
                select.append('<option value="' + d + '">' + d + '</option>');
            });
            
            $(selector).select2({
                placeholder: "Select or type a provider",
                allowClear: true,
                width: '100%'
            });
        }'''

if old_provider_filter in content:
    content = content.replace(old_provider_filter, new_provider_filter)
    print("✅ Fixed provider filter JavaScript to extract clean text")
else:
    print("❌ Could not find provider filter function")

# Also fix the search functionality to search the clean text
old_search = '''                    var val = $(this).val();
                    column.search(val).draw();'''

new_search = '''                    var val = $(this).val();
                    if (val) {
                        // Custom search that checks data-provider attribute
                        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                            var cell = $(table.cell(dataIndex, columnIndex).node());
                            var provider = cell.attr('data-provider') || cell.find('.provider-text').text().trim();
                            return provider.toLowerCase().indexOf(val.toLowerCase()) !== -1;
                        });
                        table.draw();
                        $.fn.dataTable.ext.search.pop();
                    } else {
                        column.search('').draw();
                    }'''

content = content.replace(old_search, new_search)

# Now fix the filtering in the main table filter functions
# Update the provider text extraction in applyFilters
old_apply_filters = '''wan1ProviderText = cells[1].getAttribute('data-provider') || cells[1].textContent.trim();'''
new_apply_filters = '''wan1ProviderText = $(cells[1]).attr('data-provider') || $(cells[1]).find('.provider-text').text().trim() || cells[1].textContent.trim();'''

content = content.replace(old_apply_filters, new_apply_filters)

old_apply_filters2 = '''wan2ProviderText = cells[4].getAttribute('data-provider') || cells[4].textContent.trim();'''  
new_apply_filters2 = '''wan2ProviderText = $(cells[4]).attr('data-provider') || $(cells[4]).find('.provider-text').text().trim() || cells[4].textContent.trim();'''

content = content.replace(old_apply_filters2, new_apply_filters2)

# Write the updated template
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("\n✅ Fixed JavaScript issues:")
print("  - Provider filter now extracts clean text from provider-text span")
print("  - Search functionality uses data-provider attribute")
print("  - Filters won't show badge text anymore")
print("\nProvider dropdown should now show clean provider names!")