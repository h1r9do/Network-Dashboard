#!/usr/bin/env python3
"""
Fix all filter functionality including speed filters
"""

print("=== FIXING ALL FILTER FUNCTIONALITY ===\n")

with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# Fix speed filters to also use custom search since they might have formatting issues
old_speed_filters = '''            // Speed filter handlers
            $('#wan1SpeedFilter').on('change', function() {
                var val = $(this).val();
                table.column(2).search(val ? '^' + $.fn.dataTable.util.escapeRegex(val) + '$' : '', true, false).draw();
            });
            
            $('#wan2SpeedFilter').on('change', function() {
                var val = $(this).val();
                table.column(5).search(val ? '^' + $.fn.dataTable.util.escapeRegex(val) + '$' : '', true, false).draw();
            });'''

new_speed_filters = '''            // Speed filter handlers
            $('#wan1SpeedFilter').on('change', function() {
                var val = $(this).val();
                if (val) {
                    table.column(2).search('^' + $.fn.dataTable.util.escapeRegex(val) + '$', true, false);
                } else {
                    table.column(2).search('');
                }
                table.draw();
            });
            
            $('#wan2SpeedFilter').on('change', function() {
                var val = $(this).val();
                if (val) {
                    table.column(5).search('^' + $.fn.dataTable.util.escapeRegex(val) + '$', true, false);
                } else {
                    table.column(5).search('');
                }
                table.draw();
            });'''

if old_speed_filters in content:
    content = content.replace(old_speed_filters, new_speed_filters)
    print("✅ Fixed speed filter handlers")

# Also add a debug function to see what's happening
debug_code = '''
        // Debug function to check filter values
        window.debugFilters = function() {
            console.log('Current filter values:');
            console.log('WAN1 Provider:', $('#wan1ProviderFilter').val());
            console.log('WAN2 Provider:', $('#wan2ProviderFilter').val());
            console.log('WAN1 Speed:', $('#wan1SpeedFilter').val());
            console.log('WAN2 Speed:', $('#wan2SpeedFilter').val());
            console.log('Active custom searches:', $.fn.dataTable.ext.search.length);
            
            // Check what provider values are in the table
            var providers1 = new Set();
            var providers2 = new Set();
            table.rows().every(function() {
                var row = this.node();
                var cell1 = $(row).find('td').eq(1);
                var cell2 = $(row).find('td').eq(4);
                var p1 = cell1.attr('data-provider') || cell1.find('.provider-text').text().trim();
                var p2 = cell2.attr('data-provider') || cell2.find('.provider-text').text().trim();
                if (p1) providers1.add(p1);
                if (p2) providers2.add(p2);
            });
            console.log('Unique WAN1 providers in table:', Array.from(providers1).sort());
            console.log('Unique WAN2 providers in table:', Array.from(providers2).sort());
        };
'''

# Add debug code before the closing script tag
content = content.replace('    </script>', debug_code + '    </script>')

# Write the updated content
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("\nAdded debug function - in browser console, run:")
print("  debugFilters()")
print("to see current filter states and available providers")