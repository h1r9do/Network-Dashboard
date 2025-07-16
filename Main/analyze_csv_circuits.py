#!/usr/bin/env python3
"""Analyze the latest CSV file to find sites with more than 2 enabled circuits"""

import csv
import os
from collections import defaultdict

# Find the latest CSV file
csv_files = []
for file in os.listdir('/var/www/html/circuitinfo/'):
    if file.startswith('tracking_data_') and file.endswith('.csv'):
        csv_files.append(file)

latest_file = sorted(csv_files)[-1]
csv_path = f'/var/www/html/circuitinfo/{latest_file}'

print(f"=== ANALYZING {latest_file} ===\n")

# Count circuits per site
site_circuit_counts = defaultdict(list)
enabled_count = 0
total_count = 0

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    # Find the status column (it might be at different positions)
    status_column = None
    site_name_column = None
    for column in reader.fieldnames:
        if 'status' in column.lower():
            status_column = column
        if 'site name' in column.lower():
            site_name_column = column
    
    print(f"Status column: {status_column}")
    print(f"Site name column: {site_name_column}")
    print(f"Total columns: {len(reader.fieldnames)}")
    print()
    
    for row in reader:
        total_count += 1
        site_name = row.get(site_name_column, '').strip()
        status = row.get(status_column, '').strip()
        
        if status.lower() == 'enabled' and site_name:
            enabled_count += 1
            site_circuit_counts[site_name].append(row)

print(f"📊 CSV ANALYSIS RESULTS:")
print(f"   Total circuits in CSV: {total_count}")
print(f"   Enabled circuits: {enabled_count}")
print(f"   Unique sites with enabled circuits: {len(site_circuit_counts)}")
print()

# Find sites with more than 2 circuits
sites_with_multiple = {}
for site_name, circuits in site_circuit_counts.items():
    count = len(circuits)
    if count > 2:
        sites_with_multiple[site_name] = count

print(f"🔍 SITES WITH MORE THAN 2 ENABLED CIRCUITS:")
if sites_with_multiple:
    for site_name, count in sorted(sites_with_multiple.items(), key=lambda x: x[1], reverse=True):
        print(f"   {site_name}: {count} circuits")
        
        # Show details for first few
        if len(sites_with_multiple) <= 10:
            circuits = site_circuit_counts[site_name]
            for i, circuit in enumerate(circuits, 1):
                provider = circuit.get('Provider Name', 'Unknown')
                purpose = circuit.get('Circuit Purpose', 'Unknown')
                speed = circuit.get('Details Ordered Service Speed', 'Unknown')
                print(f"     {i}. {purpose} - {provider} ({speed})")
            print()
else:
    print("   ❌ No sites found with more than 2 enabled circuits in CSV")

print()
print(f"📈 CIRCUIT COUNT DISTRIBUTION:")
distribution = defaultdict(int)
for count in site_circuit_counts.values():
    distribution[len(count)] += 1

for circuit_count in sorted(distribution.keys()):
    site_count = distribution[circuit_count]
    print(f"   {site_count} sites with {circuit_count} circuit(s)")

# Check some example sites with exactly 2 circuits
sites_with_2 = [(site, circuits) for site, circuits in site_circuit_counts.items() if len(circuits) == 2]
if sites_with_2:
    print(f"\n🔍 EXAMPLES OF SITES WITH EXACTLY 2 CIRCUITS (first 5):")
    for site_name, circuits in sites_with_2[:5]:
        print(f"   {site_name}:")
        for i, circuit in enumerate(circuits, 1):
            provider = circuit.get('Provider Name', 'Unknown')
            purpose = circuit.get('Circuit Purpose', 'Unknown')
            speed = circuit.get('Details Ordered Service Speed', 'Unknown')
            print(f"     {i}. {purpose} - {provider} ({speed})")
        print()