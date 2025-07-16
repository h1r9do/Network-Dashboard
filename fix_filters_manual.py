#!/usr/bin/env python3
"""
Manually fix the filter initialization
"""

print("=== MANUAL FILTER FIX ===\n")

with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    lines = f.readlines()

# Find the initFilters function and replace it
in_init_filters = False
new_lines = []
skip_until_closing_brace = False
brace_count = 0

for i, line in enumerate(lines):
    if 'function initFilters()' in line:
        print(f"Found initFilters at line {i+1}")
        in_init_filters = True
        skip_until_closing_brace = True
        brace_count = 0
        
        # Add the new initFilters function
        new_lines.append('''        // Initialize filters
        function initFilters() {
            // Build provider lists from server data
            var providers1 = [], providers2 = [], speeds1 = [], speeds2 = [];
            
            // Extract unique values from grouped_data passed from server
            var seenProviders1 = {}, seenProviders2 = {}, seenSpeeds1 = {}, seenSpeeds2 = {};
            
            {% for network in grouped_data %}
                {% if network.wan1.provider and network.wan1.provider != 'N/A' %}
                    if (!seenProviders1["{{ network.wan1.provider }}"]) {
                        providers1.push("{{ network.wan1.provider }}");
                        seenProviders1["{{ network.wan1.provider }}"] = true;
                    }
                {% endif %}
                {% if network.wan2.provider and network.wan2.provider != 'N/A' %}
                    if (!seenProviders2["{{ network.wan2.provider }}"]) {
                        providers2.push("{{ network.wan2.provider }}");
                        seenProviders2["{{ network.wan2.provider }}"] = true;
                    }
                {% endif %}
                {% if network.wan1.speed %}
                    if (!seenSpeeds1["{{ network.wan1.speed }}"]) {
                        speeds1.push("{{ network.wan1.speed }}");
                        seenSpeeds1["{{ network.wan1.speed }}"] = true;
                    }
                {% endif %}
                {% if network.wan2.speed %}
                    if (!seenSpeeds2["{{ network.wan2.speed }}"]) {
                        speeds2.push("{{ network.wan2.speed }}");
                        seenSpeeds2["{{ network.wan2.speed }}"] = true;
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
            
            // Provider filter handlers
            $('#wan1ProviderFilter').on('change', function() {
                var val = $(this).val();
                table.column(1).search(val ? '^' + $.fn.dataTable.util.escapeRegex(val) + '$' : '', true, false).draw();
            });
            
            $('#wan2ProviderFilter').on('change', function() {
                var val = $(this).val();
                table.column(4).search(val ? '^' + $.fn.dataTable.util.escapeRegex(val) + '$' : '', true, false).draw();
            });
            
            // Speed filter handlers
            $('#wan1SpeedFilter').on('change', function() {
                var val = $(this).val();
                table.column(2).search(val ? '^' + $.fn.dataTable.util.escapeRegex(val) + '$' : '', true, false).draw();
            });
            
            $('#wan2SpeedFilter').on('change', function() {
                var val = $(this).val();
                table.column(5).search(val ? '^' + $.fn.dataTable.util.escapeRegex(val) + '$' : '', true, false).draw();
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
        }
''')
        continue
        
    if skip_until_closing_brace:
        if '{' in line:
            brace_count += line.count('{')
        if '}' in line:
            brace_count -= line.count('}')
            if brace_count <= 0 and '}' in line:
                skip_until_closing_brace = False
                in_init_filters = False
                continue
        continue
    
    new_lines.append(line)

# Write the updated file
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.writelines(new_lines)

print("✅ Replaced initFilters function")
print("✅ Filters now populate from ALL server data")
print("✅ Starlink should appear in dropdown if present in data")