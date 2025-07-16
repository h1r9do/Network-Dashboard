#!/usr/bin/env python3
"""Update dsrallcircuits template to add the 'More than 2 Circuits' filter button"""

import re

# Read the template file
with open('/usr/local/bin/templates/dsrallcircuits.html', 'r') as f:
    content = f.read()

# 1. Update the CSS grid to accommodate 7 columns instead of 6
content = content.replace(
    'grid-template-columns: repeat(6, 1fr);',
    'grid-template-columns: repeat(7, 1fr);'
)

# 2. Add CSS for the filter button
filter_button_css = """        .filter-control button {
            background: #3498db;
            color: white;
            border: none;
            padding: 6px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            width: 100%;
        }
        .filter-control button:hover {
            background: #2980b9;
        }
        .filter-control button.active {
            background: #27ae60;
        }
"""

# Add the CSS before the .circuit-table class
content = content.replace(
    '        .circuit-table {',
    filter_button_css + '        .circuit-table {'
)

# 3. Add the new filter control after the speed filter
speed_filter_end = '''        </div>
        <div class="filter-control">
            <input type="text" id="speedFilter" placeholder="Filter Speed...">
        </div>
    </div>'''

new_filter_section = '''        </div>
        <div class="filter-control">
            <input type="text" id="speedFilter" placeholder="Filter Speed...">
        </div>
        <div class="filter-control">
            <button id="multiCircuitFilter" onclick="toggleMultiCircuitFilter()" type="button">
                More > 2 Circuits
                {% if filter_stats %}
                    <br><small>{{filter_stats.sites_with_multiple_circuits}} sites ({{filter_stats.total_circuits_at_multi_sites}} circuits)</small>
                {% endif %}
            </button>
        </div>
    </div>'''

content = content.replace(speed_filter_end, new_filter_section)

# 4. Add JavaScript function for the filter
js_function = """
    // Multi-circuit filter functionality
    let multiCircuitFilterActive = false;

    function toggleMultiCircuitFilter() {
        const button = document.getElementById('multiCircuitFilter');
        const table = $('#circuitTable').DataTable();
        
        multiCircuitFilterActive = !multiCircuitFilterActive;
        
        if (multiCircuitFilterActive) {
            button.classList.add('active');
            // Add custom search function to filter for circuit_count > 2
            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                const circuitCount = parseInt($(table.row(dataIndex).node()).data('circuit-count') || '1');
                return circuitCount > 2;
            });
        } else {
            button.classList.remove('active');
            // Remove the custom search function
            $.fn.dataTable.ext.search.pop();
        }
        
        table.draw();
        updateRowCount();
    }

    // Clear multi-circuit filter when other filters are used
    function clearMultiCircuitFilter() {
        if (multiCircuitFilterActive) {
            toggleMultiCircuitFilter();
        }
    }

    // Add event listeners to other filters to clear multi-circuit filter
    $(document).ready(function() {
        $('#siteNameFilter, #siteIdFilter, #circuitPurposeFilter, #providerFilter, #speedFilter').on('input change', function() {
            if (multiCircuitFilterActive) {
                clearMultiCircuitFilter();
            }
        });
    });
"""

# Add the JavaScript function before the closing </body> tag
content = content.replace('</body>', js_function + '\n</body>')

# 5. Update the table row to include data-circuit-count attribute
table_row_pattern = r'(<tr[^>]*>)'
table_row_replacement = r'<tr data-circuit-count="{{ circuit.circuit_count }}">'

# Find the table row in the circuits data loop
content = re.sub(
    r'{% for circuit in circuits_data %}\s*<tr>',
    '{% for circuit in circuits_data %}\n                    <tr data-circuit-count="{{ circuit.circuit_count }}">',
    content
)

# Write the updated content
with open('/usr/local/bin/templates/dsrallcircuits.html', 'w') as f:
    f.write(content)

print("✅ Successfully updated dsrallcircuits.html template")
print("   - Added 'More > 2 Circuits' filter button") 
print("   - Updated CSS grid to 7 columns")
print("   - Added JavaScript functionality for filtering")
print("   - Added circuit count data attributes to table rows")