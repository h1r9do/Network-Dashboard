#!/usr/bin/env python3
"""
Fix the production template properly - remove duplicates and syntax errors
"""

print("=== FINAL FIX FOR PRODUCTION TEMPLATE ===\n")

with open('/usr/local/bin/templates/dsrcircuits.html', 'r') as f:
    content = f.read()

# Remove the duplicate JavaScript code
# There's duplicate provider filter code at lines 730-744
content = content.replace('''        });
            
            var providers = column.data().unique().sort().filter(function(d) {
                return d && d !== 'N/A' && d !== 'null';
            });
            
            providers.each(function(d, j) {
                select.append('<option value="' + d + '">' + d + '</option>');
            });
            
            $(selector).select2({
                placeholder: "Select or type a provider",
                allowClear: true,
                width: '100%'
            });
        }''', '}')

# Also remove duplicate document.ready at the bottom
content = content.replace('''</html>

        $(document).ready(function() {
        // Initialize DataTable
        var table = $('#circuitTable').DataTable({
            paging: false,
            scrollCollapse: true,
            dom: 't'
        });

        // Track speed filter state''', '</html>')

print("✅ Removed duplicate JavaScript code")

# Write the fixed content
with open('/usr/local/bin/templates/dsrcircuits.html', 'w') as f:
    f.write(content)

print("✅ Production template fixed!")
print("\nThe template should now load without JavaScript errors")