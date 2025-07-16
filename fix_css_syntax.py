#!/usr/bin/env python3
"""
Fix CSS syntax error in template
"""

print("=== FIXING CSS SYNTAX ERROR ===\n")

# Read the template
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# Fix the malformed CSS around line 122
# The issue is the line that says:
# .filter-control:nth-child(8) { width: 3.125%; }   /* Action */.filter-control input, .filter-control select {

# Find and fix this
broken_css = ".filter-control:nth-child(8) { width: 3.125%; }   /* Action */.filter-control input, .filter-control select {"

fixed_css = """.filter-control:nth-child(8) { width: 3.125%; }   /* Action */
        
        .filter-control input, .filter-control select {"""

if broken_css in content:
    content = content.replace(broken_css, fixed_css)
    print("✅ Fixed malformed CSS line")
else:
    print("❌ Could not find malformed CSS line")

# Write the fixed template
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("✅ CSS syntax error fixed")