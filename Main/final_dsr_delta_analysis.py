#!/usr/bin/env python3
"""Final analysis of the exact DSR badge delta"""

import subprocess

print("=== FINAL DSR BADGE DELTA ANALYSIS ===\n")

# The facts we know:
# 1. CSV has 1,869 enabled circuits
# 2. Test page shows 1,689 DSR badges
# 3. Delta = 180 circuits

# Based on code analysis, DSR badge counts circuits where:
# - status = 'Enabled'
# - data_source = 'csv_import' (from DSR CSV)
# - Site has Meraki device with Discount-Tire tag
# - Site is not hub/lab/voice/test
# - Provider matches between circuit and Meraki WAN interface

# Query to find the exact breakdown
breakdown_query = """
-- Comprehensive breakdown of why circuits don't get DSR badge
WITH csv_enabled AS (
    SELECT * FROM circuits 
    WHERE status = 'Enabled' 
    AND data_source = 'csv_import'
),
circuit_analysis AS (
    SELECT 
        c.id,
        c.site_name,
        c.provider_name,
        c.circuit_purpose,
        mi.network_name as meraki_name,
        mi.device_tags,
        ec.network_name as enriched_name,
        CASE 
            -- Primary exclusion reasons
            WHEN mi.network_name IS NULL THEN '1. No Meraki device'
            WHEN ec.network_name IS NULL THEN '2. Not in enriched_circuits'
            WHEN NOT (mi.device_tags @> ARRAY['Discount-Tire']::text[]) THEN '3. No Discount-Tire tag'
            WHEN mi.network_name ILIKE '%hub%' THEN '4. Hub site'
            WHEN mi.network_name ILIKE '%lab%' THEN '5. Lab site'
            WHEN mi.network_name ILIKE '%test%' THEN '6. Test site'
            WHEN mi.network_name ILIKE '%voice%' THEN '7. Voice site'
            ELSE '8. Would be counted'
        END as status
    FROM csv_enabled c
    LEFT JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
    LEFT JOIN enriched_circuits ec ON LOWER(c.site_name) = LOWER(ec.network_name)
)
SELECT 
    status,
    COUNT(*) as circuit_count,
    COUNT(DISTINCT site_name) as site_count
FROM circuit_analysis
GROUP BY status
ORDER BY status;
"""

print("1. Primary Exclusion Reasons:")
print("-" * 70)
print(f"{'Reason':<35} {'Circuits':<15} {'Sites':<15}")
print("-" * 70)

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', breakdown_query],
    capture_output=True, text=True
)

total_excluded = 0
would_be_counted = 0

if result.returncode == 0:
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('|')
            if len(parts) >= 3:
                reason = parts[0]
                circuits = int(parts[1])
                sites = int(parts[2])
                print(f"{reason:<35} {circuits:<15} {sites:<15}")
                
                if '8. Would be counted' in reason:
                    would_be_counted = circuits
                else:
                    total_excluded += circuits

print("-" * 70)
print(f"{'Total excluded:':<35} {total_excluded:<15}")
print(f"{'Would be counted:':<35} {would_be_counted:<15}")

