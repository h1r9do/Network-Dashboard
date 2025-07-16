#!/usr/bin/env python3
"""
Final fix for provider filter initialization
"""

print("=== FINAL FIX FOR PROVIDER FILTERS ===\n")

with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# Replace the entire initFilters function to use server data
old_init_filters = '''        // Initialize filters
        function initFilters() {
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
        }'''

new_init_filters = '''        // Initialize filters
        function initFilters() {
            // Build provider lists from server data (grouped_data)
            var wan1Providers = {};
            var wan2Providers = {};
            var wan1Speeds = {};
            var wan2Speeds = {};
            
            // Extract unique values from ALL data
            {% for network in grouped_data %}
                {% if network.wan1.provider and network.wan1.provider != 'N/A' %}
                    wan1Providers["{{ network.wan1.provider }}"] = true;
                {% endif %}
                {% if network.wan2.provider and network.wan2.provider != 'N/A' %}
                    wan2Providers["{{ network.wan2.provider }}"] = true;
                {% endif %}
                {% if network.wan1.speed %}
                    wan1Speeds["{{ network.wan1.speed }}"] = true;
                {% endif %}
                {% if network.wan2.speed %}
                    wan2Speeds["{{ network.wan2.speed }}"] = true;
                {% endif %}
            {% endfor %}
            
            // Convert to sorted arrays
            var wan1ProviderList = Object.keys(wan1Providers).sort();
            var wan2ProviderList = Object.keys(wan2Providers).sort();
            var wan1SpeedList = Object.keys(wan1Speeds).sort();
            var wan2SpeedList = Object.keys(wan2Speeds).sort();
            
            // Populate WAN1 Provider dropdown
            var $wan1Provider = $('#wan1ProviderFilter');
            $wan1Provider.empty().append('<option value="">All WAN1 Providers</option>');
            wan1ProviderList.forEach(function(provider) {
                $wan1Provider.append('<option value="' + provider + '">' + provider + '</option>');
            });
            
            // Populate WAN2 Provider dropdown
            var $wan2Provider = $('#wan2ProviderFilter');
            $wan2Provider.empty().append('<option value="">All WAN2 Providers</option>');
            wan2ProviderList.forEach(function(provider) {
                $wan2Provider.append('<option value="' + provider + '">' + provider + '</option>');
            });
            
            // Populate speed dropdowns
            var $wan1Speed = $('#wan1SpeedFilter');
            $wan1Speed.empty().append('<option value="">All WAN1 Speeds</option>');
            wan1SpeedList.forEach(function(speed) {
                $wan1Speed.append('<option value="' + speed + '">' + speed + '</option>');
            });
            
            var $wan2Speed = $('#wan2SpeedFilter');
            $wan2Speed.empty().append('<option value="">All WAN2 Speeds</option>');
            wan2SpeedList.forEach(function(speed) {
                $wan2Speed.append('<option value="' + speed + '">' + speed + '</option>');
            });
            
            // Initialize Select2 on provider dropdowns
            $('#wan1ProviderFilter, #wan2ProviderFilter').select2({
                placeholder: "Select or type a provider",
                allowClear: true,
                width: '100%'
            });
            
            // Set up filter handlers for providers
            $('#wan1ProviderFilter').on('change', function() {
                var val = $(this).val();
                if (val) {
                    // Search for exact match in provider text
                    table.column(1).search('^' + $.fn.dataTable.util.escapeRegex(val) + '$', true, false).draw();
                } else {
                    table.column(1).search('').draw();
                }
            });
            
            $('#wan2ProviderFilter').on('change', function() {
                var val = $(this).val();
                if (val) {
                    table.column(4).search('^' + $.fn.dataTable.util.escapeRegex(val) + '$', true, false).draw();
                } else {
                    table.column(4).search('').draw();
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
        }'''

if old_init_filters in content:
    content = content.replace(old_init_filters, new_init_filters)
    print("✅ Replaced initFilters function to use server data")
    
    # Also need to remove or comment out the old provider filter functions
    # since we're not using them anymore
    old_provider_func = '''        // Provider filter - extract clean text without badges
        function initProviderFilter(columnIndex, selector) {'''
    
    if old_provider_func in content:
        # Find the end of the function
        start_idx = content.find(old_provider_func)
        if start_idx != -1:
            # Find the closing brace
            brace_count = 0
            idx = start_idx + len(old_provider_func)
            found_first_brace = False
            while idx < len(content):
                if content[idx] == '{':
                    brace_count += 1
                    found_first_brace = True
                elif content[idx] == '}':
                    brace_count -= 1
                    if found_first_brace and brace_count == 0:
                        # Found the end of the function
                        content = content[:start_idx] + '        // Provider filter function removed - using inline initialization\n' + content[idx+1:]
                        break
                idx += 1
        print("✅ Removed old initProviderFilter function")
else:
    print("❌ Could not find initFilters function")

# Write updated template
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("\nProvider filters will now:")
print("- Show ALL unique providers from the data")
print("- Use exact match searching")
print("- Work with Select2 for searchable dropdowns")
print("- Not be affected by DataTables pagination")