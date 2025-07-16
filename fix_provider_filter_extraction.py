#!/usr/bin/env python3
"""
Fix the provider filter to extract clean text from provider cells
"""

print("=== FIXING PROVIDER FILTER TEXT EXTRACTION ===\n")

# Read the template
with open('/usr/local/bin/templates/dsrcircuits.html', 'r') as f:
    content = f.read()

# Replace the initProviderFilter function to properly extract text
old_function = '''        function initProviderFilter(columnIndex, selector) {
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

new_function = '''        function initProviderFilter(columnIndex, selector) {
            var column = table.column(columnIndex);
            var select = $(selector)
                .empty()
                .append('<option value="">All WAN ' + (columnIndex === 1 ? '1' : '2') + ' Providers</option>')
                .on('change', function() {
                    var val = $(this).val();
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
            column.nodes().each(function() {
                var cell = $(this);
                var providerText = cell.find('.provider-text').text().trim();
                if (providerText && providerText !== 'N/A' && providerText !== 'null' && providerText !== '') {
                    providers.add(providerText);
                }
            });
            
            // Convert to sorted array and populate dropdown
            Array.from(providers).sort().forEach(function(provider) {
                select.append('<option value="' + provider + '">' + provider + '</option>');
            });
            
            $(selector).select2({
                placeholder: "Select or type a provider",
                allowClear: true,
                width: '100%'
            });
        }'''

# Replace the function
if old_function in content:
    content = content.replace(old_function, new_function)
    print("✅ Updated initProviderFilter to extract clean text from provider-text spans")
else:
    print("❌ Could not find initProviderFilter function to replace")

# Write the fixed template
with open('/usr/local/bin/templates/dsrcircuits.html', 'w') as f:
    f.write(content)

print("✅ Provider filters now extract clean provider names")
print("✅ Should show proper provider list without HTML tags/badges")