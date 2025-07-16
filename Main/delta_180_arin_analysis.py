#!/usr/bin/env python3
"""Focused analysis of ONLY the 180-circuit delta with ARIN alignment"""

import csv
import subprocess
from datetime import datetime
from collections import defaultdict

print("=== FOCUSED DELTA ANALYSIS: 180 Circuits Missing from Test Page ===\n")

# First, get the exact circuits that are in CSV but NOT getting DSR badges
delta_query = """
-- Find the exact circuits that make up the 180 delta
WITH csv_enabled AS (
    -- All enabled circuits from CSV import
    SELECT * FROM circuits 
    WHERE status = 'Enabled' 
    AND data_source = 'csv_import'
),
circuits_with_dsr_badge AS (
    -- Circuits that currently get DSR badge on test page
    SELECT c.id, c.site_name, c.circuit_purpose
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
    AND (
        LOWER(c.provider_name) = LOWER(ec.wan1_provider) OR
        LOWER(c.provider_name) = LOWER(ec.wan2_provider) OR
        (c.provider_name IS NOT NULL AND ec.wan1_provider IS NOT NULL AND 
         LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan1_provider, ' ', 1)) || '%') OR
        (c.provider_name IS NOT NULL AND ec.wan2_provider IS NOT NULL AND 
         LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan2_provider, ' ', 1)) || '%')
    )
),
delta_circuits AS (
    -- The delta: CSV circuits that DON'T get badges
    SELECT 
        c.*,
        mi.network_name as meraki_network,
        mi.device_tags,
        ec.wan1_provider,
        ec.wan2_provider,
        mi.wan1_ip,
        mi.wan2_ip,
        mi.wan1_arin_provider,
        mi.wan2_arin_provider,
        CASE 
            WHEN mi.network_name IS NULL THEN '1. No Meraki device'
            WHEN NOT (mi.device_tags @> ARRAY['Discount-Tire']::text[]) THEN '2. No Discount-Tire tag'
            WHEN mi.network_name ILIKE '%lab%' THEN '3. Lab site'
            WHEN mi.network_name ILIKE '%hub%' THEN '4. Hub site'
            WHEN mi.network_name ILIKE '%test%' THEN '5. Test site'
            WHEN mi.network_name ILIKE '%voice%' THEN '6. Voice site'
            WHEN ec.network_name IS NULL THEN '7. Not in enriched_circuits'
            ELSE '8. Provider mismatch'
        END as exclusion_reason
    FROM csv_enabled c
    LEFT JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
    LEFT JOIN enriched_circuits ec ON LOWER(c.site_name) = LOWER(ec.network_name)
    WHERE c.id NOT IN (SELECT id FROM circuits_with_dsr_badge)
)
SELECT 
    site_name,
    site_id,
    circuit_purpose,
    provider_name,
    details_service_speed,
    billing_monthly_cost,
    wan1_provider,
    wan2_provider,
    wan1_arin_provider,
    wan2_arin_provider,
    exclusion_reason,
    -- Check if ARIN could help match
    CASE 
        WHEN wan1_arin_provider IS NOT NULL AND provider_name IS NOT NULL AND (
            (LOWER(provider_name) LIKE '%at&t%' AND LOWER(wan1_arin_provider) LIKE '%at&t%') OR
            (LOWER(provider_name) LIKE '%spectrum%' AND LOWER(wan1_arin_provider) LIKE '%charter%') OR
            (LOWER(provider_name) LIKE '%cox%' AND LOWER(wan1_arin_provider) LIKE '%cox%') OR
            (LOWER(provider_name) LIKE '%comcast%' AND LOWER(wan1_arin_provider) LIKE '%comcast%') OR
            (LOWER(provider_name) LIKE '%centurylink%' AND LOWER(wan1_arin_provider) LIKE '%centurylink%') OR
            (LOWER(provider_name) LIKE '%frontier%' AND LOWER(wan1_arin_provider) LIKE '%frontier%')
        ) THEN 'Yes - WAN1'
        WHEN wan2_arin_provider IS NOT NULL AND provider_name IS NOT NULL AND (
            (LOWER(provider_name) LIKE '%at&t%' AND LOWER(wan2_arin_provider) LIKE '%at&t%') OR
            (LOWER(provider_name) LIKE '%spectrum%' AND LOWER(wan2_arin_provider) LIKE '%charter%') OR
            (LOWER(provider_name) LIKE '%cox%' AND LOWER(wan2_arin_provider) LIKE '%cox%') OR
            (LOWER(provider_name) LIKE '%comcast%' AND LOWER(wan2_arin_provider) LIKE '%comcast%') OR
            (LOWER(provider_name) LIKE '%centurylink%' AND LOWER(wan2_arin_provider) LIKE '%centurylink%') OR
            (LOWER(provider_name) LIKE '%frontier%' AND LOWER(wan2_arin_provider) LIKE '%frontier%')
        ) THEN 'Yes - WAN2'
        ELSE 'No'
    END as arin_could_match
FROM delta_circuits
ORDER BY exclusion_reason, site_name;
"""

