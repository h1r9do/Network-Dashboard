#!/usr/bin/env python3
"""
Check what's happening around the error line
"""

print("=== CHECKING ERROR LOCATION ===\n")

# The error is at line 43614 in the RENDERED output, not the template
# This means it's in the generated HTML after Jinja2 processing
# Let's look for any remaining Jinja2 syntax that might be causing issues

with open('/usr/local/bin/templates/dsrcircuits_test.html', 'r') as f:
    content = f.read()

# Look for any remaining Jinja2 loops in JavaScript
import re

# Find all Jinja2 tags in JavaScript sections
jinja_in_js = re.findall(r'<script.*?>(.*?)</script>', content, re.DOTALL)

print("Checking for Jinja2 tags in JavaScript sections...")
for i, script in enumerate(jinja_in_js):
    if '{%' in script or '{{' in script:
        print(f"\nScript section {i+1} contains Jinja2 tags:")
        # Show lines with Jinja2
        lines = script.split('\n')
        for j, line in enumerate(lines):
            if '{%' in line or '{{' in line:
                print(f"  Line {j+1}: {line.strip()}")

# Check for any unclosed parentheses in filter-related code
print("\n\nChecking for unclosed parentheses in filter code...")
filter_section = re.search(r'// Initialize filters.*?(?=</script>|$)', content, re.DOTALL)
if filter_section:
    code = filter_section.group(0)
    open_parens = code.count('(')
    close_parens = code.count(')')
    print(f"Open parentheses: {open_parens}")
    print(f"Close parentheses: {close_parens}")
    if open_parens != close_parens:
        print("⚠️ MISMATCH - Missing closing parenthesis!")

# Look for any forEach loops that might be problematic
print("\n\nChecking for forEach loops...")
foreach_matches = re.findall(r'\.forEach\([^)]*\)', content)
for match in foreach_matches[:5]:  # Show first 5
    print(f"  {match[:80]}...")

print("\n\nTo fix this, we need to see the actual rendered output.")
print("In the browser, view page source and search for line 43614")