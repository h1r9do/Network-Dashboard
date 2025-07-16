#!/usr/bin/env python3
"""
Clean up the JavaScript syntax errors by restoring clean functions
"""

print("=== CLEANING UP JAVASCRIPT SYNTAX ERRORS ===\n")

# Read the template
with open('/usr/local/bin/templates/dsrcircuits.html', 'r') as f:
    content = f.read()

# Remove the broken initProviderFilter function and replace with a clean working version
import re

# Find and remove all broken initProviderFilter functions
broken_pattern = r'function initProviderFilter\(columnIndex, selector\) \{.*?\}.*?\}'
content = re.sub(broken_pattern, '', content, flags=re.DOTALL)

# Also remove any orphaned JavaScript fragments
content = re.sub(r'table\.draw\(\);\s*\$\.fn\.dataTable\.ext\.search\.pop\(\);', '', content)
content = re.sub(r'var providers = new Set\(\);.*?width: \'100%\'\s*\}\);', '', content, flags=re.DOTALL)

# Insert a clean, working initProviderFilter function before the initDropdownFilter
clean_provider_filter = '''        // Provider filter
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
                if (!d || d === 'N/A' || d === 'null') return false;
                // Extract text from HTML if needed
                var tempDiv = $('<div>').html(d);
                var text = tempDiv.find('.provider-text').length > 0 ? 
                          tempDiv.find('.provider-text').text().trim() : 
                          tempDiv.text().trim();
                return text && text !== 'N/A' && text !== 'null';
            });
            
            var uniqueProviders = new Set();
            providers.each(function(d) {
                var tempDiv = $('<div>').html(d);
                var text = tempDiv.find('.provider-text').length > 0 ? 
                          tempDiv.find('.provider-text').text().trim() : 
                          tempDiv.text().trim();
                if (text && text !== 'N/A' && text !== 'null') {
                    uniqueProviders.add(text);
                }
            });
            
            Array.from(uniqueProviders).sort().forEach(function(provider) {
                select.append('<option value="' + provider + '">' + provider + '</option>');
            });
            
            $(selector).select2({
                placeholder: "Select or type a provider",
                allowClear: true,
                width: '100%'
            });
        }
        
'''

# Insert before initDropdownFilter
if 'function initDropdownFilter' in content:
    content = content.replace('        // Dropdown filter\n        function initDropdownFilter', 
                             clean_provider_filter + '        // Dropdown filter\n        function initDropdownFilter')
    print("✅ Inserted clean initProviderFilter function")
else:
    print("❌ Could not find insertion point")

# Write the cleaned template
with open('/usr/local/bin/templates/dsrcircuits.html', 'w') as f:
    f.write(content)

print("✅ Cleaned up JavaScript syntax errors")
print("✅ Provider filters should now work properly")