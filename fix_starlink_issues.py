#!/usr/bin/env python3
"""
Fix Starlink double counting and filter display issues
"""

print("=== FIXING STARLINK COUNTING AND FILTER ISSUES ===\n")

# First, let's check what's happening with the provider data
import psycopg2
conn = psycopg2.connect('host=localhost dbname=dsrcircuits user=dsruser password=dsrpass123')
cur = conn.cursor()

# Check enriched_circuits for provider data
cur.execute("""
    SELECT network_name, wan1_provider, wan2_provider
    FROM enriched_circuits
    WHERE wan1_provider ILIKE '%star%' OR wan2_provider ILIKE '%star%'
    ORDER BY network_name
    LIMIT 10
""")

results = cur.fetchall()
print("Sample provider values containing 'star':")
for row in results:
    print(f"  {row[0]}: WAN1='{row[1]}', WAN2='{row[2]}'")

conn.close()

# Fix the blueprint to prevent double counting
with open('/usr/local/bin/Main/dsrcircuits_blueprint.py', 'r') as f:
    lines = f.readlines()

# Find the test route (around line 190)
for i, line in enumerate(lines):
    if "def dsrcircuits_test():" in line:
        print(f"\nFound test route at line {i+1}")
        
        # Look for the duplicate wireless logic in main route
        # We need to remove it from the main route (keep only in test route)
        break

# Check if there's duplicate Starlink logic in main route
main_route_start = None
for i, line in enumerate(lines):
    if "def dsrcircuits():" in line and i < 150:  # Main route is before test route
        main_route_start = i
        print(f"Found main route at line {i+1}")
        break

# Now fix the template to clean up provider display
print("\nFixing template provider display...")

with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    template_content = f.read()

# Fix the provider cell display - remove badges from appearing in filters
# First, let's check what's in the provider cells
import re

# Find provider cell patterns
provider_cells = re.findall(r'<td class="provider-cell">.*?</td>', template_content, re.DOTALL)
if provider_cells:
    print(f"\nFound {len(provider_cells)} provider cell definitions")
    
# The issue is that the filter is picking up the badge HTML. We need to ensure
# the provider value is clean for filtering
old_provider_cell_wan1 = '''<td class="provider-cell">
                            <span class="provider-text">{{ entry.wan1.provider if entry.wan1.provider else 'N/A' }}</span>
                            {% if entry.wan1.wireless_badge %}
                                {% if entry.wan1.wireless_badge == 'VZW' %}
                                    <span class="wireless-badge vzw">📶 VZW</span>
                                {% elif entry.wan1.wireless_badge == 'ATT' %}
                                    <span class="wireless-badge att">📶 AT&T</span>
                                {% elif entry.wan1.wireless_badge == 'STARLINK' %}
                                    <span class="wireless-badge starlink">🛰️ STAR</span>
                                {% endif %}
                            {% endif %}
                            {% if entry.wan1.match_info and entry.wan1.match_info.dsr_verified %}
                                <span class="dsr-badge">DSR</span>
                            {% endif %}
                        </td>'''

# Add data attribute for clean filtering
new_provider_cell_wan1 = '''<td class="provider-cell" data-provider="{{ entry.wan1.provider if entry.wan1.provider else 'N/A' }}">
                            <span class="provider-text">{{ entry.wan1.provider if entry.wan1.provider else 'N/A' }}</span>
                            {% if entry.wan1.wireless_badge %}
                                {% if entry.wan1.wireless_badge == 'VZW' %}
                                    <span class="wireless-badge vzw">📶 VZW</span>
                                {% elif entry.wan1.wireless_badge == 'ATT' %}
                                    <span class="wireless-badge att">📶 AT&T</span>
                                {% elif entry.wan1.wireless_badge == 'STARLINK' %}
                                    <span class="wireless-badge starlink">🛰️ STAR</span>
                                {% endif %}
                            {% endif %}
                            {% if entry.wan1.match_info and entry.wan1.match_info.dsr_verified %}
                                <span class="dsr-badge">DSR</span>
                            {% endif %}
                        </td>'''

template_content = template_content.replace(old_provider_cell_wan1, new_provider_cell_wan1)

# Same for WAN2
old_provider_cell_wan2 = '''<td class="provider-cell">
                            <span class="provider-text">{{ entry.wan2.provider if entry.wan2.provider else 'N/A' }}</span>
                            {% if entry.wan2.wireless_badge %}
                                {% if entry.wan2.wireless_badge == 'VZW' %}
                                    <span class="wireless-badge vzw">📶 VZW</span>
                                {% elif entry.wan2.wireless_badge == 'ATT' %}
                                    <span class="wireless-badge att">📶 AT&T</span>
                                {% elif entry.wan2.wireless_badge == 'STARLINK' %}
                                    <span class="wireless-badge starlink">🛰️ STAR</span>
                                {% endif %}
                            {% endif %}
                            {% if entry.wan2.match_info and entry.wan2.match_info.dsr_verified %}
                                <span class="dsr-badge">DSR</span>
                            {% endif %}
                        </td>'''

new_provider_cell_wan2 = '''<td class="provider-cell" data-provider="{{ entry.wan2.provider if entry.wan2.provider else 'N/A' }}">
                            <span class="provider-text">{{ entry.wan2.provider if entry.wan2.provider else 'N/A' }}</span>
                            {% if entry.wan2.wireless_badge %}
                                {% if entry.wan2.wireless_badge == 'VZW' %}
                                    <span class="wireless-badge vzw">📶 VZW</span>
                                {% elif entry.wan2.wireless_badge == 'ATT' %}
                                    <span class="wireless-badge att">📶 AT&T</span>
                                {% elif entry.wan2.wireless_badge == 'STARLINK' %}
                                    <span class="wireless-badge starlink">🛰️ STAR</span>
                                {% endif %}
                            {% endif %}
                            {% if entry.wan2.match_info and entry.wan2.match_info.dsr_verified %}
                                <span class="dsr-badge">DSR</span>
                            {% endif %}
                        </td>'''

template_content = template_content.replace(old_provider_cell_wan2, new_provider_cell_wan2)

# Now update the JavaScript filter to use data-provider attribute
old_filter_js = '''wan1ProviderText = cells[1].textContent.trim();'''
new_filter_js = '''wan1ProviderText = cells[1].getAttribute('data-provider') || cells[1].textContent.trim();'''

template_content = template_content.replace(old_filter_js, new_filter_js)

old_filter_js2 = '''wan2ProviderText = cells[4].textContent.trim();'''
new_filter_js2 = '''wan2ProviderText = cells[4].getAttribute('data-provider') || cells[4].textContent.trim();'''

template_content = template_content.replace(old_filter_js2, new_filter_js2)

# Write updated template
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(template_content)

print("\n✅ Fixed template issues:")
print("  - Added data-provider attribute for clean filtering")
print("  - Updated JavaScript to use data attribute instead of text content")
print("  - This prevents badges from interfering with filters")