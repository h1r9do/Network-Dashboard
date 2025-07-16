#!/usr/bin/env python3
"""Find the EXACT delta between CSV and DSR badge count - FIXED VERSION"""

import csv
import subprocess
from collections import defaultdict

print("=== EXACT DSR BADGE DELTA ANALYSIS ===\n")

# Step 1: Count enabled circuits in CSV
csv_enabled_count = 0
csv_sites = defaultdict(list)

with open('/var/www/html/circuitinfo/tracking_data_2025-07-11.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['status'] == 'Enabled':
            csv_enabled_count += 1
            site = row['Site Name'].strip()
            csv_sites[site].append({
                'purpose': row.get('circuit_purpose', ''),
                'provider': row.get('provider_name', '')
            })

print(f"1. CSV File Analysis:")
print(f"   - Total enabled circuits: {csv_enabled_count}")
print(f"   - Unique sites: {len(csv_sites)}")

# Step 2: Understand what DSR badge counts
# Based on the code, DSR badge counts circuits where dsr_verified = True
# This happens when circuit.data_source = 'csv_import' AND it matches a Meraki WAN interface

# First, let's see how many circuits would be counted by the test page
test_page_query = """
-- Count circuits that would get DSR badge on test page
WITH eligible_sites AS (
    -- Sites shown on test page (with Discount-Tire tag, no IPs, not hub/lab/test)
    SELECT DISTINCT 
        ec.network_name,
        ec.wan1_provider,
        ec.wan2_provider
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
),
dsr_verified_circuits AS (
    -- Circuits that would be dsr_verified (matched to a WAN interface)
    SELECT 
        c.id,
        c.site_name,
        c.provider_name,
        c.circuit_purpose,
        es.network_name,
        CASE 
            WHEN c.provider_name IS NOT NULL AND es.wan1_provider IS NOT NULL 
                 AND LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(es.wan1_provider, ' ', 1)) || '%' THEN 'WAN1'
            WHEN c.provider_name IS NOT NULL AND es.wan2_provider IS NOT NULL 
                 AND LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(es.wan2_provider, ' ', 1)) || '%' THEN 'WAN2'
            WHEN LOWER(c.provider_name) = LOWER(es.wan1_provider) THEN 'WAN1'
            WHEN LOWER(c.provider_name) = LOWER(es.wan2_provider) THEN 'WAN2'
            ELSE NULL
        END as matched_wan
    FROM circuits c
    JOIN eligible_sites es ON LOWER(c.site_name) = LOWER(es.network_name)
    WHERE c.status = 'Enabled'
    AND c.data_source = 'csv_import'
)
SELECT 
    COUNT(CASE WHEN matched_wan IS NOT NULL THEN 1 END) as dsr_badge_count,
    COUNT(*) as total_eligible_circuits,
    COUNT(DISTINCT site_name) as unique_sites
FROM dsr_verified_circuits;
"""

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', test_page_query],
    capture_output=True, text=True
)

if result.returncode == 0 and result.stdout.strip():
    parts = result.stdout.strip().split('|')
    if len(parts) >= 3:
        calculated_dsr_count = int(parts[0])
        total_eligible = int(parts[1])
        eligible_sites = int(parts[2])
        print(f"\n2. Test Page DSR Badge Analysis:")
        print(f"   - Calculated DSR badge count: {calculated_dsr_count}")
        print(f"   - Total eligible circuits: {total_eligible}")
        print(f"   - Eligible sites: {eligible_sites}")
else:
    print(f"Query error: {result.stderr}")
    calculated_dsr_count = 0

# Use the known value from the page
actual_dsr_badge = 1689
print(f"\n3. Actual vs Expected:")
print(f"   - Test page shows: {actual_dsr_badge} (DSR badge)")
print(f"   - CSV has: {csv_enabled_count} enabled circuits")
print(f"   - DELTA: {csv_enabled_count - actual_dsr_badge} circuits")

