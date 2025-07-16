#!/usr/bin/env python3
"""
Fix the remaining 3 sites with Cell overwriting DSR data
"""
import psycopg2
import re
from datetime import datetime
from config import Config

# Get database connection
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
user, password, host, port, database = match.groups()

conn = psycopg2.connect(
    host=host,
    port=int(port),
    database=database,
    user=user,
    password=password
)
cursor = conn.cursor()

print("=== Fixing remaining sites with Cell overwriting DSR data ===")

# Sites that need fixing (excluding AZP 23 which we already fixed)
sites_to_fix = ['AZP 62', 'GAN 01', 'INC 03', 'TXD 55']

for site in sites_to_fix:
    print(f"\n--- Processing {site} ---")
    
    # Get DSR data from circuits table
    cursor.execute("""
        SELECT circuit_purpose, provider_name, details_ordered_service_speed, 
               billing_monthly_cost, status
        FROM circuits
        WHERE site_name = %s
        AND status = 'Enabled'
        ORDER BY 
            CASE LOWER(circuit_purpose)
                WHEN 'primary' THEN 1
                WHEN 'secondary' THEN 2
                ELSE 3
            END
    """, (site,))
    
    dsr_circuits = cursor.fetchall()
    print(f"DSR Enabled Circuits for {site}:")
    for row in dsr_circuits:
        print(f"  {row[0]}: {row[1]} - {row[2]} (${row[3]}) - {row[4]}")
    
    # Update enriched_circuits with correct DSR data
    if dsr_circuits:
        # First circuit should be Primary
        primary = dsr_circuits[0]
        
        cursor.execute("""
            UPDATE enriched_circuits
            SET wan1_provider = %s,
                wan1_speed = %s,
                wan1_monthly_cost = %s,
                wan1_circuit_role = 'Primary',
                last_updated = CURRENT_TIMESTAMP
            WHERE network_name = %s
        """, (primary[1], primary[2], f"${primary[3]}" if primary[3] else "$0.00", site))
        
        print(f"Updated WAN1 with DSR data: {primary[1]} - {primary[2]}")
        
        # If there's a secondary circuit, update WAN2
        if len(dsr_circuits) > 1:
            secondary = dsr_circuits[1]
            cursor.execute("""
                UPDATE enriched_circuits
                SET wan2_provider = %s,
                    wan2_speed = %s,
                    wan2_monthly_cost = %s,
                    wan2_circuit_role = 'Secondary',
                    last_updated = CURRENT_TIMESTAMP
                WHERE network_name = %s
            """, (secondary[1], secondary[2], f"${secondary[3]}" if secondary[3] else "$0.00", site))
            print(f"Updated WAN2 with DSR data: {secondary[1]} - {secondary[2]}")

# Commit all changes
conn.commit()

# Verify the updates
print("\n=== Verification ===")
for site in sites_to_fix:
    cursor.execute("""
        SELECT wan1_provider, wan1_speed, wan1_monthly_cost,
               wan2_provider, wan2_speed, wan2_monthly_cost
        FROM enriched_circuits
        WHERE network_name = %s
    """, (site,))
    result = cursor.fetchone()
    if result:
        print(f"\n{site}:")
        print(f"  WAN1: {result[0]} - {result[1]} ({result[2]})")
        print(f"  WAN2: {result[3]} - {result[4]} ({result[5]})")

cursor.close()
conn.close()

print("\n✓ All remaining sites fixed!")