#!/usr/bin/env python3
"""
Simple test to check filter data
"""

import psycopg2

print("=== TESTING FILTER DATA ===\n")

conn = psycopg2.connect('host=localhost dbname=dsrcircuits user=dsruser password=dsrpass123')
cur = conn.cursor()

# Get sample data
cur.execute("""
    SELECT ec.network_name, ec.wan1_provider, ec.wan2_provider
    FROM enriched_circuits ec
    JOIN meraki_inventory mi ON ec.network_name = mi.network_name
    WHERE ec.network_name NOT LIKE '%hub%'
    AND (mi.wan1_ip IS NOT NULL OR mi.wan2_ip IS NOT NULL)
    ORDER BY ec.network_name
    LIMIT 10
""")

print("Sample enriched circuits data:")
for row in cur.fetchall():
    print(f"{row[0]}: WAN1='{row[1]}', WAN2='{row[2]}'")

# Get unique providers
cur.execute("""
    SELECT DISTINCT wan1_provider 
    FROM enriched_circuits 
    WHERE wan1_provider IS NOT NULL 
    AND wan1_provider != '' 
    AND wan1_provider != 'N/A'
    ORDER BY wan1_provider
""")

print("\nAll unique WAN1 providers:")
providers = cur.fetchall()
for i, (p,) in enumerate(providers):
    if 'starlink' in p.lower():
        print(f"  {i+1}. '{p}' <-- STARLINK FOUND")
    else:
        print(f"  {i+1}. '{p}'")

# Check HTML generation
print("\nChecking what HTML would be generated for a Starlink circuit:")
cur.execute("""
    SELECT network_name, wan1_provider, wan2_provider
    FROM enriched_circuits
    WHERE wan1_provider ILIKE '%starlink%' OR wan2_provider ILIKE '%starlink%'
    LIMIT 3
""")

for row in cur.fetchall():
    print(f"\nSite: {row[0]}")
    if row[1] and 'starlink' in row[1].lower():
        print(f"  WAN1 Provider cell would show: '{row[1]}' with STARLINK badge")
    if row[2] and 'starlink' in row[2].lower():
        print(f"  WAN2 Provider cell would show: '{row[2]}' with STARLINK badge")

conn.close()