#!/usr/bin/env python3
"""Final delta analysis with improved site name matching"""

import csv
import subprocess
from datetime import datetime

print("=== FINAL DELTA ANALYSIS WITH NAME MATCHING ===\n")

# Query that handles site name variations
delta_query = """
WITH csv_enabled AS (
    SELECT * FROM circuits 
    WHERE status = 'Enabled' 
    AND data_source = 'csv_import'
),
-- Match circuits to Meraki with name variations
circuit_meraki_match AS (
    SELECT 
        c.*,
        mi.network_name as matched_meraki_name,
        mi.device_tags,
        mi.wan1_ip,
        mi.wan2_ip,
        mi.wan1_arin_provider,
        mi.wan2_arin_provider,
        ec.wan1_provider as ec_wan1_provider,
        ec.wan2_provider as ec_wan2_provider,
        CASE 
            WHEN mi.network_name = c.site_name THEN 'Exact'
            WHEN LOWER(mi.network_name) = LOWER(c.site_name) THEN 'Case-insensitive'
            WHEN mi.network_name = REPLACE(c.site_name, ' ', '_') THEN 'Space to underscore'
            WHEN mi.network_name = REPLACE(c.site_name, ' ', '') THEN 'Space removed'
            ELSE 'No match'
        END as name_match_type
    FROM csv_enabled c
    LEFT JOIN meraki_inventory mi ON (
        mi.network_name = c.site_name OR
        LOWER(mi.network_name) = LOWER(c.site_name) OR
        mi.network_name = REPLACE(c.site_name, ' ', '_') OR
        mi.network_name = REPLACE(c.site_name, ' ', '')
    )
    LEFT JOIN enriched_circuits ec ON (
        ec.network_name = c.site_name OR
        LOWER(ec.network_name) = LOWER(c.site_name) OR
        ec.network_name = REPLACE(c.site_name, ' ', '_') OR
        ec.network_name = REPLACE(c.site_name, ' ', '')
    )
),
-- Determine DSR badge eligibility
badge_analysis AS (
    SELECT 
        site_name,
        site_id,
        circuit_purpose,
        provider_name,
        details_service_speed,
        billing_monthly_cost,
        matched_meraki_name,
        name_match_type,
        device_tags,
        ec_wan1_provider,
        ec_wan2_provider,
        wan1_arin_provider,
        wan2_arin_provider,
        -- Would get DSR badge?
        CASE 
            WHEN matched_meraki_name IS NOT NULL
             AND device_tags @> ARRAY['Discount-Tire']::text[]
             AND NOT (matched_meraki_name ILIKE '%hub%' OR matched_meraki_name ILIKE '%lab%' OR 
                      matched_meraki_name ILIKE '%test%' OR matched_meraki_name ILIKE '%voice%')
             AND ec_wan1_provider IS NOT NULL  -- Has enriched data
             AND (LOWER(provider_name) = LOWER(ec_wan1_provider) OR 
                  LOWER(provider_name) = LOWER(ec_wan2_provider) OR
                  (provider_name IS NOT NULL AND ec_wan1_provider IS NOT NULL AND 
                   LOWER(provider_name) LIKE '%' || LOWER(SPLIT_PART(ec_wan1_provider, ' ', 1)) || '%') OR
                  (provider_name IS NOT NULL AND ec_wan2_provider IS NOT NULL AND 
                   LOWER(provider_name) LIKE '%' || LOWER(SPLIT_PART(ec_wan2_provider, ' ', 1)) || '%'))
            THEN 'Yes'
            ELSE 'No'
        END as gets_dsr_badge,
        -- Why excluded?
        CASE 
            WHEN matched_meraki_name IS NULL THEN '1. No Meraki device'
            WHEN NOT (device_tags @> ARRAY['Discount-Tire']::text[]) THEN '2. No Discount-Tire tag'
            WHEN matched_meraki_name ILIKE '%lab%' THEN '3. Lab site'
            WHEN matched_meraki_name ILIKE '%hub%' THEN '4. Hub site'
            WHEN matched_meraki_name ILIKE '%test%' THEN '5. Test site'
            WHEN matched_meraki_name ILIKE '%voice%' THEN '6. Voice site'
            WHEN ec_wan1_provider IS NULL AND ec_wan2_provider IS NULL THEN '7. Not in enriched_circuits'
            WHEN NOT (LOWER(provider_name) = LOWER(ec_wan1_provider) OR 
                      LOWER(provider_name) = LOWER(ec_wan2_provider) OR
                      (provider_name IS NOT NULL AND ec_wan1_provider IS NOT NULL AND 
                       LOWER(provider_name) LIKE '%' || LOWER(SPLIT_PART(ec_wan1_provider, ' ', 1)) || '%') OR
                      (provider_name IS NOT NULL AND ec_wan2_provider IS NOT NULL AND 
                       LOWER(provider_name) LIKE '%' || LOWER(SPLIT_PART(ec_wan2_provider, ' ', 1)) || '%'))
            THEN '8. Provider mismatch'
            ELSE '9. Should get badge'
        END as exclusion_reason,
        -- ARIN could help?
        CASE 
            WHEN (wan1_arin_provider IS NOT NULL AND provider_name IS NOT NULL AND 
                  LOWER(provider_name) LIKE '%' || LOWER(SPLIT_PART(wan1_arin_provider, ' ', 1)) || '%') OR
                 (wan2_arin_provider IS NOT NULL AND provider_name IS NOT NULL AND 
                  LOWER(provider_name) LIKE '%' || LOWER(SPLIT_PART(wan2_arin_provider, ' ', 1)) || '%')
            THEN 'Yes'
            ELSE 'No'
        END as arin_could_help
    FROM circuit_meraki_match
)
SELECT * FROM badge_analysis
ORDER BY gets_dsr_badge, exclusion_reason, site_name;
"""

