#!/usr/bin/env python3
"""Find the EXACT delta between CSV and DSR badge count"""

import csv
import subprocess
from collections import defaultdict

print("=== EXACT DSR DELTA ANALYSIS ===\n")

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

# Step 2: Count what the DSR badge shows (circuits that can be matched to Meraki)
# The DSR badge counts circuits where:
# - Circuit is enabled
# - Circuit has data_source = 'csv_import' 
# - Circuit can be matched to a Meraki device with Discount-Tire tag
# - Site is not hub/lab/test/voice
# - Site has no IPs on WAN interfaces

dsr_badge_query = """
WITH meraki_sites AS (
    SELECT DISTINCT 
        mi.network_name,
        mi.wan1_provider,
        mi.wan2_provider
    FROM meraki_inventory mi
    JOIN enriched_circuits ec ON mi.network_name = ec.network_name
    WHERE mi.device_tags @> ARRAY['Discount-Tire']::text[]
    AND NOT (
        mi.network_name ILIKE '%hub%' OR
        mi.network_name ILIKE '%lab%' OR
        mi.network_name ILIKE '%voice%' OR
        mi.network_name ILIKE '%test%'
    )
    AND (mi.wan1_ip IS NULL OR mi.wan1_ip = '' OR mi.wan1_ip = 'None')
    AND (mi.wan2_ip IS NULL OR mi.wan2_ip = '' OR mi.wan2_ip = 'None')
),
matched_circuits AS (
    SELECT 
        c.id,
        c.site_name,
        c.provider_name,
        c.circuit_purpose,
        ms.network_name,
        CASE 
            -- Match logic similar to assign_costs_improved
            WHEN LOWER(c.provider_name) = LOWER(ms.wan1_provider) THEN 'WAN1'
            WHEN LOWER(c.provider_name) = LOWER(ms.wan2_provider) THEN 'WAN2'
            WHEN c.provider_name IS NOT NULL AND ms.wan1_provider IS NOT NULL 
                 AND LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ms.wan1_provider, ' ', 1)) || '%' THEN 'WAN1'
            WHEN c.provider_name IS NOT NULL AND ms.wan2_provider IS NOT NULL 
                 AND LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ms.wan2_provider, ' ', 1)) || '%' THEN 'WAN2'
            ELSE NULL
        END as matched_to
    FROM circuits c
    JOIN meraki_sites ms ON LOWER(c.site_name) = LOWER(ms.network_name)
    WHERE c.status = 'Enabled'
    AND c.data_source = 'csv_import'
)
SELECT 
    COUNT(*) as dsr_badge_count,
    COUNT(DISTINCT site_name) as unique_sites
FROM matched_circuits
WHERE matched_to IS NOT NULL;
"""

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', dsr_badge_query],
    capture_output=True, text=True
)

if result.returncode == 0 and result.stdout.strip():
    parts = result.stdout.strip().split('|')
    dsr_badge_count = int(parts[0])
    dsr_unique_sites = int(parts[1])
    print(f"\n2. DSR Badge Count (from database):")
    print(f"   - DSR verified circuits: {dsr_badge_count}")
    print(f"   - Unique sites: {dsr_unique_sites}")
else:
    print(f"Error running query: {result.stderr}")
    dsr_badge_count = 1689  # Use the known value

print(f"\n3. Delta Analysis:")
print(f"   - CSV enabled circuits: {csv_enabled_count}")
print(f"   - DSR badge shows: {dsr_badge_count}")
print(f"   - DELTA: {csv_enabled_count - dsr_badge_count} circuits")

