#!/usr/bin/env python3
"""Calculate the impact of ARIN-based alignment on DSR badge count"""

import subprocess

print("=== ARIN Alignment Impact on DSR Badge Count ===\n")

# Query to calculate DSR badge count with ARIN-based alignment
query = """
WITH arin_aligned_circuits AS (
    SELECT 
        c.site_name,
        c.circuit_purpose,
        c.provider_name as dsr_provider,
        ec.wan1_provider,
        ec.wan2_provider,
        mi.wan1_arin_provider,
        mi.wan2_arin_provider,
        -- Current Meraki-based matching
        CASE 
            WHEN LOWER(c.provider_name) = LOWER(ec.wan1_provider) OR
                 (c.provider_name IS NOT NULL AND ec.wan1_provider IS NOT NULL AND 
                  LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan1_provider, ' ', 1)) || '%')
            THEN 'WAN1'
            WHEN LOWER(c.provider_name) = LOWER(ec.wan2_provider) OR
                 (c.provider_name IS NOT NULL AND ec.wan2_provider IS NOT NULL AND 
                  LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan2_provider, ' ', 1)) || '%')
            THEN 'WAN2'
            ELSE 'No Match'
        END as meraki_match,
        -- ARIN-based matching
        CASE 
            -- Normalize and match ARIN providers
            WHEN mi.wan1_arin_provider IS NOT NULL AND c.provider_name IS NOT NULL AND (
                -- AT&T variations
                (LOWER(c.provider_name) LIKE '%at&t%' AND LOWER(mi.wan1_arin_provider) LIKE '%at&t%') OR
                (LOWER(c.provider_name) LIKE '%at&t%' AND LOWER(mi.wan1_arin_provider) = 'att') OR
                -- Spectrum/Charter
                (LOWER(c.provider_name) LIKE '%spectrum%' AND LOWER(mi.wan1_arin_provider) LIKE '%charter%') OR
                (LOWER(c.provider_name) LIKE '%charter%' AND LOWER(mi.wan1_arin_provider) LIKE '%charter%') OR
                -- Cox
                (LOWER(c.provider_name) LIKE '%cox%' AND LOWER(mi.wan1_arin_provider) LIKE '%cox%') OR
                -- Comcast
                (LOWER(c.provider_name) LIKE '%comcast%' AND LOWER(mi.wan1_arin_provider) LIKE '%comcast%') OR
                -- CenturyLink
                (LOWER(c.provider_name) LIKE '%centurylink%' AND LOWER(mi.wan1_arin_provider) LIKE '%centurylink%') OR
                (LOWER(c.provider_name) LIKE '%qwest%' AND LOWER(mi.wan1_arin_provider) LIKE '%centurylink%') OR
                -- Frontier
                (LOWER(c.provider_name) LIKE '%frontier%' AND LOWER(mi.wan1_arin_provider) LIKE '%frontier%') OR
                -- Verizon
                (LOWER(c.provider_name) LIKE '%verizon%' AND LOWER(mi.wan1_arin_provider) LIKE '%verizon%') OR
                (LOWER(c.provider_name) LIKE '%vzw%' AND LOWER(mi.wan1_arin_provider) LIKE '%verizon%')
            ) THEN 'WAN1'
            WHEN mi.wan2_arin_provider IS NOT NULL AND c.provider_name IS NOT NULL AND (
                -- Same logic for WAN2
                (LOWER(c.provider_name) LIKE '%at&t%' AND LOWER(mi.wan2_arin_provider) LIKE '%at&t%') OR
                (LOWER(c.provider_name) LIKE '%at&t%' AND LOWER(mi.wan2_arin_provider) = 'att') OR
                (LOWER(c.provider_name) LIKE '%spectrum%' AND LOWER(mi.wan2_arin_provider) LIKE '%charter%') OR
                (LOWER(c.provider_name) LIKE '%charter%' AND LOWER(mi.wan2_arin_provider) LIKE '%charter%') OR
                (LOWER(c.provider_name) LIKE '%cox%' AND LOWER(mi.wan2_arin_provider) LIKE '%cox%') OR
                (LOWER(c.provider_name) LIKE '%comcast%' AND LOWER(mi.wan2_arin_provider) LIKE '%comcast%') OR
                (LOWER(c.provider_name) LIKE '%centurylink%' AND LOWER(mi.wan2_arin_provider) LIKE '%centurylink%') OR
                (LOWER(c.provider_name) LIKE '%qwest%' AND LOWER(mi.wan2_arin_provider) LIKE '%centurylink%') OR
                (LOWER(c.provider_name) LIKE '%frontier%' AND LOWER(mi.wan2_arin_provider) LIKE '%frontier%') OR
                (LOWER(c.provider_name) LIKE '%verizon%' AND LOWER(mi.wan2_arin_provider) LIKE '%verizon%') OR
                (LOWER(c.provider_name) LIKE '%vzw%' AND LOWER(mi.wan2_arin_provider) LIKE '%verizon%')
            ) THEN 'WAN2'
            ELSE 'No ARIN Match'
        END as arin_match
    FROM circuits c
    JOIN enriched_circuits ec ON LOWER(c.site_name) = LOWER(ec.network_name)
    JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
    WHERE c.status = 'Enabled'
    AND c.data_source = 'csv_import'
    AND mi.device_tags @> ARRAY['Discount-Tire']::text[]
    AND NOT (
        mi.network_name ILIKE '%hub%' OR
        mi.network_name ILIKE '%lab%' OR
        mi.network_name ILIKE '%test%' OR
        mi.network_name ILIKE '%voice%'
    )
)
SELECT 
    COUNT(*) as total_eligible_circuits,
    COUNT(CASE WHEN meraki_match != 'No Match' THEN 1 END) as current_dsr_badges,
    COUNT(CASE WHEN arin_match != 'No ARIN Match' THEN 1 END) as arin_based_matches,
    COUNT(CASE WHEN meraki_match = 'No Match' AND arin_match != 'No ARIN Match' THEN 1 END) as additional_arin_matches,
    COUNT(CASE WHEN meraki_match != 'No Match' OR arin_match != 'No ARIN Match' THEN 1 END) as combined_matches
FROM arin_aligned_circuits;
"""

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', query],
    capture_output=True, text=True
)

