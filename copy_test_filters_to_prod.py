#!/usr/bin/env python3
"""
Copy working filters from test template to production
"""

print("=== COPYING TEST FILTERS TO PRODUCTION ===\n")

# Read both templates
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    test_content = f.read()

with open('/usr/local/bin/Main/templates/dsrcircuits.html', 'r') as f:
    prod_content = f.read()

import re

# Extract the filter initialization section from test template
# Find from initFilters to the end of filter functions
test_filters_match = re.search(r'function initFilters\(\).*?(?=// Initialize DataTable|\$\(document\)\.ready|$)', test_content, re.DOTALL)

if test_filters_match:
    test_filters = test_filters_match.group(0)
    print("✅ Found test filter functions")
    
    # Remove any existing initFilters and related functions from production
    prod_content = re.sub(r'function initFilters\(\).*?(?=// Initialize DataTable|\$\(document\)\.ready|function \w+|$)', '', prod_content, flags=re.DOTALL)
    
    # Insert the test filters before document.ready or at end of script section
    if '$(document).ready(function()' in prod_content:
        insert_point = prod_content.find('$(document).ready(function()')
        prod_content = prod_content[:insert_point] + test_filters + '\n\n        ' + prod_content[insert_point:]
    else:
        # Insert before closing script tag
        prod_content = prod_content.replace('    </script>', test_filters + '\n    </script>')
    
    print("✅ Inserted test filters into production")
else:
    print("❌ Could not find test filters")

# Also need to ensure the filter dropdowns in HTML match
# Extract filter controls from test
test_filter_controls = re.search(r'<div class="filter-controls">.*?</div>\s*</div>', test_content, re.DOTALL)
prod_filter_controls = re.search(r'<div class="filter-controls">.*?</div>\s*</div>', prod_content, re.DOTALL)

if test_filter_controls and prod_filter_controls:
    # Replace production filter controls with test ones
    prod_content = prod_content.replace(prod_filter_controls.group(0), test_filter_controls.group(0))
    print("✅ Copied filter control HTML from test")

# Write the updated production template
with open('/usr/local/bin/Main/templates/dsrcircuits.html', 'w') as f:
    f.write(prod_content)

print("\n✅ Production template updated with test filters!")
print("The filters should now work exactly like the test page")