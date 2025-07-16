#!/usr/bin/env python3
"""
Fix JavaScript syntax error
"""

print("=== FIXING JAVASCRIPT SYNTAX ERROR ===\n")

with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    lines = f.readlines()

# Find line 74755 or around there
print(f"Total lines in file: {len(lines)}")

# The file is much smaller than 74755 lines, so let's search for syntax errors
# Look for the debugging code we just added
found_error = False
for i, line in enumerate(lines):
    # Check for common syntax errors in our debug code
    if 'console.log("' in line and line.count('"') % 2 != 0:
        print(f"Found unmatched quotes at line {i+1}: {line.strip()}")
        found_error = True
    
    # Check for template syntax that might cause issues
    if '{{' in line and 'console.log' in line:
        print(f"Found template syntax in JavaScript at line {i+1}: {line.strip()}")
        found_error = True

# Let's look for the specific error around our debug code
# The error is likely in the escaping of quotes
content = ''.join(lines)

# Fix potential issues with quote escaping in console.log statements
import re

# Fix double quotes inside console.log
old_patterns = [
    'console.log("  Option " + i + ": \'" + $(this).val() + "\' (text: \'" + $(this).text() + "\')");',
    'console.log("    " + (i+1) + ". " + site + " - WAN1: \'" + wan1 + "\'");'
]

new_patterns = [
    'console.log("  Option " + i + ": " + JSON.stringify($(this).val()) + " (text: " + JSON.stringify($(this).text()) + ")");',
    'console.log("    " + (i+1) + ". " + site + " - WAN1: " + JSON.stringify(wan1));'
]

for old, new in zip(old_patterns, new_patterns):
    if old in content:
        content = content.replace(old, new)
        print(f"Fixed: {old[:50]}...")

# Also fix any hanging parentheses in the filter initialization
# Look for the Jinja2 template syntax that might be causing issues
if '{% endfor %}' in content:
    # Make sure all Jinja2 loops are properly closed
    jinja_opens = content.count('{% for ')
    jinja_closes = content.count('{% endfor %}')
    print(f"\nJinja2 loops: {jinja_opens} opens, {jinja_closes} closes")
    
# Write the fixed content
with open('/usr/local/bin/templates/dsrcircuits_test.html', 'w') as f:
    f.write(content)

print("\n✅ Applied syntax fixes")
print("If error persists, it may be in the generated JavaScript from Jinja2 templates")