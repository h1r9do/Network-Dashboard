#!/usr/bin/env python3
"""
Investigate why Frontier Communications sites are failing to match
"""

import psycopg2
import json

# Database configuration
db_config = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

# Connect to database
conn = psycopg2.connect(**db_config)
cur = conn.cursor()

print("=== FRONTIER MATCHING INVESTIGATION ===\n")

# 1. Check DSR circuits for specific CAL sites
print("1. DSR Circuits for CAL sites (focusing on Frontier sites)")
print("-" * 80)
cur.execute("""
    SELECT site_name, provider, status, circuit_id, site_type
    FROM circuits 
    WHERE site_name IN ('CAL 13', 'CAL 17', 'CAL 15', 'CAL 02', 'CAL 19', 'CAL 18', 'CAL 14', 'CAL 01')
    ORDER BY site_name
""")
results = cur.fetchall()
for row in results:
    print(f"{row[0]:<10} | Provider: {row[1]:<30} | Status: {row[2]:<15} | Type: {row[4]}")

# 2. Check all Frontier variations in circuits table
print("\n2. All Frontier provider variations in DSR circuits")
print("-" * 80)
cur.execute("""
    SELECT DISTINCT provider, COUNT(*) as count
    FROM circuits
    WHERE LOWER(provider) LIKE '%frontier%'
    GROUP BY provider
    ORDER BY count DESC
""")
frontier_providers = cur.fetchall()
for row in frontier_providers:
    print(f"'{row[0]}': {row[1]} circuits")

# 3. Check provider_mappings table
print("\n3. Provider mappings for Frontier")
print("-" * 80)
cur.execute("""
    SELECT meraki_name, dsr_name, created_at
    FROM provider_mappings
    WHERE LOWER(meraki_name) LIKE '%frontier%' OR LOWER(dsr_name) LIKE '%frontier%'
    ORDER BY created_at DESC
""")
mappings = cur.fetchall()
if mappings:
    for row in mappings:
        print(f"Meraki: '{row[0]}' → DSR: '{row[1]}' (created: {row[2]})")
else:
    print("No Frontier mappings found in provider_mappings table")

# 4. Check Meraki inventory for Frontier sites
print("\n4. Meraki inventory for sites with Frontier in WAN1")
print("-" * 80)
cur.execute("""
    SELECT site_name, wan1_provider, wan2_provider, last_updated
    FROM meraki_inventory
    WHERE wan1_provider LIKE '%Frontier%' OR wan2_provider LIKE '%Frontier%'
    ORDER BY site_name
    LIMIT 20
""")
meraki_sites = cur.fetchall()
for row in meraki_sites:
    print(f"{row[0]:<10} | WAN1: {row[1]:<25} | WAN2: {row[2]:<25}")

# 5. Check enriched_circuits for these specific sites
print("\n5. Enriched circuits data for CAL sites")
print("-" * 80)
cur.execute("""
    SELECT ec.site_name, ec.dsr_provider, ec.wan1_provider, ec.wan2_provider,
           ec.provider_match_type, ec.provider_match_confidence
    FROM enriched_circuits ec
    WHERE ec.site_name IN ('CAL 13', 'CAL 17', 'CAL 15', 'CAL 02', 'CAL 19', 'CAL 18', 'CAL 14', 'CAL 01')
    ORDER BY ec.site_name
""")
enriched = cur.fetchall()
for row in enriched:
    print(f"{row[0]:<10} | DSR: {row[1]:<20} | WAN1: {row[2]:<20} | Match: {row[4]} ({row[5]}%)")

# 6. Look for exact matches between DSR and Meraki
print("\n6. Checking for exact provider name mismatches")
print("-" * 80)
cur.execute("""
    SELECT DISTINCT c.provider as dsr_provider, mi.wan1_provider as meraki_provider
    FROM circuits c
    JOIN meraki_inventory mi ON c.site_name = mi.site_name
    WHERE (LOWER(c.provider) LIKE '%frontier%' OR LOWER(mi.wan1_provider) LIKE '%frontier%')
    AND c.provider != mi.wan1_provider
    ORDER BY c.provider, mi.wan1_provider
""")
mismatches = cur.fetchall()
for row in mismatches:
    print(f"DSR: '{row[0]}' vs Meraki: '{row[1]}'")

cur.close()
conn.close()