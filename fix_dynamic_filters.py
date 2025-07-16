#!/usr/bin/env python3
"""
Fix the filters to populate dynamically from DataTable columns
"""

print("=== FIXING DYNAMIC FILTERS ===\n")

# Read the template
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# Replace the initFilters function with proper dynamic population
old_init_filters = '''        function initFilters() {
            // WAN1 Provider
            $('#wan1ProviderFilter').on('change', function() {
                table.column(1).search(this.value).draw();
            });
            
            // WAN2 Provider  
            $('#wan2ProviderFilter').on('change', function() {
                table.column(4).search(this.value).draw();
            });
            
            // Speed text filters
            $('#wan1SpeedFilter').on('keyup', function() {
                table.column(2).search(this.value).draw();
            });
            
            $('#wan2SpeedFilter').on('keyup', function() {
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
        }'''

new_init_filters = '''        function initFilters() {
            // Initialize provider dropdowns with unique values from columns
            initProviderFilter(1, '#wan1ProviderFilter');
            initProviderFilter(4, '#wan2ProviderFilter');
            initSpeedFilter(2, '#wan1SpeedFilter');
            initSpeedFilter(5, '#wan2SpeedFilter');
            
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
        }
        
        // Provider filter with dynamic population
        function initProviderFilter(columnIndex, selector) {
            var column = table.column(columnIndex);
            var select = $(selector)
                .empty()
                .append('<option value="">All WAN ' + (columnIndex === 1 ? '1' : '2') + ' Providers</option>')
                .on('change', function() {
                    var val = $(this).val();
                    column.search(val ? '^' + val.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + '$' : '', true, false).draw();
                });
            
            // Get unique providers from the column data
            var providers = [];
            column.data().unique().sort().each(function(d) {
                if (d && d !== 'N/A' && d !== 'null' && d.trim() !== '') {
                    // Remove any HTML tags and wireless badges
                    var cleanProvider = d.replace(/<[^>]*>/g, '').trim();
                    if (cleanProvider && providers.indexOf(cleanProvider) === -1) {
                        providers.push(cleanProvider);
                    }
                }
            });
            
            // Sort and add to dropdown
            providers.sort().forEach(function(provider) {
                select.append('<option value="' + provider + '">' + provider + '</option>');
            });
            
            console.log(selector + ' populated with ' + providers.length + ' providers');
        }
        
        // Speed filter with dynamic population  
        function initSpeedFilter(columnIndex, selector) {
            var column = table.column(columnIndex);
            var select = $(selector)
                .empty()
                .append('<option value="">All WAN ' + (columnIndex === 2 ? '1' : '2') + ' Speeds</option>')
                .on('change', function() {
                    var val = $(this).val();
                    column.search(val ? '^' + val.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + '$' : '', true, false).draw();
                });
            
            // Get unique speeds from the column data
            var speeds = [];
            column.data().unique().sort().each(function(d) {
                if (d && d !== 'N/A' && d !== 'null' && d.trim() !== '') {
                    if (speeds.indexOf(d) === -1) {
                        speeds.push(d);
                    }
                }
            });
            
            // Sort and add to dropdown
            speeds.sort().forEach(function(speed) {
                select.append('<option value="' + speed + '">' + speed + '</option>');
            });
            
            console.log(selector + ' populated with ' + speeds.length + ' speeds');
        }'''

# Replace the function
content = content.replace(old_init_filters, new_init_filters)

# Also need to fix the row count update function
old_row_count = '''        // Update row count
        function updateRowCount() {
            var filteredCount = table.rows({ search: 'applied' }).count();
            var totalCount = table.rows().count();
            $('#rowCount').text(`Showing ${filteredCount} of ${totalCount} rows`);
        }'''

if old_row_count not in content:
    # Add the updateRowCount function
    update_row_count_func = '''
        // Update row count
        function updateRowCount() {
            var filteredCount = table.rows({ search: 'applied' }).count();
            var totalCount = table.rows().count();
            $('#rowCount').text(`Showing ${filteredCount} of ${totalCount} rows`);
        }
        '''
    
    # Insert before initFilters
    content = content.replace('        function initFilters()', update_row_count_func + '        function initFilters()')

# Make sure updateRowCount is called on table draw
if 'table.on(\'draw.dt\', function() {' not in content:
    # Add the draw event handler
    draw_handler = '''
        // Update row count on draw
        table.on('draw.dt', function() {
            updateRowCount();
        });
        '''
    
    # Insert before the closing script tag
    content = content.replace('    });', '        ' + draw_handler.strip() + '\n    });')

# Initialize everything at the end
if 'initFilters();' not in content:
    content = content.replace('    });', '        \n        // Initialize filters and row count\n        initFilters();\n        updateRowCount();\n    });')

# Write the fixed template
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("✅ Fixed dynamic filter population")
print("✅ Filters now populate from actual DataTable column data")
print("✅ Row count will update dynamically")