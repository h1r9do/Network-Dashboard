#!/usr/bin/env python3
import json
import sys
import subprocess

# Get data from API
result = subprocess.run(['curl', '-s', 'http://10.0.145.130:5052/api/inventory-datacenter'], capture_output=True, text=True)
data = json.loads(result.stdout)
inventory = data['inventory']

# Track site transitions
current_site = None
site_counts = {}

print('Site grouping verification:')
print('-' * 50)

for i, item in enumerate(inventory):
    site = item['site']
    
    # Count items per site
    if site not in site_counts:
        site_counts[site] = 0
    site_counts[site] += 1
    
    # Show when site changes
    if site != current_site:
        if current_site:
            print(f'  ...{site_counts[current_site]} total items in {current_site}')
        print(f'\n--- {site} ---')
        current_site = site
        # Show first few items of this site
        print(f'  {item["hostname"] or "(component)"} - {item["position"]} - {item["model"][:30] if item["model"] else "(no model)"}')
    elif i < 50:  # Show first 50 items
        print(f'  {item["hostname"] or "(component)"} - {item["position"]} - {item["model"][:30] if item["model"] else "(no model)"}')

# Final site count
if current_site:
    print(f'  ...{site_counts[current_site]} total items in {current_site}')

print(f'\nSite summary:')
for site, count in sorted(site_counts.items()):
    print(f'  {site}: {count} items')
    
print(f'\nTotal items: {len(inventory)}')