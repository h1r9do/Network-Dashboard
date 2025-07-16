#!/usr/bin/env python3
"""Find possible matches for unmatched sites in the database"""

import subprocess
import csv
from datetime import datetime

# List of sites to search for
unmatched_sites = [
    "CAL000", "CALW01", "CAN00", "CAS00", "COD00", "GAACALLCTR", 
    "ILC00", "ILR01", "ILX 01", "INIW00", "KONFARA", "KSK00N",
    "KYN 00", "MIA00", "MIHW00", "MNM 09 -B", "MNMW01", "MOS XX",
    "NCC00", "NCC W00", "NMA00", "NMA Call Center", "NNM 09", "NVL000",
    "NVLW 01", "OKO00", "TNN00", "TXD00", "TXH00", "TXH Training",
    "TXHW00", "TXS000", "UTSW01", "UTSW02", "VAF 01", "WAS00",
    "WDGA01_01", "WDIL01", "WDTD01"
]

print("=== SEARCHING FOR SITE MATCHES ===\n")

# Create comprehensive search query
search_query = """
WITH search_sites AS (
    SELECT UNNEST(ARRAY[{sites}]::text[]) as search_site
),
potential_matches AS (
    SELECT DISTINCT
        ss.search_site as original_site,
        mi.network_name as meraki_name,
        mi.device_tags,
        CASE 
            -- Exact match
            WHEN mi.network_name = ss.search_site THEN 1
            -- Case insensitive
            WHEN LOWER(mi.network_name) = LOWER(ss.search_site) THEN 2
            -- Space to underscore
            WHEN mi.network_name = REPLACE(ss.search_site, ' ', '_') THEN 3
            -- Remove spaces
            WHEN REPLACE(mi.network_name, ' ', '') = REPLACE(ss.search_site, ' ', '') THEN 4
            -- Remove underscores
            WHEN REPLACE(mi.network_name, '_', '') = REPLACE(ss.search_site, '_', '') THEN 5
            -- Prefix match (first 3-4 chars)
            WHEN LEFT(mi.network_name, 3) = LEFT(ss.search_site, 3) THEN 6
            -- W variations (W00 vs 00)
            WHEN REPLACE(mi.network_name, 'W', '') = REPLACE(ss.search_site, 'W', '') THEN 7
            -- 000 vs 00 variations
            WHEN REPLACE(mi.network_name, '000', '00') = REPLACE(ss.search_site, '000', '00') THEN 8
            -- Special characters removed
            WHEN REGEXP_REPLACE(LOWER(mi.network_name), '[^a-z0-9]', '', 'g') = 
                 REGEXP_REPLACE(LOWER(ss.search_site), '[^a-z0-9]', '', 'g') THEN 9
            -- Fuzzy match on core parts
            WHEN LENGTH(mi.network_name) >= 3 AND LENGTH(ss.search_site) >= 3 AND
                 SUBSTRING(LOWER(mi.network_name), 1, 3) = SUBSTRING(LOWER(ss.search_site), 1, 3) AND
                 (mi.network_name LIKE '%00%' AND ss.search_site LIKE '%00%') THEN 10
            ELSE 99
        END as match_score,
        CASE 
            WHEN mi.network_name = ss.search_site THEN 'Exact match'
            WHEN LOWER(mi.network_name) = LOWER(ss.search_site) THEN 'Case difference'
            WHEN mi.network_name = REPLACE(ss.search_site, ' ', '_') THEN 'Space→Underscore'
            WHEN REPLACE(mi.network_name, ' ', '') = REPLACE(ss.search_site, ' ', '') THEN 'Spaces removed'
            WHEN REPLACE(mi.network_name, '_', '') = REPLACE(ss.search_site, '_', '') THEN 'Underscores removed'
            WHEN LEFT(mi.network_name, 3) = LEFT(ss.search_site, 3) THEN 'Prefix match'
            WHEN REPLACE(mi.network_name, 'W', '') = REPLACE(ss.search_site, 'W', '') THEN 'W variation'
            WHEN REPLACE(mi.network_name, '000', '00') = REPLACE(ss.search_site, '000', '00') THEN '000→00 variation'
            WHEN REGEXP_REPLACE(LOWER(mi.network_name), '[^a-z0-9]', '', 'g') = 
                 REGEXP_REPLACE(LOWER(ss.search_site), '[^a-z0-9]', '', 'g') THEN 'Special chars removed'
            WHEN LENGTH(mi.network_name) >= 3 AND LENGTH(ss.search_site) >= 3 AND
                 SUBSTRING(LOWER(mi.network_name), 1, 3) = SUBSTRING(LOWER(ss.search_site), 1, 3) AND
                 (mi.network_name LIKE '%00%' AND ss.search_site LIKE '%00%') THEN 'Fuzzy prefix+00'
            ELSE 'No clear match'
        END as match_type
    FROM search_sites ss
    CROSS JOIN meraki_inventory mi
    WHERE match_score < 99
)
SELECT * FROM potential_matches
ORDER BY original_site, match_score, meraki_name;
"""

