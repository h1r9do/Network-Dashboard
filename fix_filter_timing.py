#!/usr/bin/env python3
"""
Fix filter initialization timing to happen after DataTable is ready
"""

print("=== FIXING FILTER INITIALIZATION TIMING ===\n")

# Read the template
with open('/usr/local/bin/templates/dsrcircuits.html', 'r') as f:
    content = f.read()

# Find the current initialization and wrap it in a timeout
old_init = '''        // Initialize filters and row count
        initFilters();
        updateRowCount();'''

new_init = '''        // Initialize filters and row count after table is ready
        setTimeout(function() {
            initFilters();
            updateRowCount();
        }, 100);'''

if old_init in content:
    content = content.replace(old_init, new_init)
    print("✅ Added timeout to filter initialization")
else:
    # Try alternative pattern
    alt_old = '''        initFilters();
        updateRowCount();'''
    
    alt_new = '''        setTimeout(function() {
            initFilters();
            updateRowCount();
        }, 100);'''
    
    if alt_old in content:
        content = content.replace(alt_old, alt_new)
        print("✅ Added timeout to filter initialization (alternative pattern)")
    else:
        print("❌ Could not find initialization pattern")

# Also add debugging to the initProviderFilter function
debug_provider_filter = '''        function initProviderFilter(columnIndex, selector) {
            console.log('Initializing provider filter for column ' + columnIndex + ' with selector ' + selector);
            var column = table.column(columnIndex);
            var select = $(selector)
                .empty()
                .append('<option value="">All WAN ' + (columnIndex === 1 ? '1' : '2') + ' Providers</option>')
                .on('change', function() {
                    var val = $(this).val();
                    console.log('Provider filter changed to: ' + val);
                    // Use custom search that looks at the provider-text span
                    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                        if (!val) return true;
                        var cellHtml = data[columnIndex];
                        var tempDiv = $('<div>').html(cellHtml);
                        var providerText = tempDiv.find('.provider-text').text().trim();
                        return providerText === val;
                    });
                    table.draw();
                    $.fn.dataTable.ext.search.pop();
                });
            
            // Get unique providers from the actual cells, extracting text from provider-text spans
            var providers = new Set();
            var cellCount = column.nodes().length;
            console.log('Found ' + cellCount + ' cells in column ' + columnIndex);
            
            column.nodes().each(function() {
                var cell = $(this);
                var providerText = cell.find('.provider-text').text().trim();
                console.log('Cell content: "' + providerText + '"');
                if (providerText && providerText !== 'N/A' && providerText !== 'null' && providerText !== '') {
                    providers.add(providerText);
                }
            });
            
            console.log('Found ' + providers.size + ' unique providers for column ' + columnIndex);
            
            // Convert to sorted array and populate dropdown
            Array.from(providers).sort().forEach(function(provider) {
                console.log('Adding provider: ' + provider);
                select.append('<option value="' + provider + '">' + provider + '</option>');
            });
            
            $(selector).select2({
                placeholder: "Select or type a provider",
                allowClear: true,
                width: '100%'
            });
        }'''

# Replace the function with debug version
import re
current_function_pattern = r'function initProviderFilter\(columnIndex, selector\) \{.*?\}'
if re.search(current_function_pattern, content, re.DOTALL):
    content = re.sub(current_function_pattern, debug_provider_filter, content, flags=re.DOTALL)
    print("✅ Added debugging to initProviderFilter function")

# Write the fixed template
with open('/usr/local/bin/templates/dsrcircuits.html', 'w') as f:
    f.write(content)

print("✅ Filter initialization now happens after table is ready")
print("✅ Added debugging to see what's happening")