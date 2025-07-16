#!/usr/bin/env python3
"""
Check how many sites have Cell in enriched_circuits but real provider in DSR
"""
import psycopg2
import re
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

# Find sites where enriched shows Cell but DSR has real data
cursor.execute("""
    WITH dsr_enabled AS (
        SELECT DISTINCT site_name, provider_name, details_ordered_service_speed
        FROM circuits
        WHERE status = 'Enabled'
        AND provider_name NOT LIKE '%Cell%'
        AND provider_name != 'nan'
        AND circuit_purpose = 'Primary'
    )
    SELECT ec.network_name, ec.wan1_provider, ec.wan1_speed,
           de.provider_name as dsr_provider, de.details_ordered_service_speed as dsr_speed
    FROM enriched_circuits ec
    JOIN dsr_enabled de ON ec.network_name = de.site_name
    WHERE ec.wan1_provider IN ('Cell', 'Digi', 'VZW Cell')
    ORDER BY ec.network_name
    LIMIT 20
""")

print('Sites where enriched shows Cell but DSR has real provider data:')
for row in cursor.fetchall():
    print(f'  {row[0]}: Enriched={row[1]}/{row[2]}, DSR={row[3]}/{row[4]}')

# Count total
cursor.execute("""
    WITH dsr_enabled AS (
        SELECT DISTINCT site_name
        FROM circuits
        WHERE status = 'Enabled'
        AND provider_name NOT LIKE '%Cell%'
        AND provider_name != 'nan'
        AND circuit_purpose = 'Primary'
    )
    SELECT COUNT(*)
    FROM enriched_circuits ec
    JOIN dsr_enabled de ON ec.network_name = de.site_name
    WHERE ec.wan1_provider IN ('Cell', 'Digi', 'VZW Cell')
""")
count = cursor.fetchone()[0]
print(f'\nTotal sites with Cell overwriting real DSR data: {count}')

cursor.close()
conn.close()