print("Querying for delta circuits...")
result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '\t', '-c', delta_query],
    capture_output=True, text=True
)

if result.returncode != 0:
    print(f"Query error: {result.stderr}")
    exit(1)

# Parse results
delta_circuits = []
exclusion_counts = defaultdict(int)
arin_could_help = 0

fieldnames = [
    'site_name', 'site_id', 'circuit_purpose', 'provider_name', 
    'speed', 'monthly_cost', 'wan1_provider', 'wan2_provider',
    'wan1_arin_provider', 'wan2_arin_provider', 'exclusion_reason',
    'arin_could_match'
]

for line in result.stdout.strip().split('\n'):
    if line:
        parts = line.split('\t')
        if len(parts) >= 12:
            circuit = dict(zip(fieldnames, parts))
            delta_circuits.append(circuit)
            exclusion_counts[circuit['exclusion_reason']] += 1
            if circuit['arin_could_match'].startswith('Yes'):
                arin_could_help += 1

# Write delta circuits to CSV
output_file = f'/usr/local/bin/Main/delta_180_circuits_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
with open(output_file, 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(delta_circuits)

print(f"\nDelta Analysis Complete!")
print(f"Total delta circuits: {len(delta_circuits)}")
print(f"Output file: {output_file}")

print(f"\nExclusion Reason Breakdown:")
for reason, count in sorted(exclusion_counts.items()):
    print(f"  {reason}: {count} circuits")

print(f"\nARIN Alignment Potential:")
print(f"  Circuits where ARIN could help match: {arin_could_help}")
print(f"  Would reduce delta from {len(delta_circuits)} to {len(delta_circuits) - arin_could_help}")

# Get count to verify
verify_query = """
SELECT 
    (SELECT COUNT(*) FROM circuits WHERE status = 'Enabled' AND data_source = 'csv_import') as csv_total,
    (SELECT COUNT(*) FROM (
        SELECT c.id FROM circuits c
        JOIN enriched_circuits ec ON LOWER(c.site_name) = LOWER(ec.network_name)
        JOIN meraki_inventory mi ON LOWER(c.site_name) = LOWER(mi.network_name)
        WHERE c.status = 'Enabled' AND c.data_source = 'csv_import'
        AND mi.device_tags @> ARRAY['Discount-Tire']::text[]
        AND NOT (mi.network_name ILIKE '%hub%' OR mi.network_name ILIKE '%lab%' OR 
                 mi.network_name ILIKE '%test%' OR mi.network_name ILIKE '%voice%')
        AND (LOWER(c.provider_name) = LOWER(ec.wan1_provider) OR 
             LOWER(c.provider_name) = LOWER(ec.wan2_provider) OR
             (c.provider_name IS NOT NULL AND ec.wan1_provider IS NOT NULL AND 
              LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan1_provider, ' ', 1)) || '%') OR
             (c.provider_name IS NOT NULL AND ec.wan2_provider IS NOT NULL AND 
              LOWER(c.provider_name) LIKE '%' || LOWER(SPLIT_PART(ec.wan2_provider, ' ', 1)) || '%'))
    ) as dsr_badges) as would_get_badge;
"""

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', verify_query],
    capture_output=True, text=True
)

if result.returncode == 0:
    parts = result.stdout.strip().split('|')
    if len(parts) >= 2:
        csv_total = int(parts[0])
        badge_count = int(parts[1])
        print(f"\nVerification:")
        print(f"  CSV total: {csv_total}")
        print(f"  Would get badge: {badge_count}")
        print(f"  Delta: {csv_total - badge_count}")

# Show examples of each exclusion type
print(f"\n=== Example Circuits by Exclusion Reason ===")
for reason in sorted(exclusion_counts.keys()):
    print(f"\n{reason}:")
    examples = [c for c in delta_circuits if c['exclusion_reason'] == reason][:3]
    for ex in examples:
        print(f"  - {ex['site_name']} ({ex['circuit_purpose']}): {ex['provider_name']}")
        if ex['arin_could_match'].startswith('Yes'):
            print(f"    → ARIN could match via {ex['arin_could_match'].split(' - ')[1]}")