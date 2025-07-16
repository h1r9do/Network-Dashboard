#!/usr/bin/env python3
"""
Fix filter initialization and add simple debugging
"""

print("=== FIXING FILTERS AND DEBUGGING ===\n")

with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# Replace the problematic initFilters function with a simpler version
old_init_filters = '''        // Initialize filters
        function initFilters() {
            // Build provider lists from server data
            var providers1 = [], providers2 = [], speeds1 = [], speeds2 = [];
            
            // Extract unique values from grouped_data passed from server
            var seenProviders1 = {}, seenProviders2 = {}, seenSpeeds1 = {}, seenSpeeds2 = {};
            
            {% for network in grouped_data %}
                {% if network.wan1.provider and network.wan1.provider != 'N/A' %}
                    if (!seenProviders1[{{ network.wan1.provider|tojson }}]) {
                        providers1.push({{ network.wan1.provider|tojson }});
                        seenProviders1[{{ network.wan1.provider|tojson }}] = true;
                    }
                {% endif %}
                {% if network.wan2.provider and network.wan2.provider != 'N/A' %}
                    if (!seenProviders2[{{ network.wan2.provider|tojson }}]) {
                        providers2.push({{ network.wan2.provider|tojson }});
                        seenProviders2[{{ network.wan2.provider|tojson }}] = true;
                    }
                {% endif %}
                {% if network.wan1.speed %}
                    if (!seenSpeeds1[{{ network.wan1.speed|tojson }}]) {
                        speeds1.push({{ network.wan1.speed|tojson }});
                        seenSpeeds1[{{ network.wan1.speed|tojson }}] = true;
                    }
                {% endif %}
                {% if network.wan2.speed %}
                    if (!seenSpeeds2[{{ network.wan2.speed|tojson }}]) {
                        speeds2.push({{ network.wan2.speed|tojson }});
                        seenSpeeds2[{{ network.wan2.speed|tojson }}] = true;
                    }
                {% endif %}
            {% endfor %}
            
            // Sort the arrays
            providers1.sort();
            providers2.sort();
            speeds1.sort();
            speeds2.sort();
            
            // Populate provider dropdowns
            var $wan1Provider = $('#wan1ProviderFilter').empty()
                .append('<option value="">All WAN1 Providers</option>');
            providers1.forEach(function(p) {
                $wan1Provider.append('<option value="' + p + '">' + p + '</option>');
            });
            
            var $wan2Provider = $('#wan2ProviderFilter').empty()
                .append('<option value="">All WAN2 Providers</option>');
            providers2.forEach(function(p) {
                $wan2Provider.append('<option value="' + p + '">' + p + '</option>');
            });
            
            // Populate speed dropdowns
            var $wan1Speed = $('#wan1SpeedFilter').empty()
                .append('<option value="">All WAN1 Speeds</option>');
            speeds1.forEach(function(s) {
                $wan1Speed.append('<option value="' + s + '">' + s + '</option>');
            });
            
            var $wan2Speed = $('#wan2SpeedFilter').empty()
                .append('<option value="">All WAN2 Speeds</option>');
            speeds2.forEach(function(s) {
                $wan2Speed.append('<option value="' + s + '">' + s + '</option>');
            });
            
            // Initialize Select2
            $('#wan1ProviderFilter, #wan2ProviderFilter').select2({
                placeholder: "Select or type a provider",
                allowClear: true,
                width: '100%'
            });
            
            // Provider filter handlers - custom search for provider text
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
            });
            
            $('#wan2ProviderFilter').on('change', function() {
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
            });
            
            // Speed filter handlers
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
            });
            
            // Other filters
            $('#siteFilter').on('keyup', function() {
                table.column(0).search(this.value).draw();
            });
            
            $('#wan1CostFilter').on('keyup', function() {
                table.column(3).search(this.value).draw();
            });
            
            $('#wan2CostFilter').on('keyup', function() {
                table.column(6).search(this.value).draw();
            });
        }'''

