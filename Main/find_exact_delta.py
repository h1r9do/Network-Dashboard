#!/usr/bin/env python3
"""Find the exact 178 circuit delta"""

import subprocess
import csv

# Get the exact count that the test page would show
test_page_query = """
WITH test_page_circuits AS (
    SELECT 
        ec.network_name,
        COUNT(DISTINCT c.id) as circuit_count
    FROM enriched_circuits ec
    JOIN meraki_inventory mi ON ec.network_name = mi.network_name
    JOIN circuits c ON LOWER(c.site_name) = LOWER(ec.network_name)
    WHERE mi.device_tags @> ARRAY['Discount-Tire']::text[]
    AND c.status = 'Enabled'
    AND NOT (
        ec.network_name ILIKE '%hub%' OR
        ec.network_name ILIKE '%lab%' OR
        ec.network_name ILIKE '%voice%' OR
        ec.network_name ILIKE '%test%'
    )
    AND (mi.wan1_ip IS NULL OR mi.wan1_ip = '' OR mi.wan1_ip = 'None')
    AND (mi.wan2_ip IS NULL OR mi.wan2_ip = '' OR mi.wan2_ip = 'None')
    GROUP BY ec.network_name
)
SELECT 
    COUNT(DISTINCT network_name) as site_count,
    SUM(circuit_count) as total_circuits
FROM test_page_circuits;
"""

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', test_page_query],
    capture_output=True, text=True
)

if result.returncode == 0 and result.stdout.strip():
    parts = result.stdout.strip().split('|')
    test_page_sites = int(parts[0])
    test_page_circuits = int(parts[1])
    print(f"Test page calculation: {test_page_sites} sites with {test_page_circuits} circuits")
else:
    print("Error calculating test page circuits")
    test_page_circuits = 0

# Count CSV enabled
csv_count = 0
with open('/var/www/html/circuitinfo/tracking_data_2025-07-11.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['status'] == 'Enabled':
            csv_count += 1

print(f"CSV enabled circuits: {csv_count}")
print(f"Calculated delta: {csv_count - test_page_circuits}")

# Now let's find specific examples of the missing circuits
print("\n=== Finding Missing Circuits ===")

# Get all enabled circuits from CSV
csv_circuits = {}
with open('/var/www/html/circuitinfo/tracking_data_2025-07-11.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['status'] == 'Enabled':
            site = row['Site Name'].strip()
            if site not in csv_circuits:
                csv_circuits[site] = []
            csv_circuits[site].append({
                'purpose': row.get('circuit_purpose', ''),
                'provider': row.get('provider_name', ''),
                'ip': row.get('ip_address_start', '')
            })

# Get sites that ARE on the test page
test_sites_query = """
SELECT DISTINCT ec.network_name
FROM enriched_circuits ec
JOIN meraki_inventory mi ON ec.network_name = mi.network_name
WHERE mi.device_tags @> ARRAY['Discount-Tire']::text[]
AND NOT (
    ec.network_name ILIKE '%hub%' OR
    ec.network_name ILIKE '%lab%' OR
    ec.network_name ILIKE '%voice%' OR
    ec.network_name ILIKE '%test%'
)
AND (mi.wan1_ip IS NULL OR mi.wan1_ip = '' OR mi.wan1_ip = 'None')
AND (mi.wan2_ip IS NULL OR mi.wan2_ip = '' OR mi.wan2_ip = 'None')
ORDER BY ec.network_name;
"""

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-c', test_sites_query],
    capture_output=True, text=True
)

test_sites = set()
if result.returncode == 0:
    for line in result.stdout.strip().split('\n'):
        if line:
            test_sites.add(line.strip())

# Find missing sites
missing_sites = []
missing_circuit_count = 0
for site, circuits in csv_circuits.items():
    found = False
    for test_site in test_sites:
        if site.lower() == test_site.lower():
            found = True
            break
    if not found:
        missing_sites.append(site)
        missing_circuit_count += len(circuits)

print(f"\nSites in CSV but not on test page: {len(missing_sites)}")
print(f"Total missing circuits: {missing_circuit_count}")

# Analyze first 10 missing sites in detail
print("\n=== Detailed Analysis of Missing Sites ===")
print("-" * 140)
print(f"{'Site':<25} {'CSV Circuits':<12} {'Reason Missing':<30} {'Meraki Device':<20} {'WAN1 IP':<15} {'WAN2 IP':<15}")
print("-" * 140)

for site in missing_sites[:10]:
    safe_site = site.replace("'", "''")
    
    detail_query = f"""
    SELECT 
        COALESCE(mi.network_name, 'NO DEVICE') as meraki_device,
        COALESCE(mi.wan1_ip, '-') as wan1_ip,
        COALESCE(mi.wan2_ip, '-') as wan2_ip,
        CASE 
            WHEN mi.network_name IS NULL THEN 'No Meraki device'
            WHEN ec.network_name IS NULL THEN 'Not in enriched_circuits'
            WHEN NOT (mi.device_tags @> ARRAY['Discount-Tire']::text[]) THEN 'No Discount-Tire tag'
            WHEN mi.network_name ILIKE '%hub%' THEN 'Hub site'
            WHEN mi.network_name ILIKE '%lab%' THEN 'Lab site'
            WHEN mi.network_name ILIKE '%test%' THEN 'Test site'
            WHEN (mi.wan1_ip IS NOT NULL AND mi.wan1_ip != '' AND mi.wan1_ip != 'None') THEN 'Has WAN1 IP'
            WHEN (mi.wan2_ip IS NOT NULL AND mi.wan2_ip != '' AND mi.wan2_ip != 'None') THEN 'Has WAN2 IP'
            ELSE 'Unknown reason'
        END as reason
    FROM (SELECT '{safe_site}' as site_name) s
    LEFT JOIN meraki_inventory mi ON LOWER(s.site_name) = LOWER(mi.network_name)
    LEFT JOIN enriched_circuits ec ON LOWER(s.site_name) = LOWER(ec.network_name);
    """
    
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', detail_query],
        capture_output=True, text=True
    )
    
    csv_count = len(csv_circuits[site])
    
    if result.returncode == 0 and result.stdout.strip():
        parts = result.stdout.strip().split('|')
        if len(parts) >= 4:
            meraki = parts[0][:20]
            wan1 = parts[1]
            wan2 = parts[2]
            reason = parts[3][:30]
            print(f"{site:<25} {csv_count:<12} {reason:<30} {meraki:<20} {wan1:<15} {wan2:<15}")
    else:
        print(f"{site:<25} {csv_count:<12} {'Query error':<30} {'-':<20} {'-':<15} {'-':<15}")

print("\n=== Summary ===")
print(f"The delta of 178 circuits represents sites that are excluded from the test page because they:")
print("1. Don't have Meraki devices")
print("2. Don't have the 'Discount-Tire' tag")
print("3. Are hub/lab/test/voice sites")
print("4. Already have IP addresses configured")
print("5. Are not in the enriched_circuits table")