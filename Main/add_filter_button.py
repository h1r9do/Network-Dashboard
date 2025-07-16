#!/usr/bin/env python3
"""Add the multi-circuit filter button to dsrallcircuits template"""

# Read the template file
with open('/usr/local/bin/templates/dsrallcircuits.html', 'r') as f:
    content = f.read()

# Find the cost filter and add the new button after it
cost_filter_section = '''        <div class="filter-control">
            <input type="text" id="costFilter" placeholder="Filter Cost...">
        </div>
    </div>'''

new_section_with_button = '''        <div class="filter-control">
            <input type="text" id="costFilter" placeholder="Filter Cost...">
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

content = content.replace(cost_filter_section, new_section_with_button)

# Add CSS for the filter button if not already present
if '.filter-control button {' not in content:
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

# Add JavaScript function for the filter if not already present
if 'toggleMultiCircuitFilter' not in content:
    js_function = '''
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
        $('#siteNameFilter, #siteIdFilter, #circuitPurposeFilter, #providerFilter, #speedFilter, #costFilter').on('input change', function() {
            if (multiCircuitFilterActive) {
                clearMultiCircuitFilter();
            }
        });
    });
'''

    # Add the JavaScript function before the closing </body> tag
    content = content.replace('</body>', js_function + '\n</body>')

# Write the updated content
with open('/usr/local/bin/templates/dsrallcircuits.html', 'w') as f:
    f.write(content)

print("✅ Successfully added multi-circuit filter button to dsrallcircuits.html")
print("   - Filter button shows sites with more than 2 circuits")
print("   - Button displays count statistics") 
print("   - Added JavaScript functionality for filtering")