print("Running comprehensive analysis with name matching...")
result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '\t', '-c', delta_query],
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
name_match_stats = {}

for line in result.stdout.strip().split('\n'):
    if line:
        parts = line.split('\t')
        if len(parts) >= 16:
            circuit = {
                'site_name': parts[0],
                'site_id': parts[1],
                'circuit_purpose': parts[2],
                'provider_name': parts[3],
                'speed': parts[4],
                'cost': parts[5],
                'matched_meraki_name': parts[6],
                'name_match_type': parts[7],
                'device_tags': parts[8],
                'wan1_provider': parts[9],
                'wan2_provider': parts[10],
                'wan1_arin': parts[11],
                'wan2_arin': parts[12],
                'gets_badge': parts[13],
                'exclusion_reason': parts[14],
                'arin_could_help': parts[15]
            }
            all_circuits.append(circuit)
            
            # Count stats
            if circuit['gets_badge'] == 'Yes':
                badge_yes += 1
            else:
                badge_no += 1
                exclusion_counts[circuit['exclusion_reason']] = exclusion_counts.get(circuit['exclusion_reason'], 0) + 1
            
            # Name matching stats
            match_type = circuit['name_match_type']
            name_match_stats[match_type] = name_match_stats.get(match_type, 0) + 1

# CSV count
csv_count = 0
with open('/var/www/html/circuitinfo/tracking_data_2025-07-11.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['status'] == 'Enabled':
            csv_count += 1

print(f"\n=== RESULTS ===")
print(f"CSV File: {csv_count} enabled circuits")
print(f"Database: {len(all_circuits)} circuits from CSV import")
print(f"Would get DSR badge: {badge_yes}")
print(f"Would NOT get DSR badge: {badge_no}")
print(f"Test page shows: 1,689")
print(f"Delta: {csv_count - 1689}")

print(f"\nName Matching Statistics:")
for match_type, count in sorted(name_match_stats.items()):
    print(f"  {match_type}: {count}")

print(f"\nExclusion Reasons:")
for reason, count in sorted(exclusion_counts.items()):
    print(f"  {reason}: {count}")

# Find specific examples of name mismatches
print(f"\nExamples of sites with name variations:")
examples_shown = 0
for circuit in all_circuits:
    if circuit['name_match_type'] in ['Space to underscore', 'Space removed'] and examples_shown < 10:
        has_tag = 'Yes' if 'Discount-Tire' in str(circuit['device_tags']) else 'No'
        print(f"  CSV: '{circuit['site_name']}' → Meraki: '{circuit['matched_meraki_name']}' (DT tag: {has_tag})")
        examples_shown += 1

# Write detailed CSV
output_file = f'/usr/local/bin/Main/final_delta_with_matching_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
excluded_only = f'/usr/local/bin/Main/excluded_with_matching_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

fieldnames = ['site_name', 'site_id', 'circuit_purpose', 'provider_name', 'speed', 'cost',
              'matched_meraki_name', 'name_match_type', 'gets_badge', 'exclusion_reason',
              'wan1_provider', 'wan2_provider', 'wan1_arin', 'wan2_arin', 'arin_could_help']

# All circuits
with open(output_file, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for circuit in all_circuits:
        writer.writerow({k: circuit.get(k, '') for k in fieldnames})

# Excluded only
with open(excluded_only, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for circuit in all_circuits:
        if circuit['gets_badge'] == 'No':
            writer.writerow({k: circuit.get(k, '') for k in fieldnames})

print(f"\nFiles created:")
print(f"  All circuits: {output_file}")
print(f"  Excluded only: {excluded_only}")

# Check impact of fixing name matching
no_match_but_fixable = [c for c in all_circuits if c['exclusion_reason'] == '1. No Meraki device' and c['site_name'] != c['site_name'].replace(' ', '_')]
print(f"\nPotential improvements:")
print(f"  Sites marked 'No Meraki' that might have underscore version: {len(no_match_but_fixable)}")

# Final summary
print(f"\n=== FINAL SUMMARY ===")
print(f"The 180-circuit delta consists of:")
print(f"1. {exclusion_counts.get('1. No Meraki device', 0)} - No Meraki device (even with name matching)")
print(f"2. {exclusion_counts.get('2. No Discount-Tire tag', 0)} - Missing Discount-Tire tag")
print(f"3. {exclusion_counts.get('3. Lab site', 0)} - Lab sites (excluded by design)")
print(f"4. {exclusion_counts.get('8. Provider mismatch', 0)} - Provider doesn't match")
print(f"5. {csv_count - len(all_circuits)} - In CSV but not in database")
print(f"6. Remaining gap likely due to counting/timing differences")