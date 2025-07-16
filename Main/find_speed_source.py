#!/usr/bin/env python3
"""
Find where the "20.0 M" format is coming from
"""
import psycopg2
import re

# Read config
with open('/usr/local/bin/Main/config.py', 'r') as f:
    config_content = f.read()
    
uri_match = re.search(r"SQLALCHEMY_DATABASE_URI = ['\"]postgresql://([^:]+):([^@]+)@([^/]+)/([^'\"]+)['\"]", config_content)
if uri_match:
    user, password, host, database = uri_match.groups()

try:
    conn = psycopg2.connect(
        host=host.split(':')[0],
        port=5432,
        database=database,
        user=user,
        password=password
    )
    cursor = conn.cursor()
    
    # Let's check COD 28 which has the issue
    site = 'COD 28'
    
    print(f"Investigating {site}...")
    print("="*60)
    
    # Check enriched circuits with all fields
    cursor.execute("""
        SELECT *
        FROM enriched_circuits
        WHERE network_name = %s
    """, (site,))
    
    columns = [desc[0] for desc in cursor.description]
    row = cursor.fetchone()
    
    if row:
        print("\nEnriched Circuits Record:")
        for i, col in enumerate(columns):
            if col in ['wan1_speed', 'wan2_speed', 'wan1_provider', 'wan2_provider']:
                print(f"  {col}: '{row[i]}'")
    
    # Check if there's a pattern - sites where WAN2 has no DSR match
    print("\n" + "="*60)
    print("\nChecking pattern: Sites with '\\d+\\.\\d+ M' format...")
    
    cursor.execute("""
        SELECT ec.network_name, ec.wan1_speed, ec.wan2_speed,
               ec.wan1_provider, ec.wan2_provider,
               c1.provider_name as dsr_primary_provider,
               c1.details_ordered_service_speed as dsr_primary_speed,
               c2.provider_name as dsr_secondary_provider,
               c2.details_ordered_service_speed as dsr_secondary_speed
        FROM enriched_circuits ec
        LEFT JOIN circuits c1 ON ec.network_name = c1.site_name 
            AND c1.circuit_purpose = 'Primary' AND c1.status = 'Enabled'
        LEFT JOIN circuits c2 ON ec.network_name = c2.site_name 
            AND c2.circuit_purpose = 'Secondary' AND c2.status = 'Enabled'
        WHERE ec.wan1_speed ~ '^\\d+\\.\\d+ M$' OR ec.wan2_speed ~ '^\\d+\\.\\d+ M$'
        LIMIT 10
    """)
    
    results = cursor.fetchall()
    print(f"\nFound {len(results)} sites with the pattern:")
    
    for row in results:
        print(f"\n{row[0]}:")
        print(f"  Enriched WAN1: '{row[1]}' / {row[3]}")
        print(f"  Enriched WAN2: '{row[2]}' / {row[4]}")
        print(f"  DSR Primary: {row[5]} - '{row[6]}'" if row[5] else "  DSR Primary: None")
        print(f"  DSR Secondary: {row[7]} - '{row[8]}'" if row[7] else "  DSR Secondary: None")
        
        # Check if WAN2 has no DSR match
        if row[2] and ' M' in row[2] and not row[7]:
            print("  >>> WAN2 has space-M format and NO DSR Secondary match!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()