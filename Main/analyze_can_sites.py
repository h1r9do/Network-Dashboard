#!/usr/bin/env python3
"""Analyze CAN 17 and CAN 22 circuits in detail from CSV"""

import csv
import os

# Find the latest CSV file
csv_files = []
for file in os.listdir('/var/www/html/circuitinfo/'):
    if file.startswith('tracking_data_') and file.endswith('.csv'):
        csv_files.append(file)

latest_file = sorted(csv_files)[-1]
csv_path = f'/var/www/html/circuitinfo/{latest_file}'

print(f"=== ANALYZING {latest_file} for CAN 17 and CAN 22 ===\n")

# Read and analyze
can_17_circuits = []
can_22_circuits = []

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        site_name = row.get('Site Name', '').strip()
        status = row.get('status', '').strip()
        
        if site_name == 'CAN 17' and status.lower() == 'enabled':
            can_17_circuits.append({
                'record_number': row.get('record_number', 'MISSING'),
                'site_name': site_name,
                'site_id': row.get('Site ID', 'Unknown'),
                'circuit_purpose': row.get('Circuit Purpose', 'Unknown'),
                'provider': row.get('Provider Name', 'Unknown'),
                'speed': row.get('Details Ordered Service Speed', 'Unknown'),
                'status': status,
                'date_updated': row.get('Date Record Updated', 'Unknown'),
                'enabled_date': row.get('Milestone Enabled', 'Unknown')
            })
        elif site_name == 'CAN 22' and status.lower() == 'enabled':
            can_22_circuits.append({
                'record_number': row.get('record_number', 'MISSING'),
                'site_name': site_name,
                'site_id': row.get('Site ID', 'Unknown'),
                'circuit_purpose': row.get('Circuit Purpose', 'Unknown'),
                'provider': row.get('Provider Name', 'Unknown'),
                'speed': row.get('Details Ordered Service Speed', 'Unknown'),
                'status': status,
                'date_updated': row.get('Date Record Updated', 'Unknown'),
                'enabled_date': row.get('Milestone Enabled', 'Unknown')
            })

print("🔍 CAN 17 - 3 Enabled Circuits in CSV:")
for i, circuit in enumerate(can_17_circuits, 1):
    print(f"\n  Circuit {i}:")
    print(f"    Record Number: {circuit['record_number']}")
    print(f"    Site ID: {circuit['site_id']}")
    print(f"    Circuit Purpose: {circuit['circuit_purpose']}")
    print(f"    Provider: {circuit['provider']}")
    print(f"    Speed: {circuit['speed']}")
    print(f"    Enabled Date: {circuit['enabled_date']}")

print("\n" + "="*60)
print("\n🔍 CAN 22 - 3 Enabled Circuits in CSV:")
for i, circuit in enumerate(can_22_circuits, 1):
    print(f"\n  Circuit {i}:")
    print(f"    Record Number: {circuit['record_number']}")
    print(f"    Site ID: {circuit['site_id']}")
    print(f"    Circuit Purpose: {circuit['circuit_purpose']}")
    print(f"    Provider: {circuit['provider']}")
    print(f"    Speed: {circuit['speed']}")
    print(f"    Enabled Date: {circuit['enabled_date']}")

# Now check what's in the database for these record numbers
print("\n" + "="*60)
print("\n📊 CHECKING DATABASE FOR THESE RECORD NUMBERS...")

import subprocess

# Get all record numbers
all_record_numbers = []
for circuit in can_17_circuits + can_22_circuits:
    if circuit['record_number'] != 'MISSING':
        all_record_numbers.append(circuit['record_number'])

if all_record_numbers:
    record_list = "', '".join(all_record_numbers)
    query = f"""
    SELECT record_number, site_name, circuit_purpose, provider_name, status, 
           DATE(created_at) as created_date, DATE(updated_at) as updated_date
    FROM circuits 
    WHERE record_number IN ('{record_list}')
    ORDER BY site_name, circuit_purpose;
    """
    
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-c', query],
        capture_output=True, text=True
    )
    
    if result.returncode == 0:
        print("\nDatabase records for these record numbers:")
        print(result.stdout)
    else:
        print(f"Database query error: {result.stderr}")
else:
    print("\nNo valid record numbers found to query")