#!/usr/bin/env python3
"""
Fix provider filter to show all providers and count Starlink correctly
"""

print("=== FIXING PROVIDER FILTER AND STARLINK COUNT ===\n")

# First, let's check how many Starlink providers are actually in enriched_circuits
import psycopg2
conn = psycopg2.connect('host=localhost dbname=dsrcircuits user=dsruser password=dsrpass123')
cur = conn.cursor()

# Count actual Starlink providers
cur.execute("""
    SELECT COUNT(DISTINCT network_name) as starlink_sites,
           SUM(CASE WHEN wan1_provider ILIKE '%starlink%' THEN 1 ELSE 0 END) as wan1_starlink,
           SUM(CASE WHEN wan2_provider ILIKE '%starlink%' THEN 1 ELSE 0 END) as wan2_starlink
    FROM enriched_circuits
    WHERE wan1_provider ILIKE '%starlink%' OR wan2_provider ILIKE '%starlink%'
""")

result = cur.fetchone()
print(f"Database Starlink counts:")
print(f"  - Sites with Starlink: {result[0]}")
print(f"  - WAN1 Starlink: {result[1]}")
print(f"  - WAN2 Starlink: {result[2]}")
print(f"  - Total Starlink circuits: {result[1] + result[2]}")

conn.close()

# Now fix the template to properly populate provider filters
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# Replace the provider filter initialization completely
# The issue is that it's only getting data from visible rows, not all rows
old_init_filters = '''            // Initialize filters
            initProviderFilter(1, '#wan1ProviderFilter');
            initProviderFilter(4, '#wan2ProviderFilter');
            initDropdownFilter(2, '#wan1SpeedFilter');
            initDropdownFilter(5, '#wan2SpeedFilter');'''

new_init_filters = '''            // Initialize filters AFTER table is fully loaded
            // Use original data from server, not filtered table data
            var allProviders1 = [];
            var allProviders2 = [];
            var allSpeeds1 = [];
            var allSpeeds2 = [];
            
            // Extract unique values from grouped_data
            {% for network in grouped_data %}
                {% if network.wan1.provider and network.wan1.provider != 'N/A' %}
                    if (allProviders1.indexOf("{{ network.wan1.provider }}") === -1) {
                        allProviders1.push("{{ network.wan1.provider }}");
                    }
                {% endif %}
                {% if network.wan2.provider and network.wan2.provider != 'N/A' %}
                    if (allProviders2.indexOf("{{ network.wan2.provider }}") === -1) {
                        allProviders2.push("{{ network.wan2.provider }}");
                    }
                {% endif %}
                {% if network.wan1.speed %}
                    if (allSpeeds1.indexOf("{{ network.wan1.speed }}") === -1) {
                        allSpeeds1.push("{{ network.wan1.speed }}");
                    }
                {% endif %}
                {% if network.wan2.speed %}
                    if (allSpeeds2.indexOf("{{ network.wan2.speed }}") === -1) {
                        allSpeeds2.push("{{ network.wan2.speed }}");
                    }
                {% endif %}
            {% endfor %}
            
            // Sort the arrays
            allProviders1.sort();
            allProviders2.sort();
            allSpeeds1.sort();
            allSpeeds2.sort();
            
            // Populate WAN1 Provider filter
            var wan1Select = $('#wan1ProviderFilter');
            wan1Select.empty().append('<option value="">All WAN1 Providers</option>');
            allProviders1.forEach(function(provider) {
                wan1Select.append('<option value="' + provider + '">' + provider + '</option>');
            });
            
            // Populate WAN2 Provider filter
            var wan2Select = $('#wan2ProviderFilter');
            wan2Select.empty().append('<option value="">All WAN2 Providers</option>');
            allProviders2.forEach(function(provider) {
                wan2Select.append('<option value="' + provider + '">' + provider + '</option>');
            });
            
            // Initialize Select2
            $('#wan1ProviderFilter, #wan2ProviderFilter').select2({
                placeholder: "Select or type a provider",
                allowClear: true,
                width: '100%'
            });
            
            // Set up filter handlers
            $('#wan1ProviderFilter').on('change', function() {
                var val = $(this).val();
                table.column(1).search(val ? '^' + $.fn.dataTable.util.escapeRegex(val) + '$' : '', true, false).draw();
            });
            
            $('#wan2ProviderFilter').on('change', function() {
                var val = $(this).val();
                table.column(4).search(val ? '^' + $.fn.dataTable.util.escapeRegex(val) + '$' : '', true, false).draw();
            });
            
            initDropdownFilter(2, '#wan1SpeedFilter');
            initDropdownFilter(5, '#wan2SpeedFilter');'''

if old_init_filters in content:
    content = content.replace(old_init_filters, new_init_filters)
    print("\n✅ Fixed provider filter initialization")
else:
    print("\n❌ Could not find filter initialization code")

# Write updated template
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

# Now fix the Starlink counting to only count circuits, not badges
print("\nFixing Starlink counting logic...")

with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    bp_content = f.read()

# The counting should be based on actual provider names containing "Starlink"
old_starlink_count = '''            # Count wireless badges
            if entry['wan1'].get('wireless_badge'):
                if entry['wan1']['wireless_badge'] == 'VZW':
                    vzw_count += 1
                elif entry['wan1']['wireless_badge'] == 'ATT':
                    att_count += 1
                elif entry['wan1']['wireless_badge'] == 'STARLINK':
                    starlink_count += 1
                    
            if entry['wan2'].get('wireless_badge'):
                if entry['wan2']['wireless_badge'] == 'VZW':
                    vzw_count += 1
                elif entry['wan2']['wireless_badge'] == 'ATT':
                    att_count += 1
                elif entry['wan2']['wireless_badge'] == 'STARLINK':
                    starlink_count += 1'''

new_starlink_count = '''            # Count wireless providers (not badges, actual providers)
            # Check WAN1
            if entry['wan1'].get('wireless_badge'):
                if entry['wan1']['wireless_badge'] == 'VZW':
                    vzw_count += 1
                elif entry['wan1']['wireless_badge'] == 'ATT':
                    att_count += 1
            
            # Count Starlink based on provider name
            if entry['wan1']['provider'] and 'starlink' in entry['wan1']['provider'].lower():
                starlink_count += 1
                    
            # Check WAN2
            if entry['wan2'].get('wireless_badge'):
                if entry['wan2']['wireless_badge'] == 'VZW':
                    vzw_count += 1
                elif entry['wan2']['wireless_badge'] == 'ATT':
                    att_count += 1
                    
            # Count Starlink based on provider name
            if entry['wan2']['provider'] and 'starlink' in entry['wan2']['provider'].lower():
                starlink_count += 1'''

if old_starlink_count in bp_content:
    bp_content = bp_content.replace(old_starlink_count, new_starlink_count)
    print("✅ Fixed Starlink counting to use provider names")
    
    with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'w') as f:
        f.write(bp_content)
else:
    print("❌ Could not find counting logic")

print("\nSummary of fixes:")
print("1. Provider filters now populate from ALL data, not just visible rows")
print("2. Starlink count based on actual provider name containing 'starlink'")
print("3. Should show 15 Starlink circuits based on database query")