# Replace with a simpler version that collects data from the table after it loads
new_init_filters = '''        // Initialize filters
        function initFilters() {
            // Wait for table to be ready, then populate filters from actual table data
            setTimeout(function() {
                populateFiltersFromTable();
                setupFilterHandlers();
            }, 100);
        }
        
        function populateFiltersFromTable() {
            // Get unique values from the DataTable
            var providers1 = new Set();
            var providers2 = new Set();
            var speeds1 = new Set();
            var speeds2 = new Set();
            
            // Iterate through all rows
            table.rows().every(function() {
                var data = this.data();
                var row = this.node();
                
                // Get providers from cells
                var $row = $(row);
                var wan1Provider = $row.find('td').eq(1).attr('data-provider') || 
                                  $row.find('td').eq(1).find('.provider-text').text().trim();
                var wan2Provider = $row.find('td').eq(4).attr('data-provider') || 
                                  $row.find('td').eq(4).find('.provider-text').text().trim();
                
                // Get speeds from data
                var wan1Speed = data[2]; // Column 2 is WAN1 Speed
                var wan2Speed = data[5]; // Column 5 is WAN2 Speed
                
                if (wan1Provider && wan1Provider !== 'N/A' && wan1Provider.trim() !== '') {
                    providers1.add(wan1Provider);
                }
                if (wan2Provider && wan2Provider !== 'N/A' && wan2Provider.trim() !== '') {
                    providers2.add(wan2Provider);
                }
                if (wan1Speed && wan1Speed.trim() !== '') {
                    speeds1.add(wan1Speed);
                }
                if (wan2Speed && wan2Speed.trim() !== '') {
                    speeds2.add(wan2Speed);
                }
            });
            
            // Convert to sorted arrays
            var providers1Array = Array.from(providers1).sort();
            var providers2Array = Array.from(providers2).sort();
            var speeds1Array = Array.from(speeds1).sort();
            var speeds2Array = Array.from(speeds2).sort();
            
            // Populate dropdowns
            var $wan1Provider = $('#wan1ProviderFilter').empty()
                .append('<option value="">All WAN1 Providers</option>');
            providers1Array.forEach(function(p) {
                $wan1Provider.append($('<option></option>').attr('value', p).text(p));
            });
            
            var $wan2Provider = $('#wan2ProviderFilter').empty()
                .append('<option value="">All WAN2 Providers</option>');
            providers2Array.forEach(function(p) {
                $wan2Provider.append($('<option></option>').attr('value', p).text(p));
            });
            
            var $wan1Speed = $('#wan1SpeedFilter').empty()
                .append('<option value="">All WAN1 Speeds</option>');
            speeds1Array.forEach(function(s) {
                $wan1Speed.append($('<option></option>').attr('value', s).text(s));
            });
            
            var $wan2Speed = $('#wan2SpeedFilter').empty()
                .append('<option value="">All WAN2 Speeds</option>');
            speeds2Array.forEach(function(s) {
                $wan2Speed.append($('<option></option>').attr('value', s).text(s));
            });
            
            // Initialize Select2
            $('#wan1ProviderFilter, #wan2ProviderFilter').select2({
                placeholder: "Select or type a provider",
                allowClear: true,
                width: '100%'
            });
            
            console.log('Filters populated - WAN1 Providers:', providers1Array.length, 
                        'WAN2 Providers:', providers2Array.length);
        }
        
        function setupFilterHandlers() {
            // Provider filters - use custom search
            $('#wan1ProviderFilter').on('change', function() {
                var val = $(this).val();
                if (val) {
                    // Custom search function
                    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                        var row = table.row(dataIndex).node();
                        var cell = $(row).find('td').eq(1);
                        var provider = cell.attr('data-provider') || cell.find('.provider-text').text().trim();
                        return provider === val;
                    });
                    table.draw();
                    $.fn.dataTable.ext.search.pop();
                } else {
                    table.draw();
                }
            });
            
            $('#wan2ProviderFilter').on('change', function() {
                var val = $(this).val();
                if (val) {
                    $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                        var row = table.row(dataIndex).node();
                        var cell = $(row).find('td').eq(4);
                        var provider = cell.attr('data-provider') || cell.find('.provider-text').text().trim();
                        return provider === val;
                    });
                    table.draw();
                    $.fn.dataTable.ext.search.pop();
                } else {
                    table.draw();
                }
            });
            
            // Speed filters
            $('#wan1SpeedFilter').on('change', function() {
                var val = $(this).val();
                table.column(2).search(val ? '^' + $.fn.dataTable.util.escapeRegex(val) + '$' : '', true, false).draw();
            });
            
            $('#wan2SpeedFilter').on('change', function() {
                var val = $(this).val();
                table.column(5).search(val ? '^' + $.fn.dataTable.util.escapeRegex(val) + '$' : '', true, false).draw();
            });
            
            // Text filters
            $('#siteFilter').on('keyup', function() {
                table.column(0).search(this.value).draw();
            });
            
            $('#wan1CostFilter').on('keyup', function() {
                table.column(3).search(this.value).draw();
            });
            
            $('#wan2CostFilter').on('keyup', function() {
                table.column(6).search(this.value).draw();
            });
        }'''

if old_init_filters in content:
    content = content.replace(old_init_filters, new_init_filters)
    print("✅ Replaced initFilters with simpler version")
else:
    print("❌ Could not find initFilters function")

# Also add simple debugging
simple_debug = '''
        // Simple debugging
        window.checkFilters = function() {
            console.log('=== FILTER CHECK ===');
            console.log('WAN1 Provider options:', $('#wan1ProviderFilter option').length - 1);
            console.log('WAN2 Provider options:', $('#wan2ProviderFilter option').length - 1);
            console.log('Table rows:', table.rows().count());
            console.log('First 5 WAN1 providers:');
            $('#wan1ProviderFilter option').slice(1, 6).each(function() {
                console.log('  - "' + $(this).val() + '"');
            });
        };
'''

# Add before closing script tag
content = content.replace('    </script>', simple_debug + '    </script>')

# Write the updated content
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("\n✅ Fixed filter initialization")
print("✅ Filters now populate from table data after loading")
print("✅ No more Jinja2 syntax issues")
print("\nIn browser console, run: checkFilters()")