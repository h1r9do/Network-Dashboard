#!/usr/bin/env python3
"""
Check if DSR circuits have the problematic speed format
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
    
    # Check DSR circuits for problematic speed formats
    cursor.execute("""
        SELECT site_name, circuit_purpose, provider_name, details_ordered_service_speed
        FROM circuits
        WHERE status = 'Enabled'
        AND details_ordered_service_speed LIKE '%% M'
        ORDER BY site_name
        LIMIT 20
    """)
    
    print("DSR Circuits with space before M in speed:")
    results = cursor.fetchall()
    for row in results:
        print(f"  {row[0]} - {row[1]}: {row[2]} - '{row[3]}'")
    
    print(f"\nTotal found: {len(results)}")
    
    # Check specific sites
    print("\n" + "="*60)
    print("\nChecking specific problem sites in DSR circuits:")
    
    for site in ['CAN 30', 'COD 36', 'NMA 02', 'GAA 21']:
        cursor.execute("""
            SELECT site_name, circuit_purpose, provider_name, details_ordered_service_speed
            FROM circuits
            WHERE site_name = %s
            AND status = 'Enabled'
        """, (site,))
        
        rows = cursor.fetchall()
        if rows:
            print(f"\n{site}:")
            for row in rows:
                print(f"  {row[1]}: {row[2]} - '{row[3]}'")
        else:
            print(f"\n{site}: No DSR circuits found")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")