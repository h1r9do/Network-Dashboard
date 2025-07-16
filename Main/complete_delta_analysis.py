#!/usr/bin/env python3
"""Complete delta analysis - CSV vs Test Page DSR badges"""

import csv
import subprocess
from datetime import datetime

print("=== COMPLETE DELTA ANALYSIS ===\n")

# Read CSV file to get true count
csv_enabled_count = 0
csv_sites = set()
with open('/var/www/html/circuitinfo/tracking_data_2025-07-11.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['status'] == 'Enabled':
            csv_enabled_count += 1
            csv_sites.add(row['Site Name'].strip())

print(f"1. CSV File:")
print(f"   - Enabled circuits: {csv_enabled_count}")
print(f"   - Unique sites: {len(csv_sites)}")

# Get ALL circuits in database and their badge status
analysis_query = """
WITH csv_circuits AS (
    SELECT * FROM circuits 
    WHERE status = 'Enabled' 
    AND data_source = 'csv_import'
),
badge_analysis AS (
    SELECT 
        c.id,
        c.site_name,
        c.site_id,
        c.circuit_purpose,
        c.provider_name,
        c.details_service_speed,
        c.billing_monthly_cost,
        mi.network_name as meraki_network,
        mi.device_tags,
        ec.wan1_provider,
        ec.wan2_provider,
        mi.wan1_ip,
        mi.wan2_ip,
        mi.wan1_arin_provider,
        mi.wan2_arin_provider,
        -- Would get DSR badge?
        CASE 
            WHEN mi.device_tags @> ARRAY['Discount-Tire']::text[]
             AND NOT (mi.network_name ILIKE '%hub%' OR mi.network_name ILIKE '%lab%' OR 
                      mi.network_name ILIKE '%test%' OR mi.network_name ILIKE '%voice%')
             AND ec.network_name IS NOT NULL
             AND (LOWER(c.provider_name) = LOWER(ec.wan1_provider) OR 
                  LOWER(c.provider_name) = LOWER(ec.wan2_provider) OR
                  (c.provider_name IS NOT NULL AND ec.wan1_provider IS NOT NULL AND 
                   LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan1_provider, ' ', 1)) || '%') OR
                  (c.provider_name IS NOT NULL AND ec.wan2_provider IS NOT NULL AND 
                   LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan2_provider, ' ', 1)) || '%'))
            THEN 'Yes'
            ELSE 'No'
        END as gets_dsr_badge,
        -- Why excluded?
        CASE 
            WHEN mi.network_name IS NULL THEN 'No Meraki device'
            WHEN NOT (mi.device_tags @> ARRAY['Discount-Tire']::text[]) THEN 'No Discount-Tire tag'
            WHEN mi.network_name ILIKE '%lab%' THEN 'Lab site'
            WHEN mi.network_name ILIKE '%hub%' THEN 'Hub site'
            WHEN mi.network_name ILIKE '%test%' THEN 'Test site'
            WHEN mi.network_name ILIKE '%voice%' THEN 'Voice site'
            WHEN ec.network_name IS NULL THEN 'Not in enriched_circuits'
            WHEN NOT (LOWER(c.provider_name) = LOWER(ec.wan1_provider) OR 
                      LOWER(c.provider_name) = LOWER(ec.wan2_provider) OR
                      (c.provider_name IS NOT NULL AND ec.wan1_provider IS NOT NULL AND 
                       LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan1_provider, ' ', 1)) || '%') OR
                      (c.provider_name IS NOT NULL AND ec.wan2_provider IS NOT NULL AND 
                       LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan2_provider, ' ', 1)) || '%'))
            THEN 'Provider mismatch'
            ELSE 'Should get badge'
        END as exclusion_reason,
        -- ARIN could help?
        CASE 
            WHEN (mi.wan1_arin_provider IS NOT NULL AND c.provider_name IS NOT NULL AND 
                  LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(mi.wan1_arin_provider, ' ', 1)) || '%') OR
                 (mi.wan2_arin_provider IS NOT NULL AND c.provider_name IS NOT NULL AND 
                  LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(mi.wan2_arin_provider, ' ', 1)) || '%')
            THEN 'Yes'
            ELSE 'No'
        END as arin_could_help
    FROM csv_circuits c
    LEFT JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
    LEFT JOIN enriched_circuits ec ON LOWER(c.site_name) = LOWER(ec.network_name)
)
SELECT * FROM badge_analysis
ORDER BY gets_dsr_badge, exclusion_reason, site_name;
"""

print("\n2. Database Analysis:")
result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '\t', '-c', analysis_query],
    capture_output=True, text=True
)

