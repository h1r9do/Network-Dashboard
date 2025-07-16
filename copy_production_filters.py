#!/usr/bin/env python3
"""
Copy working filter code from production to test template
"""

print("=== COPYING PRODUCTION FILTERS TO TEST ===\n")

with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# Remove all the broken filter code and replace with production version
# Find and remove current initFilters and related functions
import re

# Remove everything from initFilters to the debug code
pattern = r'function initFilters\(\).*?(?=// Simple debugging|// ============ COMPREHENSIVE DEBUGGING|$)'
content = re.sub(pattern, '', content, flags=re.DOTALL)

# Now insert the working production filter code
production_filters = '''        function initFilters() {
            initProviderFilter(1, '#wan1ProviderFilter');
            initProviderFilter(4, '#wan2ProviderFilter');
            initDropdownFilter(2, '#wan1SpeedFilter');
            initDropdownFilter(5, '#wan2SpeedFilter');
            
            $('#siteFilter').on('keyup', function() {
                table.column(0).search(this.value).draw();
            });
            
            $('#wan1CostFilter').on('keyup', function() {
                table.column(3).search(this.value).draw();
            });
            
            $('#wan2CostFilter').on('keyup', function() {
                table.column(6).search(this.value).draw();
            });
            
            $('#clearFilters').on('click', function() {
                $('#siteFilter').val('');
                $('#wan1ProviderFilter').val('').trigger('change');
                $('#wan2ProviderFilter').val('').trigger('change');
                $('#wan1SpeedFilter').val('').trigger('change');
                $('#wan2SpeedFilter').val('').trigger('change');
                $('#wan1CostFilter').val('');
                $('#wan2CostFilter').val('');
                table.search('').columns().search('').draw();
            });
        }
        
        // Provider filter
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
                return d && d !== 'N/A' && d !== 'null' && d.trim() !== '';
            });
            
            providers.each(function(d, j) {
                select.append('<option value="' + d + '">' + d + '</option>');
            });
            
            $(selector).select2({
                placeholder: "Select or type a provider",
                allowClear: true,
                width: '100%'
            });
        }
        
        // Dropdown filter
        function initDropdownFilter(columnIndex, selector) {
            var column = table.column(columnIndex);
            var select = $(selector)
                .empty()
                .append('<option value="">All WAN ' + (columnIndex === 2 ? '1' : '2') + ' Speeds</option>')
                .on('change', function() {
                    var val = $(this).val();
                    if (val) {
                        column.search('^' + val + '$', true, false).draw();
                    } else {
                        column.search('').draw();
                    }
                });
            
            var speeds = column.data().unique().sort().filter(function(d) {
                return d && d !== 'N/A' && d !== 'null' && d.trim() !== '';
            });
            
            speeds.each(function(d, j) {
                select.append('<option value="' + d + '">' + d + '</option>');
            });
        }
        
'''

# Find where to insert (before the debug code or at end of script section)
if '// Simple debugging' in content:
    insert_point = content.find('// Simple debugging')
    content = content[:insert_point] + production_filters + '\n        ' + content[insert_point:]
elif '// ============ COMPREHENSIVE DEBUGGING' in content:
    insert_point = content.find('// ============ COMPREHENSIVE DEBUGGING')
    content = content[:insert_point] + production_filters + '\n        ' + content[insert_point:]
else:
    # Insert before closing script tag
    content = content.replace('    </script>', production_filters + '\n    </script>')

print("✅ Copied production filter code")

# Now we need to make sure the provider filter can handle the badges in the test page
# The issue is that column.data() might return HTML with badges
# Let's override initProviderFilter to extract clean text
override_provider = '''
        // Override provider filter for test page to handle badges
        var originalInitProviderFilter = initProviderFilter;
        initProviderFilter = function(columnIndex, selector) {
            var column = table.column(columnIndex);
            var select = $(selector)
                .empty()
                .append('<option value="">All WAN ' + (columnIndex === 1 ? '1' : '2') + ' Providers</option>')
                .on('change', function() {
                    var val = $(this).val();
                    if (val) {
                        // Custom search that checks the provider text, not the full HTML
                        $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                            var row = table.row(dataIndex).node();
                            var cell = $(row).find('td').eq(columnIndex);
                            var provider = cell.attr('data-provider') || cell.find('.provider-text').text().trim() || cell.text().trim();
                            // Remove any badge text
                            provider = provider.replace(/DSR|VZW|AT&T|STAR|📶|🛰️/g, '').trim();
                            return provider === val;
                        });
                        table.draw();
                        $.fn.dataTable.ext.search.pop();
                    } else {
                        column.search('').draw();
                    }
                });
            
            // Get unique providers from the cells, not the raw data
            var providers = new Set();
            column.nodes().each(function() {
                var cell = $(this);
                var provider = cell.attr('data-provider') || cell.find('.provider-text').text().trim() || cell.text().trim();
                // Remove any badge text
                provider = provider.replace(/DSR|VZW|AT&T|STAR|📶|🛰️/g, '').trim();
                if (provider && provider !== 'N/A' && provider !== 'null' && provider !== '') {
                    providers.add(provider);
                }
            });
            
            // Convert to sorted array and populate dropdown
            Array.from(providers).sort().forEach(function(d) {
                select.append('<option value="' + d + '">' + d + '</option>');
            });
            
            $(selector).select2({
                placeholder: "Select or type a provider",
                allowClear: true,
                width: '100%'
            });
        };
'''

# Add the override after the filter functions
content = content.replace(production_filters, production_filters + override_provider)

# Write the updated content
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("✅ Added provider filter override for badge handling")
print("✅ Filters should now work exactly like production!")
print("\nThe filters will:")
print("- Extract clean provider text without badges")
print("- Populate dropdowns from actual table data")
print("- Filter correctly when you select a provider")