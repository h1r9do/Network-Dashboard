#!/usr/bin/env python3
"""Check for site name variations using pattern matching"""

import subprocess
import csv

print("=== Checking Site Name Variations ===\n")

# Get the sites that appear to have no Meraki device
no_meraki_query = """
-- Get sites marked as "No Meraki device" and look for variations
WITH no_meraki_sites AS (
    SELECT DISTINCT site_name, site_id
    FROM circuits 
    WHERE status = 'Enabled' 
    AND data_source = 'csv_import'
    AND site_name NOT IN (
        SELECT DISTINCT network_name FROM meraki_inventory
    )
),
potential_matches AS (
    SELECT 
        nms.site_name as csv_site,
        nms.site_id as csv_site_id,
        mi.network_name as meraki_site,
        mi.device_tags,
        mi.wan1_ip,
        mi.wan2_ip,
        mi.wan1_provider,
        mi.wan2_provider,
        -- Check different matching patterns
        CASE 
            -- Exact match (shouldn't happen but check)
            WHEN LOWER(nms.site_name) = LOWER(mi.network_name) THEN 'Exact match'
            -- Space vs underscore
            WHEN LOWER(REPLACE(nms.site_name, ' ', '_')) = LOWER(mi.network_name) THEN 'Space→Underscore'
            WHEN LOWER(REPLACE(nms.site_name, ' ', '')) = LOWER(REPLACE(mi.network_name, '_', '')) THEN 'Space/Underscore removed'
            -- Leading zeros
            WHEN LOWER(nms.site_name) LIKE LOWER(SUBSTRING(mi.network_name, 1, 3) || '%00%') THEN 'Leading zeros'
            -- Pattern matching for sites like "AZP 00" matching "AZP_00" or "AZP00"
            WHEN LOWER(REPLACE(REPLACE(nms.site_name, ' ', ''), '0', '')) = 
                 LOWER(REPLACE(REPLACE(mi.network_name, '_', ''), '0', '')) THEN 'Pattern match (no zeros)'
            -- More flexible pattern
            WHEN SUBSTRING(LOWER(nms.site_name), 1, 3) = SUBSTRING(LOWER(mi.network_name), 1, 3)
                 AND nms.site_name LIKE '%00%' AND mi.network_name LIKE '%00%' THEN 'Prefix+00 match'
            ELSE NULL
        END as match_type
    FROM no_meraki_sites nms
    CROSS JOIN meraki_inventory mi
    WHERE 
        -- Look for any potential match
        (
            -- Same prefix (first 3 chars)
            SUBSTRING(LOWER(nms.site_name), 1, 3) = SUBSTRING(LOWER(mi.network_name), 1, 3)
            OR
            -- After removing spaces/underscores
            LOWER(REPLACE(REPLACE(nms.site_name, ' ', ''), '_', '')) = 
            LOWER(REPLACE(REPLACE(mi.network_name, ' ', ''), '_', ''))
            OR
            -- Pattern with wildcards
            LOWER(mi.network_name) LIKE LOWER(REPLACE(REPLACE(nms.site_name, ' ', '%'), '00', '%00%'))
        )
)
SELECT * FROM potential_matches 
WHERE match_type IS NOT NULL
ORDER BY csv_site, match_type;
"""

print("1. Searching for site variations...")
result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '\t', '-c', no_meraki_query],
    capture_output=True, text=True
)

matches_found = []
if result.returncode == 0:
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('\t')
            if len(parts) >= 9:
                matches_found.append({
                    'csv_site': parts[0],
                    'csv_site_id': parts[1],
                    'meraki_site': parts[2],
                    'device_tags': parts[3],
                    'wan1_ip': parts[4],
                    'wan2_ip': parts[5],
                    'wan1_provider': parts[6],
                    'wan2_provider': parts[7],
                    'match_type': parts[8] if len(parts) > 8 else ''
                })

