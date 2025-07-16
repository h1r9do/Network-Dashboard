#!/usr/bin/env python3
"""
Check exact DSR speeds for problem sites
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
    
    # Check all speed values in circuits table
    print("Checking for any DSR speeds with space before M...")
    
    cursor.execute("""
        SELECT DISTINCT details_ordered_service_speed
        FROM circuits
        WHERE status = 'Enabled'
        AND details_ordered_service_speed IS NOT NULL
        AND details_ordered_service_speed != ''
        ORDER BY details_ordered_service_speed
    """)
    
    all_speeds = [row[0] for row in cursor.fetchall()]
    
    space_m_speeds = []
    for speed in all_speeds:
        if re.search(r'\d+\.?\d*\s+M(?!B)', speed):
            space_m_speeds.append(speed)
    
    if space_m_speeds:
        print(f"\nFound {len(space_m_speeds)} unique DSR speeds with space before M:")
        for speed in space_m_speeds[:20]:
            print(f"  '{speed}'")
            
        # Find which sites have these speeds
        print("\nSites with these speeds:")
        for speed in space_m_speeds[:5]:
            cursor.execute("""
                SELECT site_name, circuit_purpose, provider_name
                FROM circuits
                WHERE details_ordered_service_speed = %s
                AND status = 'Enabled'
                LIMIT 5
            """, (speed,))
            
            sites = cursor.fetchall()
            if sites:
                print(f"\n  Speed '{speed}':")
                for site in sites:
                    print(f"    {site[0]} - {site[1]}: {site[2]}")
    else:
        print("\nNo DSR speeds found with space before M!")
        
    # Let's check what formats exist
    print("\n" + "="*60)
    print("\nSample of speed formats in DSR:")
    
    # Get a variety of speeds
    sample_speeds = []
    for speed in all_speeds[:50]:
        if speed and speed not in ['Cell', 'Satellite']:
            sample_speeds.append(speed)
    
    print("First 20 non-Cell/Satellite speeds:")
    for speed in sample_speeds[:20]:
        print(f"  '{speed}'")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")