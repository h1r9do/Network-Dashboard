#!/usr/bin/env python3
"""
Check for column count mismatch in the template
"""

print("=== CHECKING FOR COLUMN MISMATCH ===\n")

with open('/usr/local/bin/Main/templates/dsrcircuits.html', 'r') as f:
    content = f.read()

import re

# Count <th> tags in thead
thead_match = re.search(r'<thead>(.*?)</thead>', content, re.DOTALL)
if thead_match:
    thead_content = thead_match.group(1)
    th_count = thead_content.count('<th')
    print(f"Number of <th> in header: {th_count}")
    
    # Extract header columns
    headers = re.findall(r'<th[^>]*>(.*?)</th>', thead_content)
    print("\nHeader columns:")
    for i, header in enumerate(headers):
        print(f"  {i+1}. {header.strip()}")

# Count <td> tags in a typical row
tbody_match = re.search(r'<tbody>.*?<tr[^>]*>(.*?)</tr>', content, re.DOTALL)
if tbody_match:
    row_content = tbody_match.group(1)
    td_count = row_content.count('<td')
    print(f"\nNumber of <td> in body rows: {td_count}")

# Check if they match
if th_count != td_count:
    print(f"\n❌ MISMATCH! Headers: {th_count}, Body cells: {td_count}")
    print("This is causing the DataTables error!")
else:
    print(f"\n✅ Column counts match: {th_count}")

# Look for the specific row structure
print("\nChecking row structure...")
row_pattern = r'{% for entry in grouped_data %}.*?</tr>'
row_match = re.search(row_pattern, content, re.DOTALL)
if row_match:
    row_template = row_match.group(0)
    td_tags = re.findall(r'<td[^>]*>', row_template)
    print(f"Found {len(td_tags)} <td> tags in row template")
    
    # The production template expects 9 columns (with roles)
    # The test template has 7 columns (without roles)
    # This mismatch is likely the issue!