if result.returncode == 0 and result.stdout.strip():
    parts = result.stdout.strip().split('|')
    if len(parts) >= 5:
        total = int(parts[0])
        current_badges = int(parts[1])
        arin_matches = int(parts[2])
        additional = int(parts[3])
        combined = int(parts[4])
        
        print("DSR Badge Count Analysis:")
        print(f"- Total eligible circuits: {total}")
        print(f"\nCurrent system (Meraki provider matching):")
        print(f"  - DSR badges: {current_badges}")
        print(f"  - No match: {total - current_badges}")
        print(f"\nUsing ARIN provider data:")
        print(f"  - ARIN-based matches: {arin_matches}")
        print(f"  - Additional matches from ARIN: {additional}")
        print(f"\nCombined approach (Meraki OR ARIN):")
        print(f"  - Total DSR badges: {combined}")
        print(f"  - Improvement: +{combined - current_badges} badges ({((combined - current_badges) / current_badges * 100):.1f}% increase)")
        
        print(f"\nCSV vs System comparison:")
        print(f"- CSV enabled circuits: 1,869")
        print(f"- Test page currently shows: 1,689")
        print(f"- With ARIN alignment: {combined} (closer to CSV count)")
        print(f"- Remaining gap: {1869 - combined} circuits")

# Get examples of circuits that would benefit from ARIN alignment
examples_query = """
SELECT 
    c.site_name,
    c.circuit_purpose,
    c.provider_name as dsr_provider,
    ec.wan1_provider as meraki_wan1,
    mi.wan1_arin_provider as arin_wan1,
    ec.wan2_provider as meraki_wan2,
    mi.wan2_arin_provider as arin_wan2
FROM circuits c
JOIN enriched_circuits ec ON LOWER(c.site_name) = LOWER(ec.network_name)
JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
WHERE c.status = 'Enabled'
AND c.data_source = 'csv_import'
AND mi.device_tags @> ARRAY['Discount-Tire']::text[]
AND NOT (
    mi.network_name ILIKE '%hub%' OR
    mi.network_name ILIKE '%lab%' OR
    mi.network_name ILIKE '%test%' OR
    mi.network_name ILIKE '%voice%'
)
-- No current Meraki match
AND NOT (
    LOWER(c.provider_name) = LOWER(ec.wan1_provider) OR
    LOWER(c.provider_name) = LOWER(ec.wan2_provider) OR
    (c.provider_name IS NOT NULL AND ec.wan1_provider IS NOT NULL AND 
     LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan1_provider, ' ', 1)) || '%') OR
    (c.provider_name IS NOT NULL AND ec.wan2_provider IS NOT NULL AND 
     LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan2_provider, ' ', 1)) || '%')
)
-- But ARIN would match
AND (
    (mi.wan1_arin_provider IS NOT NULL AND c.provider_name IS NOT NULL AND 
     LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(mi.wan1_arin_provider, ' ', 1)) || '%') OR
    (mi.wan2_arin_provider IS NOT NULL AND c.provider_name IS NOT NULL AND 
     LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(mi.wan2_arin_provider, ' ', 1)) || '%')
)
LIMIT 10;
"""

print("\n=== Examples of circuits that would benefit from ARIN alignment ===")
result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', examples_query],
    capture_output=True, text=True
)

if result.returncode == 0:
    i = 1
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('|')
            if len(parts) >= 7:
                print(f"\n{i}. {parts[0]} - {parts[1]}")
                print(f"   DSR Provider: {parts[2]}")
                print(f"   Meraki WAN1: {parts[3]} | ARIN WAN1: {parts[4]}")
                print(f"   Meraki WAN2: {parts[5]} | ARIN WAN2: {parts[6]}")
                i += 1