# Format sites for SQL
site_list = "'" + "','".join([s.replace("'", "''") for s in unmatched_sites]) + "'"
formatted_query = search_query.format(sites=site_list)

print("Searching for matches...")
result = subprocess.run(
    ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '\t', '-c', formatted_query],
    capture_output=True, text=True
)

matches = []
if result.returncode == 0:
    for line in result.stdout.strip().split('\n'):
        if line:
            parts = line.split('\t')
            if len(parts) >= 5:
                matches.append({
                    'original_site': parts[0],
                    'meraki_name': parts[1],
                    'device_tags': parts[2],
                    'match_score': int(parts[3]),
                    'match_type': parts[4]
                })

print(f"Found {len(matches)} potential matches\n")

# Group by original site
matches_by_site = {}
for match in matches:
    site = match['original_site']
    if site not in matches_by_site:
        matches_by_site[site] = []
    matches_by_site[site].append(match)

# Display results
found_count = 0
no_match_sites = []

for site in unmatched_sites:
    if site in matches_by_site:
        found_count += 1
        site_matches = sorted(matches_by_site[site], key=lambda x: x['match_score'])
        print(f"\n'{site}' - Found {len(site_matches)} potential match(es):")
        for i, match in enumerate(site_matches[:3]):  # Show top 3
            has_dt = 'Yes' if 'Discount-Tire' in str(match['device_tags']) else 'No'
            print(f"  {i+1}. '{match['meraki_name']}' ({match['match_type']}, DT tag: {has_dt})")
    else:
        no_match_sites.append(site)

# Also try more aggressive pattern matching for no-match sites
if no_match_sites:
    print(f"\n\n=== AGGRESSIVE SEARCH FOR {len(no_match_sites)} UNMATCHED SITES ===")
    
    for site in no_match_sites[:10]:  # First 10
        # Extract prefix and numbers
        prefix = ''.join([c for c in site[:3] if c.isalpha()])
        
        pattern_query = f"""
        SELECT network_name, device_tags @> ARRAY['Discount-Tire']::text[] as has_dt
        FROM meraki_inventory
        WHERE network_name ILIKE '{prefix}%'
        AND (network_name LIKE '%00%' OR network_name LIKE '%01%' OR network_name LIKE '%W%')
        LIMIT 5;
        """
        
        result = subprocess.run(
            ['sudo', '-u', 'postgres', 'psql', '-d', 'dsrcircuits', '-t', '-A', '-F', '|', '-c', pattern_query],
            capture_output=True, text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            print(f"\n'{site}' - Pattern search results:")
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        has_dt = 'Yes' if parts[1] == 't' else 'No'
                        print(f"  → '{parts[0]}' (DT tag: {has_dt})")
        else:
            print(f"\n'{site}' - No matches even with pattern search")

# Write results to CSV
output_file = f'/usr/local/bin/Main/site_match_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
with open(output_file, 'w', newline='') as f:
    fieldnames = ['original_site', 'meraki_name', 'match_type', 'match_score', 'has_dt_tag']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    
    for match in matches:
        writer.writerow({
            'original_site': match['original_site'],
            'meraki_name': match['meraki_name'],
            'match_type': match['match_type'],
            'match_score': match['match_score'],
            'has_dt_tag': 'Yes' if 'Discount-Tire' in str(match['device_tags']) else 'No'
        })

print(f"\n\n=== SUMMARY ===")
print(f"Sites searched: {len(unmatched_sites)}")
print(f"Sites with potential matches: {found_count}")
print(f"Sites with no matches: {len(no_match_sites)}")
print(f"Results saved to: {output_file}")

# List all unmatched sites
if no_match_sites:
    print(f"\nSites with NO matches found:")
    for site in sorted(no_match_sites):
        print(f"  - {site}")