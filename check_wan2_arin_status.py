#!/usr/bin/env python3
"""
Check WAN2 ARIN resolution status - diagnostic script
"""

import psycopg2
import psycopg2.extras
from config import Config
import re

# Parse database connection
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
if match:
    user, password, host, port, database = match.groups()
    
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )
    
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=== WAN2 ARIN Resolution Status Check ===\n")
    
    # 1. Count total WAN2 interfaces with IPs
    cursor.execute("""
        SELECT COUNT(*) as total
        FROM meraki_inventory
        WHERE wan2_ip IS NOT NULL 
        AND wan2_ip != ''
        AND wan2_ip != 'None'
        AND network_name NOT ILIKE '%hub%'
        AND network_name NOT ILIKE '%lab%'
        AND network_name NOT ILIKE '%voice%'
        AND network_name NOT ILIKE '%test%'
    """)
    total_with_ip = cursor.fetchone()['total']
    print(f"Total WAN2 interfaces with IP addresses: {total_with_ip}")
    
    # 2. Count WAN2 with IPs but no ARIN provider
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM meraki_inventory
        WHERE wan2_ip IS NOT NULL 
        AND wan2_ip != ''
        AND wan2_ip != 'None'
        AND (wan2_arin_provider IS NULL OR wan2_arin_provider = '')
        AND network_name NOT ILIKE '%hub%'
        AND network_name NOT ILIKE '%lab%'
        AND network_name NOT ILIKE '%voice%'
        AND network_name NOT ILIKE '%test%'
    """)
    no_arin = cursor.fetchone()['count']
    print(f"WAN2 with IP but no ARIN provider: {no_arin}")
    
    # 3. Show examples of WAN2 with IP but no ARIN
    if no_arin > 0:
        print("\nExamples of WAN2 with IP but no ARIN provider:")
        cursor.execute("""
            SELECT network_name, wan2_ip, wan2_arin_provider
            FROM meraki_inventory
            WHERE wan2_ip IS NOT NULL 
            AND wan2_ip != ''
            AND wan2_ip != 'None'
            AND (wan2_arin_provider IS NULL OR wan2_arin_provider = '')
            AND network_name NOT ILIKE '%hub%'
            AND network_name NOT ILIKE '%lab%'
            AND network_name NOT ILIKE '%voice%'
            AND network_name NOT ILIKE '%test%'
            LIMIT 10
        """)
        for row in cursor.fetchall():
            print(f"  {row['network_name']}: IP={row['wan2_ip']}, ARIN={row['wan2_arin_provider']}")
    
    # 4. Check enriched_circuits vs meraki_inventory
    print("\n=== Checking EnrichedCircuits vs MerakiInventory ===")
    
    cursor.execute("""
        SELECT 
            e.network_name,
            e.wan2_provider as enriched_provider,
            e.wan2_speed as enriched_speed,
            m.wan2_ip,
            m.wan2_arin_provider,
            m.wan2_provider_label
        FROM enriched_circuits e
        JOIN meraki_inventory m ON e.network_name = m.network_name
        WHERE (e.wan2_speed IS NULL OR e.wan2_speed = '' OR e.wan2_speed = 'N/A' OR e.wan2_speed ILIKE '%unknown%')
        AND (e.wan2_provider = 'Unknown' OR e.wan2_provider = 'N/A' OR e.wan2_provider IS NULL)
        AND m.wan2_arin_provider IS NOT NULL
        AND m.wan2_arin_provider != ''
        AND e.network_name NOT ILIKE '%hub%'
        AND e.network_name NOT ILIKE '%lab%'
        AND e.network_name NOT ILIKE '%voice%'
        AND e.network_name NOT ILIKE '%test%'
        LIMIT 20
    """)
    
    results = cursor.fetchall()
    if results:
        print(f"\nFound {len(results)} cases where EnrichedCircuits shows Unknown but ARIN data exists:")
        for row in results:
            print(f"\n{row['network_name']}:")
            print(f"  Enriched Provider: {row['enriched_provider']}")
            print(f"  WAN2 IP: {row['wan2_ip']}")
            print(f"  ARIN Provider: {row['wan2_arin_provider']}")
            print(f"  Provider Label: {row['wan2_provider_label']}")
    
    conn.close()