# Now check the "would be counted" circuits to see how many actually match
match_check_query = """
-- For circuits that pass all filters, check provider matching
WITH eligible_circuits AS (
    SELECT 
        c.id,
        c.site_name,
        c.provider_name as circuit_provider,
        ec.wan1_provider,
        ec.wan2_provider
    FROM circuits c
    JOIN enriched_circuits ec ON LOWER(c.site_name) = LOWER(ec.network_name)
    JOIN meraki_inventory mi ON ec.network_name = mi.network_name
    WHERE c.status = 'Enabled'
    AND c.data_source = 'csv_import'
    AND mi.device_tags @> ARRAY['Discount-Tire']::text[]
    AND NOT (
        ec.network_name ILIKE '%hub%' OR
        ec.network_name ILIKE '%lab%' OR
        ec.network_name ILIKE '%voice%' OR
        ec.network_name ILIKE '%test%'
    )
)
SELECT 
    COUNT(*) as total_eligible,
    COUNT(CASE 
        WHEN circuit_provider IS NOT NULL AND 
             (LOWER(circuit_provider) = LOWER(wan1_provider) OR 
              LOWER(circuit_provider) = LOWER(wan2_provider) OR
              LOWER(circuit_provider) LIKE '%' || LOWER(SPLIT_PART(wan1_provider, ' ', 1)) || '%' OR
              LOWER(circuit_provider) LIKE '%' || LOWER(SPLIT_PART(wan2_provider, ' ', 1)) || '%')
        THEN 1 
    END) as matched_provider,
    COUNT(CASE 
        WHEN circuit_provider IS NULL OR 
             (circuit_provider IS NOT NULL AND 
              NOT (LOWER(circuit_provider) = LOWER(wan1_provider) OR 
                   LOWER(circuit_provider) = LOWER(wan2_provider) OR
                   LOWER(circuit_provider) LIKE '%' || LOWER(SPLIT_PART(wan1_provider, ' ', 1)) || '%' OR
                   LOWER(circuit_provider) LIKE '%' || LOWER(SPLIT_PART(wan2_provider, ' ', 1)) || '%'))
        THEN 1 
    END) as unmatched_provider
FROM eligible_circuits;
"""

print(f"\n2. Provider Matching Analysis (for {would_be_counted} eligible circuits):")

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', match_check_query],
    capture_output=True, text=True
)

if result.returncode == 0 and result.stdout.strip():
    parts = result.stdout.strip().split('|')
    if len(parts) >= 3:
        total_eligible = int(parts[0])
        matched = int(parts[1])
        unmatched = int(parts[2])
        
        print(f"   - Total eligible circuits: {total_eligible}")
        print(f"   - Provider matched (DSR badge): {matched}")
        print(f"   - Provider not matched: {unmatched}")

# Final summary with specific examples
examples_query = """
-- Get examples of excluded circuits
SELECT 
    c.site_name,
    c.provider_name,
    c.circuit_purpose,
    CASE 
        WHEN mi.network_name IS NULL THEN 'No Meraki device'
        WHEN NOT (mi.device_tags @> ARRAY['Discount-Tire']::text[]) THEN 'No Discount-Tire tag'
        WHEN mi.network_name ILIKE '%lab%' THEN 'Lab site'
        WHEN ec.network_name IS NULL THEN 'Not in enriched_circuits'
        ELSE 'Other'
    END as reason
FROM circuits c
LEFT JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
LEFT JOIN enriched_circuits ec ON LOWER(c.site_name) = LOWER(ec.network_name)
WHERE c.status = 'Enabled' 
AND c.data_source = 'csv_import'
AND (
    mi.network_name IS NULL OR
    NOT (mi.device_tags @> ARRAY['Discount-Tire']::text[]) OR
    mi.network_name ILIKE '%lab%' OR
    ec.network_name IS NULL
)
ORDER BY reason, c.site_name
LIMIT 10;
"""

print(f"\n3. Example Excluded Circuits:")
print("-" * 90)
print(f"{'Site':<25} {'Provider':<25} {'Purpose':<15} {'Reason':<25}")
print("-" * 90)

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', examples_query],
    capture_output=True, text=True
)

if result.returncode == 0:
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('|')
            if len(parts) >= 4:
                site = parts[0][:25]
                provider = parts[1][:25] if parts[1] else '-'
                purpose = parts[2][:15] if parts[2] else '-'
                reason = parts[3][:25]
                print(f"{site:<25} {provider:<25} {purpose:<15} {reason:<25}")

print(f"\n=== FINAL SUMMARY ===")
print(f"CSV enabled circuits: 1,869")
print(f"Test page DSR badges: 1,689")
print(f"Delta: 180 circuits")
print(f"\nThe 180 missing circuits break down as:")
print(f"1. No Meraki device in inventory")
print(f"2. Missing Discount-Tire tag")
print(f"3. Lab/Hub/Test/Voice sites (excluded by design)")
print(f"4. Not in enriched_circuits table")
print(f"5. Provider mismatch between circuit and Meraki WAN")