if result.returncode != 0:
    print(f"Query error: {result.stderr}")
    exit(1)

# Parse results
all_circuits = []
badge_yes = 0
badge_no = 0
exclusion_counts = {}
arin_help_by_reason = {}

for line in result.stdout.strip().split('\n'):
    if line:
        parts = line.split('\t')
        if len(parts) >= 18:
            circuit = {
                'id': parts[0],
                'site_name': parts[1],
                'site_id': parts[2],
                'circuit_purpose': parts[3],
                'provider_name': parts[4],
                'speed': parts[5],
                'cost': parts[6],
                'meraki_network': parts[7],
                'device_tags': parts[8],
                'wan1_provider': parts[9],
                'wan2_provider': parts[10],
                'wan1_ip': parts[11],
                'wan2_ip': parts[12],
                'wan1_arin': parts[13],
                'wan2_arin': parts[14],
                'gets_badge': parts[15],
                'exclusion_reason': parts[16],
                'arin_could_help': parts[17]
            }
            all_circuits.append(circuit)
            
            if circuit['gets_badge'] == 'Yes':
                badge_yes += 1
            else:
                badge_no += 1
                reason = circuit['exclusion_reason']
                exclusion_counts[reason] = exclusion_counts.get(reason, 0) + 1
                
                if circuit['arin_could_help'] == 'Yes':
                    if reason not in arin_help_by_reason:
                        arin_help_by_reason[reason] = 0
                    arin_help_by_reason[reason] += 1

print(f"   - Total CSV import circuits: {len(all_circuits)}")
print(f"   - Would get DSR badge: {badge_yes}")
print(f"   - Would NOT get DSR badge: {badge_no}")

# Also check circuits NOT in CSV
non_csv_query = """
SELECT COUNT(*) FROM circuits 
WHERE status = 'Enabled' 
AND (data_source != 'csv_import' OR data_source IS NULL);
"""
result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-c', non_csv_query],
    capture_output=True, text=True
)
non_csv_count = int(result.stdout.strip()) if result.returncode == 0 else 0

print(f"\n3. Delta Breakdown:")
print(f"   CSV has {csv_enabled_count} enabled circuits")
print(f"   Test page shows 1,689 DSR badges")
print(f"   Delta: {csv_enabled_count - 1689} circuits\n")

print(f"   Database has:")
print(f"   - {len(all_circuits)} circuits from CSV import")
print(f"   - {non_csv_count} circuits from other sources")
print(f"   - {badge_yes} would get DSR badges")
print(f"   - {badge_no} excluded")

print(f"\n4. Exclusion Reasons for {badge_no} circuits:")
for reason, count in sorted(exclusion_counts.items(), key=lambda x: x[1], reverse=True):
    arin_help = arin_help_by_reason.get(reason, 0)
    print(f"   - {reason}: {count} circuits" + (f" (ARIN could help with {arin_help})" if arin_help > 0 else ""))

# Write detailed output
output_file = f'/usr/local/bin/Main/complete_delta_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
excluded_file = f'/usr/local/bin/Main/excluded_circuits_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

# Write all circuits
fieldnames = ['site_name', 'site_id', 'circuit_purpose', 'provider_name', 'speed', 'cost',
              'gets_badge', 'exclusion_reason', 'wan1_provider', 'wan2_provider',
              'wan1_arin', 'wan2_arin', 'arin_could_help']

with open(output_file, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for circuit in all_circuits:
        writer.writerow({k: circuit.get(k, '') for k in fieldnames})

# Write only excluded circuits
with open(excluded_file, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for circuit in all_circuits:
        if circuit['gets_badge'] == 'No':
            writer.writerow({k: circuit.get(k, '') for k in fieldnames})

print(f"\n5. Files Created:")
print(f"   - All circuits: {output_file}")
print(f"   - Excluded only: {excluded_file}")

# Check for circuits in CSV but not in database
print(f"\n6. Data Integrity Check:")
db_sites = {c['site_name'] for c in all_circuits}
missing_from_db = csv_sites - db_sites
if missing_from_db:
    print(f"   WARNING: {len(missing_from_db)} sites in CSV but not in database!")
    print(f"   Examples: {list(missing_from_db)[:5]}")
else:
    print(f"   ✓ All CSV sites found in database")

print(f"\n7. Summary:")
print(f"   The delta of {csv_enabled_count - 1689} circuits consists of:")
print(f"   - {badge_no} circuits excluded by test page logic")
print(f"   - {csv_enabled_count - len(all_circuits)} circuits in CSV but not in database")
print(f"   - Potential mismatch in counting logic")