# Step 3: Find the specific circuits that make up the delta
delta_query = """
-- Find enabled circuits from CSV that are NOT counted in DSR badge
WITH csv_circuits AS (
    SELECT * FROM circuits 
    WHERE status = 'Enabled' 
    AND data_source = 'csv_import'
),
meraki_sites AS (
    SELECT DISTINCT 
        mi.network_name,
        mi.wan1_provider,
        mi.wan2_provider,
        mi.device_tags
    FROM meraki_inventory mi
    WHERE (mi.wan1_ip IS NULL OR mi.wan1_ip = '' OR mi.wan1_ip = 'None')
    AND (mi.wan2_ip IS NULL OR mi.wan2_ip = '' OR mi.wan2_ip = 'None')
),
matched_circuits AS (
    SELECT 
        c.id,
        c.site_name,
        c.provider_name,
        ms.network_name as meraki_network,
        CASE 
            WHEN ms.network_name IS NULL THEN 'No Meraki device'
            WHEN NOT (ms.device_tags @> ARRAY['Discount-Tire']::text[]) THEN 'No Discount-Tire tag'
            WHEN ms.network_name ILIKE '%hub%' THEN 'Hub site'
            WHEN ms.network_name ILIKE '%lab%' THEN 'Lab site'
            WHEN ms.network_name ILIKE '%test%' THEN 'Test site'
            WHEN ms.network_name ILIKE '%voice%' THEN 'Voice site'
            WHEN LOWER(c.provider_name) = LOWER(ms.wan1_provider) 
              OR LOWER(c.provider_name) = LOWER(ms.wan2_provider) THEN 'Matched'
            ELSE 'Provider mismatch'
        END as status
    FROM csv_circuits c
    LEFT JOIN meraki_sites ms ON LOWER(c.site_name) = LOWER(ms.network_name)
)
SELECT 
    status as exclusion_reason,
    COUNT(*) as circuit_count,
    COUNT(DISTINCT site_name) as site_count
FROM matched_circuits
WHERE status != 'Matched'
GROUP BY status
ORDER BY circuit_count DESC;
"""

print(f"\n4. Breakdown of Excluded Circuits:")
print("-" * 60)
print(f"{'Reason':<30} {'Circuits':<15} {'Sites':<15}")
print("-" * 60)

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', delta_query],
    capture_output=True, text=True
)

if result.returncode == 0:
    total_excluded = 0
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('|')
            if len(parts) >= 3:
                reason = parts[0]
                circuits = int(parts[1])
                sites = int(parts[2])
                total_excluded += circuits
                print(f"{reason:<30} {circuits:<15} {sites:<15}")
    
    print("-" * 60)
    print(f"{'TOTAL EXCLUDED':<30} {total_excluded:<15}")

# Step 4: Get specific examples of excluded circuits
example_query = """
WITH csv_circuits AS (
    SELECT * FROM circuits 
    WHERE status = 'Enabled' 
    AND data_source = 'csv_import'
),
examples AS (
    SELECT 
        c.site_name,
        c.provider_name,
        c.circuit_purpose,
        mi.network_name,
        mi.device_tags,
        CASE 
            WHEN mi.network_name IS NULL THEN 'No Meraki device'
            WHEN NOT (mi.device_tags @> ARRAY['Discount-Tire']::text[]) THEN 'No Discount-Tire tag'
            WHEN mi.network_name ILIKE '%hub%' THEN 'Hub site'
            WHEN mi.network_name ILIKE '%lab%' THEN 'Lab site'
            ELSE 'Other'
        END as reason
    FROM csv_circuits c
    LEFT JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
    WHERE NOT EXISTS (
        -- Exclude circuits that would be counted in DSR badge
        SELECT 1 FROM meraki_inventory mi2
        WHERE LOWER(c.site_name) = LOWER(mi2.network_name)
        AND mi2.device_tags @> ARRAY['Discount-Tire']::text[]
        AND NOT (mi2.network_name ILIKE '%hub%' OR mi2.network_name ILIKE '%lab%')
        AND (mi2.wan1_ip IS NULL OR mi2.wan1_ip = '' OR mi2.wan1_ip = 'None')
        AND (mi2.wan2_ip IS NULL OR mi2.wan2_ip = '' OR mi2.wan2_ip = 'None')
    )
)
SELECT * FROM examples
ORDER BY reason, site_name
LIMIT 20;
"""

print(f"\n5. Example Excluded Circuits:")
print("-" * 100)
print(f"{'Site':<25} {'Provider':<20} {'Purpose':<15} {'Reason':<30}")
print("-" * 100)

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', example_query],
    capture_output=True, text=True
)

if result.returncode == 0:
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('|')
            if len(parts) >= 6:
                site = parts[0][:25]
                provider = parts[1][:20] if parts[1] else '-'
                purpose = parts[2][:15] if parts[2] else '-'
                reason = parts[5][:30]
                print(f"{site:<25} {provider:<20} {purpose:<15} {reason:<30}")