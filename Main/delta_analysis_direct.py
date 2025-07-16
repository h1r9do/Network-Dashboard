#!/usr/bin/env python3
"""Direct delta analysis using subprocess calls"""

import csv
import subprocess
import json
from collections import defaultdict

# First read the CSV
print("=== Reading CSV File ===")
csv_enabled = defaultdict(list)
csv_total = 0

with open('/var/www/html/circuitinfo/tracking_data_2025-07-11.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['status'] == 'Enabled':
            csv_total += 1
            site = row['Site Name'].strip()
            csv_enabled[site].append({
                'purpose': row.get('circuit_purpose', ''),
                'provider': row.get('provider_name', ''),
                'speed': row.get('details_service_speed', ''),
                'ip': row.get('ip_address_start', '')
            })

print(f"CSV: {csv_total} enabled circuits across {len(csv_enabled)} sites")

# Get test page sites
print("\n=== Querying Test Page Sites ===")
test_query = """
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
AND (mi.wan2_ip IS NULL OR mi.wan2_ip = '' OR mi.wan2_ip = 'None');
"""

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-c', test_query],
    capture_output=True, text=True
)

test_page_sites = set()
if result.returncode == 0:
    for line in result.stdout.strip().split('\n'):
        if line:
            test_page_sites.add(line)

print(f"Test page shows: {len(test_page_sites)} sites")

# Find delta sites
delta_sites = []
for site in csv_enabled:
    if site not in test_page_sites and site.lower() not in [s.lower() for s in test_page_sites]:
        delta_sites.append(site)

delta_circuits = sum(len(csv_enabled[site]) for site in delta_sites)
print(f"\nDelta: {len(delta_sites)} sites with {delta_circuits} circuits not on test page")

# Analyze first 20 delta sites
print("\n=== Analyzing Delta Sites (First 20) ===")
print("-" * 130)
print(f"{'Site Name':<30} {'CSV Circuits':<12} {'DB Status':<25} {'WAN1 IP':<15} {'WAN2 IP':<15} {'WAN1 Provider':<20}")
print("-" * 130)

for site in delta_sites[:20]:
    # Escape single quotes in site name
    safe_site = site.replace("'", "''")
    
    # Query for this specific site
    site_query = f"""
    SELECT 
        c.site_name,
        COUNT(DISTINCT c.id) as db_circuits,
        COALESCE(mi.network_name, 'NO MERAKI DEVICE') as meraki_status,
        COALESCE(mi.wan1_ip, '-') as wan1_ip,
        COALESCE(mi.wan2_ip, '-') as wan2_ip,
        COALESCE(mi.wan1_provider, '-') as wan1_prov,
        COALESCE(mi.wan2_provider, '-') as wan2_prov,
        CASE 
            WHEN mi.network_name IS NULL THEN 'No Meraki device'
            WHEN NOT (mi.device_tags @> ARRAY['Discount-Tire']::text[]) THEN 'No DT tag'
            WHEN mi.network_name ILIKE '%hub%' THEN 'Hub site'
            WHEN mi.network_name ILIKE '%lab%' THEN 'Lab site'
            WHEN (mi.wan1_ip IS NOT NULL AND mi.wan1_ip != '' AND mi.wan1_ip != 'None') THEN 'Has WAN1 IP'
            WHEN (mi.wan2_ip IS NOT NULL AND mi.wan2_ip != '' AND mi.wan2_ip != 'None') THEN 'Has WAN2 IP'
            ELSE 'Unknown'
        END as reason
    FROM circuits c
    LEFT JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
    WHERE c.status = 'Enabled' AND c.site_name = '{safe_site}'
    GROUP BY c.site_name, mi.network_name, mi.wan1_ip, mi.wan2_ip, 
             mi.wan1_provider, mi.wan2_provider, mi.device_tags;
    """
    
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', site_query],
        capture_output=True, text=True
    )
    
    csv_count = len(csv_enabled[site])
    
    if result.returncode == 0 and result.stdout.strip():
        parts = result.stdout.strip().split('|')
        if len(parts) >= 8:
            db_count = parts[1]
            reason = parts[7]
            wan1_ip = parts[3] if parts[3] != 'None' else '-'
            wan2_ip = parts[4] if parts[4] != 'None' else '-'
            wan1_prov = parts[5][:20]
            
            print(f"{site:<30} {csv_count:<12} {reason:<25} {wan1_ip:<15} {wan2_ip:<15} {wan1_prov:<20}")
    else:
        print(f"{site:<30} {csv_count:<12} {'NOT IN DATABASE':<25} {'-':<15} {'-':<15} {'-':<20}")

# Summary statistics
print("\n=== Summary Statistics ===")
summary_query = """
WITH delta_sites AS (
    SELECT UNNEST(ARRAY[{}]::text[]) as site_name
)
SELECT 
    COUNT(DISTINCT CASE WHEN mi.network_name IS NULL THEN ds.site_name END) as no_meraki,
    COUNT(DISTINCT CASE WHEN mi.network_name IS NOT NULL AND NOT (mi.device_tags @> ARRAY['Discount-Tire']::text[]) THEN ds.site_name END) as no_dt_tag,
    COUNT(DISTINCT CASE WHEN mi.network_name ILIKE '%hub%' OR mi.network_name ILIKE '%lab%' THEN ds.site_name END) as excluded_type,
    COUNT(DISTINCT CASE WHEN (mi.wan1_ip IS NOT NULL AND mi.wan1_ip != '' AND mi.wan1_ip != 'None') OR
                           (mi.wan2_ip IS NOT NULL AND mi.wan2_ip != '' AND mi.wan2_ip != 'None') THEN ds.site_name END) as has_ips
FROM delta_sites ds
LEFT JOIN meraki_inventory mi ON LOWER(ds.site_name) = LOWER(mi.network_name);
"""

# Format site list for query
site_array = "'" + "','".join([s.replace("'", "''") for s in delta_sites[:100]]) + "'"
formatted_query = summary_query.format(site_array)

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', formatted_query],
    capture_output=True, text=True
)

if result.returncode == 0 and result.stdout.strip():
    parts = result.stdout.strip().split('|')
    if len(parts) >= 4:
        print(f"\nReasons for exclusion (first 100 delta sites):")
        print(f"- No Meraki device: {parts[0]} sites")
        print(f"- No Discount-Tire tag: {parts[1]} sites")  
        print(f"- Hub/Lab site: {parts[2]} sites")
        print(f"- Already has IPs: {parts[3]} sites")

print(f"\n=== FINAL SUMMARY ===")
print(f"CSV shows: {csv_total} enabled circuits")
print(f"Test page would show: {csv_total - delta_circuits} circuits")
print(f"Delta: {delta_circuits} circuits excluded")