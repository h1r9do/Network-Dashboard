#!/usr/bin/env python3
"""
Fix AZP 23 data to show correct DSR information
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

print("=== Fixing AZP 23 Data ===")

# Get DSR data from circuits table
cursor.execute("""
    SELECT circuit_purpose, provider_name, details_ordered_service_speed, 
           billing_monthly_cost, status
    FROM circuits
    WHERE site_name = 'AZP 23'
    AND status = 'Enabled'
    ORDER BY 
        CASE LOWER(circuit_purpose)
            WHEN 'primary' THEN 1
            WHEN 'secondary' THEN 2
            ELSE 3
        END
""")

dsr_circuits = cursor.fetchall()
print("\nDSR Enabled Circuits:")
for row in dsr_circuits:
    print(f"  {row[0]}: {row[1]} - {row[2]} (${row[3]}) - {row[4]}")

# Update enriched_circuits with correct DSR data
if dsr_circuits:
    # First circuit should be Primary (Cox Business)
    primary = dsr_circuits[0]
    
    cursor.execute("""
        UPDATE enriched_circuits
        SET wan1_provider = %s,
            wan1_speed = %s,
            wan1_monthly_cost = %s,
            wan1_circuit_role = 'Primary',
            last_updated = CURRENT_TIMESTAMP
        WHERE network_name = 'AZP 23'
    """, (primary[1], primary[2], f"${primary[3]}" if primary[3] else "$0.00"))
    
    print(f"\nUpdated WAN1 with DSR data: {primary[1]} - {primary[2]}")

# Keep WAN2 as is (Digi Cell) since there's no secondary enabled circuit
conn.commit()

# Verify the update
cursor.execute("""
    SELECT wan1_provider, wan1_speed, wan1_monthly_cost,
           wan2_provider, wan2_speed, wan2_monthly_cost
    FROM enriched_circuits
    WHERE network_name = 'AZP 23'
""")
result = cursor.fetchone()
if result:
    print("\nUpdated enriched_circuits data:")
    print(f"  WAN1: {result[0]} - {result[1]} ({result[2]})")
    print(f"  WAN2: {result[3]} - {result[4]} ({result[5]})")

cursor.close()
conn.close()

print("\n✓ AZP 23 data fixed!")