# Step 4: Find WHY circuits are excluded
exclusion_query = """
-- Find why circuits are not counted in DSR badge
WITH all_csv_enabled AS (
    SELECT * FROM circuits 
    WHERE status = 'Enabled' 
    AND data_source = 'csv_import'
),
exclusion_reasons AS (
    SELECT 
        c.id,
        c.site_name,
        c.provider_name,
        c.circuit_purpose,
        CASE 
            WHEN mi.network_name IS NULL THEN 'No Meraki device'
            WHEN NOT (mi.device_tags @> ARRAY['Discount-Tire']::text[]) THEN 'No Discount-Tire tag'
            WHEN mi.network_name ILIKE '%hub%' THEN 'Hub site'
            WHEN mi.network_name ILIKE '%lab%' THEN 'Lab site'
            WHEN mi.network_name ILIKE '%test%' THEN 'Test site'
            WHEN mi.network_name ILIKE '%voice%' THEN 'Voice site'
            WHEN (mi.wan1_ip IS NOT NULL AND mi.wan1_ip != '' AND mi.wan1_ip != 'None') 
              OR (mi.wan2_ip IS NOT NULL AND mi.wan2_ip != '' AND mi.wan2_ip != 'None') THEN 'Site has IP addresses'
            WHEN ec.network_name IS NULL THEN 'Not in enriched_circuits'
            ELSE 'Would be eligible'
        END as exclusion_reason
    FROM all_csv_enabled c
    LEFT JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
    LEFT JOIN enriched_circuits ec ON LOWER(c.site_name) = LOWER(ec.network_name)
)
SELECT 
    exclusion_reason,
    COUNT(*) as circuit_count,
    COUNT(DISTINCT site_name) as site_count,
    STRING_AGG(DISTINCT site_name, ', ' ORDER BY site_name) FILTER (WHERE exclusion_reason != 'Would be eligible') as example_sites
FROM exclusion_reasons
GROUP BY exclusion_reason
ORDER BY circuit_count DESC
LIMIT 10;
"""

print(f"\n4. Exclusion Reasons Breakdown:")
print("-" * 80)
print(f"{'Reason':<30} {'Circuits':<12} {'Sites':<10} {'Examples':<30}")
print("-" * 80)

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', exclusion_query],
    capture_output=True, text=True
)

total_excluded = 0
if result.returncode == 0:
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('|')
            if len(parts) >= 3:
                reason = parts[0]
                circuits = int(parts[1])
                sites = int(parts[2])
                examples = parts[3][:30] if len(parts) > 3 and parts[3] else ''
                total_excluded += circuits if reason != 'Would be eligible' else 0
                print(f"{reason:<30} {circuits:<12} {sites:<10} {examples:<30}")

print("-" * 80)
print(f"{'TOTAL EXCLUDED:':<30} {total_excluded:<12}")

# Step 5: For "Would be eligible" circuits, check why they don't get DSR badge
eligible_check_query = """
-- For eligible sites, why don't circuits get DSR badge?
WITH eligible_sites AS (
    SELECT DISTINCT 
        ec.network_name,
        ec.wan1_provider,
        ec.wan2_provider
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
),
circuit_matching AS (
    SELECT 
        c.site_name,
        c.provider_name as circuit_provider,
        es.wan1_provider,
        es.wan2_provider,
        CASE 
            WHEN c.provider_name IS NULL THEN 'Circuit has no provider'
            WHEN es.wan1_provider IS NULL AND es.wan2_provider IS NULL THEN 'Meraki has no providers'
            WHEN LOWER(c.provider_name) = LOWER(es.wan1_provider) 
              OR LOWER(c.provider_name) = LOWER(es.wan2_provider) THEN 'Provider matches'
            WHEN c.provider_name IS NOT NULL AND es.wan1_provider IS NOT NULL 
                 AND LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(es.wan1_provider, ' ', 1)) || '%' THEN 'Partial match WAN1'
            WHEN c.provider_name IS NOT NULL AND es.wan2_provider IS NOT NULL 
                 AND LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(es.wan2_provider, ' ', 1)) || '%' THEN 'Partial match WAN2'
            ELSE 'Provider mismatch'
        END as match_status
    FROM circuits c
    JOIN eligible_sites es ON LOWER(c.site_name) = LOWER(es.network_name)
    WHERE c.status = 'Enabled'
    AND c.data_source = 'csv_import'
)
SELECT 
    match_status,
    COUNT(*) as count
FROM circuit_matching
GROUP BY match_status
ORDER BY count DESC;
"""

print(f"\n5. Provider Matching Analysis (for eligible sites):")
print("-" * 60)

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', eligible_check_query],
    capture_output=True, text=True
)

if result.returncode == 0:
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('|')
            if len(parts) >= 2:
                status = parts[0]
                count = parts[1]
                print(f"{status:<40} {count}")

print(f"\n=== SUMMARY ===")
print(f"The delta of {csv_enabled_count - actual_dsr_badge} circuits is caused by:")
print(f"1. Sites without Meraki devices")
print(f"2. Sites without Discount-Tire tag") 
print(f"3. Hub/Lab/Test/Voice sites (excluded by design)")
print(f"4. Sites that already have IP addresses")
print(f"5. Circuits where provider doesn't match Meraki WAN provider")