print(f"Found {len(matches_found)} potential matches\n")

# Show examples
if matches_found:
    print("Examples of found matches:")
    for i, match in enumerate(matches_found[:10]):
        print(f"{i+1}. CSV: '{match['csv_site']}' → Meraki: '{match['meraki_site']}' ({match['match_type']})")
        if 'Discount-Tire' in str(match['device_tags']):
            print(f"   ✓ Has Discount-Tire tag")
        else:
            print(f"   ✗ Missing Discount-Tire tag")

# Now check specific examples mentioned
print("\n2. Checking specific sites mentioned:")
specific_sites = ['AZP 00', 'CAL000', 'CALW01', 'CAN00', 'ILC 18', 'INW 01', 'TXH 41']

for site in specific_sites:
    # Try different patterns
    search_patterns = [
        site,
        site.replace(' ', '_'),
        site.replace(' ', ''),
        site.replace('00', '_00'),
        site.replace(' 0', '_0'),
        site[:3] + '%' + site[3:]  # Wildcard in middle
    ]
    
    search_query = f"""
    SELECT network_name, device_tags, wan1_provider, wan2_provider
    FROM meraki_inventory
    WHERE {' OR '.join([f"network_name ILIKE '{pattern}'" for pattern in search_patterns])}
    LIMIT 5;
    """
    
    result = subprocess.run(
        ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', search_query],
        capture_output=True, text=True
    )
    
    if result.returncode == 0 and result.stdout.strip():
        print(f"\n'{site}' - Found in Meraki:")
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 4:
                    print(f"  → '{parts[0]}' (Tags: {parts[1][:50]}...)")
    else:
        print(f"\n'{site}' - NOT FOUND in Meraki inventory")

# Write comprehensive matching analysis
output_file = '/usr/local/bin/Main/site_name_variations_analysis.csv'
fieldnames = ['csv_site', 'csv_site_id', 'meraki_site', 'match_type', 
              'has_dt_tag', 'wan1_ip', 'wan2_ip', 'wan1_provider', 'wan2_provider']

with open(output_file, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for match in matches_found:
        row = {
            'csv_site': match['csv_site'],
            'csv_site_id': match['csv_site_id'],
            'meraki_site': match['meraki_site'],
            'match_type': match['match_type'],
            'has_dt_tag': 'Yes' if 'Discount-Tire' in str(match['device_tags']) else 'No',
            'wan1_ip': match['wan1_ip'],
            'wan2_ip': match['wan2_ip'],
            'wan1_provider': match['wan1_provider'],
            'wan2_provider': match['wan2_provider']
        }
        writer.writerow(row)

print(f"\n3. Analysis saved to: {output_file}")

# Final query to show impact
impact_query = """
SELECT 
    COUNT(DISTINCT c.site_name) as sites_marked_no_meraki,
    COUNT(DISTINCT CASE 
        WHEN EXISTS (
            SELECT 1 FROM meraki_inventory mi 
            WHERE SUBSTRING(LOWER(c.site_name), 1, 3) = SUBSTRING(LOWER(mi.network_name), 1, 3)
            AND (c.site_name LIKE '%00%' AND mi.network_name LIKE '%00%')
        ) THEN c.site_name 
    END) as likely_has_meraki_variant
FROM circuits c
WHERE c.status = 'Enabled' 
AND c.data_source = 'csv_import'
AND c.site_name NOT IN (
    SELECT DISTINCT network_name FROM meraki_inventory
);
"""

result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', impact_query],
    capture_output=True, text=True
)

if result.returncode == 0 and result.stdout.strip():
    parts = result.stdout.strip().split('|')
    if len(parts) >= 2:
        print(f"\n4. Impact Summary:")
        print(f"   - Sites marked as 'No Meraki device': {parts[0]}")
        print(f"   - Likely have Meraki with name variation: {parts[1]}")
        print(f"   - This could recover some of the 64 'No Meraki' circuits")