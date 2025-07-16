#!/usr/bin/env python3
"""Simple export of delta between CSV and DSR badge"""

import csv
import subprocess
from datetime import datetime

# Query to get ALL the data we need
query = """
-- Get all enabled circuits with full details
SELECT 
    -- Circuit data
    c.site_name,
    c.site_id,
    c.circuit_purpose,
    c.provider_name as circuit_provider,
    c.details_service_speed as circuit_speed,
    c.billing_monthly_cost as circuit_cost,
    c.ip_address_start as circuit_ip,
    c.status,
    c.data_source,
    -- Meraki WAN1 data
    ec.wan1_provider as meraki_wan1_provider,
    ec.wan1_speed as meraki_wan1_speed,
    mi.wan1_ip as meraki_wan1_ip,
    -- Meraki WAN2 data
    ec.wan2_provider as meraki_wan2_provider,
    ec.wan2_speed as meraki_wan2_speed,
    mi.wan2_ip as meraki_wan2_ip,
    -- Meraki metadata
    CASE WHEN mi.network_name IS NOT NULL THEN 'Yes' ELSE 'No' END as has_meraki_device,
    CASE WHEN mi.device_tags @> ARRAY['Discount-Tire']::text[] THEN 'Yes' ELSE 'No' END as has_dt_tag,
    -- Exclusion analysis
    CASE 
        WHEN c.data_source != 'csv_import' THEN 'Not from CSV import'
        WHEN mi.network_name IS NULL THEN 'No Meraki device'
        WHEN NOT (mi.device_tags @> ARRAY['Discount-Tire']::text[]) THEN 'No Discount-Tire tag'
        WHEN mi.network_name ILIKE '%hub%' THEN 'Hub site'
        WHEN mi.network_name ILIKE '%lab%' THEN 'Lab site'
        WHEN mi.network_name ILIKE '%test%' THEN 'Test site'
        WHEN mi.network_name ILIKE '%voice%' THEN 'Voice site'
        WHEN ec.network_name IS NULL THEN 'Not in enriched_circuits'
        ELSE 'Eligible'
    END as exclusion_reason,
    -- Provider matching
    CASE 
        WHEN c.provider_name IS NULL THEN 'No provider'
        WHEN LOWER(c.provider_name) = LOWER(ec.wan1_provider) THEN 'Exact match WAN1'
        WHEN LOWER(c.provider_name) = LOWER(ec.wan2_provider) THEN 'Exact match WAN2'
        WHEN ec.wan1_provider IS NOT NULL AND 
             LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan1_provider, ' ', 1)) || '%' THEN 'Partial match WAN1'
        WHEN ec.wan2_provider IS NOT NULL AND 
             LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan2_provider, ' ', 1)) || '%' THEN 'Partial match WAN2'
        ELSE 'No match'
    END as provider_match,
    -- Would get DSR badge?
    CASE 
        WHEN c.data_source = 'csv_import' 
         AND mi.device_tags @> ARRAY['Discount-Tire']::text[]
         AND NOT (mi.network_name ILIKE '%hub%' OR mi.network_name ILIKE '%lab%' OR 
                  mi.network_name ILIKE '%test%' OR mi.network_name ILIKE '%voice%')
         AND ec.network_name IS NOT NULL
         AND (LOWER(c.provider_name) = LOWER(ec.wan1_provider) OR 
              LOWER(c.provider_name) = LOWER(ec.wan2_provider) OR
              (ec.wan1_provider IS NOT NULL AND LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan1_provider, ' ', 1)) || '%') OR
              (ec.wan2_provider IS NOT NULL AND LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan2_provider, ' ', 1)) || '%'))
        THEN 'Yes'
        ELSE 'No'
    END as would_get_dsr_badge
FROM circuits c
LEFT JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
LEFT JOIN enriched_circuits ec ON LOWER(c.site_name) = LOWER(ec.network_name)
WHERE c.status = 'Enabled'
ORDER BY c.site_name, c.circuit_purpose;
"""

print("Exporting delta analysis...")

# Execute query
result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '\t', '-c', query],
    capture_output=True, text=True
)

if result.returncode != 0:
    print(f"Query error: {result.stderr}")
    exit(1)

# Parse results and write CSV
output_file = f'/usr/local/bin/Main/dsr_delta_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
fieldnames = [
    'site_name', 'site_id', 'circuit_purpose', 'circuit_provider', 'circuit_speed',
    'circuit_cost', 'circuit_ip', 'status', 'data_source', 'meraki_wan1_provider',
    'meraki_wan1_speed', 'meraki_wan1_ip', 'meraki_wan2_provider',
    'meraki_wan2_speed', 'meraki_wan2_ip', 'has_meraki_device',
    'has_dt_tag', 'exclusion_reason', 'provider_match', 'would_get_dsr_badge'
]

rows_written = 0
dsr_badge_yes = 0
dsr_badge_no = 0
exclusion_counts = {}

with open(output_file, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('\t')
            if len(parts) >= 20:
                row = dict(zip(fieldnames, parts))
                writer.writerow(row)
                rows_written += 1
                
                # Count statistics
                if row['would_get_dsr_badge'] == 'Yes':
                    dsr_badge_yes += 1
                else:
                    dsr_badge_no += 1
                    reason = row['exclusion_reason']
                    exclusion_counts[reason] = exclusion_counts.get(reason, 0) + 1

print(f"\nExport complete!")
print(f"File: {output_file}")
print(f"Total rows: {rows_written}")
print(f"\nDSR Badge Summary:")
print(f"- Would get DSR badge: {dsr_badge_yes}")
print(f"- Would NOT get DSR badge: {dsr_badge_no}")
print(f"\nExclusion reasons:")
for reason, count in sorted(exclusion_counts.items(), key=lambda x: x[1], reverse=True):
    if reason != 'Eligible':
        print(f"  - {reason}: {count}")

# Also read CSV file counts
csv_count = 0
with open('/var/www/html/circuitinfo/tracking_data_2025-07-11.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['status'] == 'Enabled':
            csv_count += 1

print(f"\nDelta Analysis:")
print(f"- CSV enabled circuits: {csv_count}")
print(f"- Database enabled circuits: {rows_written}")
print(f"- Would get DSR badge: {dsr_badge_yes}")
print(f"- Test page shows: 1689")
print(f"- Unexplained difference: {1689 - dsr_badge_yes}")

# Create a second file with just the excluded circuits
excluded_file = f'/usr/local/bin/Main/dsr_excluded_circuits_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
print(f"\nCreating excluded circuits file: {excluded_file}")

with open(output_file, 'r') as infile:
    reader = csv.DictReader(infile)
    with open(excluded_file, 'w', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        excluded_count = 0
        for row in reader:
            if row['would_get_dsr_badge'] == 'No' and row['data_source'] == 'csv_import':
                writer.writerow(row)
                excluded_count += 1

print(f"Excluded circuits written: {excluded_count}")