#!/usr/bin/env python3
"""Export delta analysis with ARIN provider information"""

import csv
import subprocess
from datetime import datetime

# Query to get ALL the data including ARIN info
query = """
-- Get all enabled circuits with full details including ARIN
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
    mi.wan1_arin_provider as wan1_arin_provider,
    -- Meraki WAN2 data
    ec.wan2_provider as meraki_wan2_provider,
    ec.wan2_speed as meraki_wan2_speed,
    mi.wan2_ip as meraki_wan2_ip,
    mi.wan2_arin_provider as wan2_arin_provider,
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
    -- ARIN vs Meraki provider comparison
    CASE 
        WHEN mi.wan1_arin_provider IS NOT NULL AND ec.wan1_provider IS NOT NULL THEN
            CASE 
                WHEN LOWER(mi.wan1_arin_provider) LIKE '%' || LOWER(SPLIT_PART(ec.wan1_provider, ' ', 1)) || '%' THEN 'WAN1 ARIN matches Meraki'
                ELSE 'WAN1 ARIN differs from Meraki'
            END
        ELSE 'No WAN1 ARIN data'
    END as wan1_arin_match,
    CASE 
        WHEN mi.wan2_arin_provider IS NOT NULL AND ec.wan2_provider IS NOT NULL THEN
            CASE 
                WHEN LOWER(mi.wan2_arin_provider) LIKE '%' || LOWER(SPLIT_PART(ec.wan2_provider, ' ', 1)) || '%' THEN 'WAN2 ARIN matches Meraki'
                ELSE 'WAN2 ARIN differs from Meraki'
            END
        ELSE 'No WAN2 ARIN data'
    END as wan2_arin_match,
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

print("Exporting delta analysis with ARIN data...")

# Execute query
result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '\t', '-c', query],
    capture_output=True, text=True
)

if result.returncode != 0:
    print(f"Query error: {result.stderr}")
    exit(1)

# Parse results and write CSV
output_file = f'/usr/local/bin/Main/dsr_delta_with_arin_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
fieldnames = [
    'site_name', 'site_id', 'circuit_purpose', 'circuit_provider', 'circuit_speed',
    'circuit_cost', 'circuit_ip', 'status', 'data_source', 
    'meraki_wan1_provider', 'meraki_wan1_speed', 'meraki_wan1_ip', 
    'wan1_arin_provider',
    'meraki_wan2_provider', 'meraki_wan2_speed', 'meraki_wan2_ip',
    'wan2_arin_provider',
    'has_meraki_device', 'has_dt_tag', 'exclusion_reason', 'provider_match',
    'wan1_arin_match', 'wan2_arin_match', 'would_get_dsr_badge'
]

rows_written = 0
dsr_badge_yes = 0
dsr_badge_no = 0
arin_mismatch_count = 0

with open(output_file, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('\t')
            if len(parts) >= 24:
                row = dict(zip(fieldnames, parts))
                writer.writerow(row)
                rows_written += 1
                
                # Count statistics
                if row['would_get_dsr_badge'] == 'Yes':
                    dsr_badge_yes += 1
                else:
                    dsr_badge_no += 1
                
                # Count ARIN mismatches
                if 'differs' in row.get('wan1_arin_match', '') or 'differs' in row.get('wan2_arin_match', ''):
                    arin_mismatch_count += 1

print(f"\nExport complete!")
print(f"File: {output_file}")
print(f"Total rows: {rows_written}")
print(f"\nDSR Badge Summary:")
print(f"- Would get DSR badge: {dsr_badge_yes}")
print(f"- Would NOT get DSR badge: {dsr_badge_no}")
print(f"\nARIN Data:")
print(f"- Sites with ARIN/Meraki provider mismatch: {arin_mismatch_count}")

# Create a filtered file with just ARIN mismatches
arin_mismatch_file = f'/usr/local/bin/Main/dsr_arin_mismatches_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
print(f"\nCreating ARIN mismatch file: {arin_mismatch_file}")

with open(output_file, 'r') as infile:
    reader = csv.DictReader(infile)
    with open(arin_mismatch_file, 'w', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        mismatch_count = 0
        for row in reader:
            if ('differs' in row.get('wan1_arin_match', '') or 
                'differs' in row.get('wan2_arin_match', '')):
                writer.writerow(row)
                mismatch_count += 1

print(f"ARIN mismatch records written: {mismatch_count}")

# Create summary of ARIN providers
print("\nCreating ARIN provider summary...")
arin_summary_query = """
SELECT 
    COUNT(DISTINCT CASE WHEN wan1_arin_provider IS NOT NULL THEN site_name END) as sites_with_wan1_arin,
    COUNT(DISTINCT CASE WHEN wan2_arin_provider IS NOT NULL THEN site_name END) as sites_with_wan2_arin,
    COUNT(DISTINCT CASE WHEN wan1_arin_provider IS NOT NULL OR wan2_arin_provider IS NOT NULL THEN site_name END) as sites_with_any_arin
FROM meraki_inventory
WHERE network_name IN (
    SELECT DISTINCT site_name FROM circuits WHERE status = 'Enabled'
);
"""

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', arin_summary_query],
    capture_output=True, text=True
)

if result.returncode == 0 and result.stdout.strip():
    parts = result.stdout.strip().split('|')
    if len(parts) >= 3:
        print(f"\nARIN Provider Coverage:")
        print(f"- Sites with WAN1 ARIN data: {parts[0]}")
        print(f"- Sites with WAN2 ARIN data: {parts[1]}")
        print(f"- Sites with any ARIN data: {parts[2]}")