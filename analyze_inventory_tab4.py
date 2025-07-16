#!/usr/bin/env python3
import json
import sys
import requests

# Fetch the data
response = requests.get('http://10.0.145.130:5052/api/inventory-datacenter')
data = response.json()
inventory = data.get('inventory', [])

# Check grouping structure
print('Analysis of device grouping structure:')
print(f'Total items: {len(inventory)}')

# Count by position
position_counts = {}
for item in inventory:
    pos = item['position']
    position_counts[pos] = position_counts.get(pos, 0) + 1

print('\nGrouping by Position:')
for pos, count in sorted(position_counts.items()):
    print(f'  {pos}: {count}')

# Check parent-child relationships
standalone_with_children = {}
for item in inventory:
    if item['position'] != 'Standalone' and item.get('parent_hostname'):
        parent = item['parent_hostname']
        if parent not in standalone_with_children:
            standalone_with_children[parent] = []
        standalone_with_children[parent].append(item)

print(f'\nNumber of parent devices: {len(standalone_with_children)}')
print('\nSample parent-child relationships:')
for i, (parent, children) in enumerate(list(standalone_with_children.items())[:3]):
    print(f'\n  Parent: {parent}')
    print(f'  Children ({len(children)}):')
    for child in children[:3]:
        ser = child.get('serial_number', '')
        mod = child.get('model', '')
        loc = child.get('port_location', '')
        print(f'    - {loc} | Serial: {ser} | Model: {mod}')

# Analyze EOL/EOS dates
print('\n\nEOL/EOS Date Analysis:')
has_eos = 0
has_eol = 0
both = 0
neither = 0

for item in inventory:
    eos = item.get('end_of_sale', '').strip()
    eol = item.get('end_of_support', '').strip()
    
    if eos and eol:
        both += 1
    elif eos:
        has_eos += 1
    elif eol:
        has_eol += 1
    else:
        neither += 1

print(f'Items with both EOS and EOL dates: {both}')
print(f'Items with only EOS date: {has_eos}')
print(f'Items with only EOL date: {has_eol}')
print(f'Items with neither date: {neither}')

# Show table structure
print('\n\nTable Column Structure:')
if inventory:
    print('Columns:', ', '.join(inventory[0].keys()))