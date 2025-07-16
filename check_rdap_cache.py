#!/usr/bin/env python3
"""
Check RDAP cache status and identify issues
"""

import psycopg2
import json

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='dsrcircuits',
    user='dsruser',
    password='dsrpass123'
)
cursor = conn.cursor()

print("=== RDAP CACHE ANALYSIS ===\n")

# Check some successful lookups
cursor.execute("""
    SELECT ip_address, provider_name, last_queried
    FROM rdap_cache
    WHERE provider_name <> 'Unknown'
    ORDER BY last_queried DESC
    LIMIT 10
""")
print('Recent successful lookups:')
for row in cursor.fetchall():
    print(f'  {row[0]} -> {row[1]} ({row[2]})')

# Check if Unknown entries are being retried
print('\n\nChecking if Unknown IPs are being retried...')
cursor.execute("""
    SELECT COUNT(DISTINCT ip_address) 
    FROM rdap_cache 
    WHERE provider_name = 'Unknown'
""")
unknown_count = cursor.fetchone()[0]
print(f'Total unique IPs with Unknown provider: {unknown_count}')

# Check a specific unresolved IP
test_ip = '75.148.163.185'
cursor.execute("""
    SELECT ip_address, provider_name, rdap_response IS NOT NULL as has_response, last_queried
    FROM rdap_cache
    WHERE ip_address = %s
""", (test_ip,))
result = cursor.fetchone()
print(f'\nExample unresolved IP ({test_ip}):')
if result:
    print(f'  Provider: {result[1]}')
    print(f'  Has RDAP response: {result[2]}')
    print(f'  Last queried: {result[3]}')
else:
    print('  Not found in cache')

# Check if script is caching failed lookups
cursor.execute("""
    SELECT COUNT(*) 
    FROM rdap_cache 
    WHERE provider_name = 'Unknown' 
    AND rdap_response IS NULL
""")
null_responses = cursor.fetchone()[0]
print(f'\nUnknown IPs with NULL rdap_response: {null_responses}')

# Look at the get_provider_for_ip logic in the script
print('\n\nPotential issues found:')
print('1. The nightly_meraki_db.py script caches "Unknown" results')
print('2. Once an IP is cached as "Unknown", it is never retried')
print('3. The script loads cache at start and uses it throughout')
print('4. Failed RDAP lookups (network errors, etc.) get cached as "Unknown"')

# Check when cache was last updated
cursor.execute("""
    SELECT 
        DATE(last_queried) as query_date,
        COUNT(*) as lookups,
        COUNT(CASE WHEN provider_name = 'Unknown' THEN 1 END) as unknown_count
    FROM rdap_cache
    GROUP BY DATE(last_queried)
    ORDER BY query_date DESC
    LIMIT 7
""")
print('\nCache activity by date:')
for row in cursor.fetchall():
    percent_unknown = (row[2] / row[1] * 100) if row[1] > 0 else 0
    print(f'  {row[0]}: {row[1]} lookups, {row[2]} unknown ({percent_unknown:.1f}%)')

cursor.close()
conn.close()