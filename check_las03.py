#!/usr/bin/env python3
"""
Check LAS 03 specifically in the database
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
    
    print("=== LAS 03 Investigation ===\n")
    
    # Check in meraki_inventory
    print("1. Meraki Inventory:")
    cursor.execute("""
        SELECT *
        FROM meraki_inventory
        WHERE network_name ILIKE '%las%03%' OR network_name = 'LAS 03'
    """)
    
    meraki_results = cursor.fetchall()
    if meraki_results:
        for row in meraki_results:
            print(f"  Network: {row['network_name']}")
            print(f"  Network ID: {row['network_id']}")
            print(f"  Device: {row['device_model']} - {row['device_name']}")
            print(f"  Tags: {row['device_tags']}")
            print(f"  WAN1 IP: {row['wan1_ip']}")
            print(f"  WAN2 IP: {row['wan2_ip']}")
            print(f"  Last Updated: {row['last_updated']}")
    else:
        print("  Not found in meraki_inventory")
    
    # Check in enriched_circuits
    print("\n2. Enriched Circuits:")
    cursor.execute("""
        SELECT *
        FROM enriched_circuits
        WHERE network_name ILIKE '%las%03%' OR network_name = 'LAS 03'
    """)
    
    enriched_results = cursor.fetchall()
    if enriched_results:
        for row in enriched_results:
            print(f"  Network: {row['network_name']}")
            print(f"  Device Tags: {row['device_tags']}")
            print(f"  WAN1 Provider: {row['wan1_provider']}")
            print(f"  WAN2 Provider: {row['wan2_provider']}")
            print(f"  Last Updated: {row['last_updated']}")
    else:
        print("  Not found in enriched_circuits")
    
    # Check in circuits table
    print("\n3. Circuits Table:")
    cursor.execute("""
        SELECT site_name, provider_name, status, circuit_purpose
        FROM circuits
        WHERE site_name ILIKE '%las%03%' OR site_name = 'LAS 03'
    """)
    
    circuit_results = cursor.fetchall()
    if circuit_results:
        for row in circuit_results:
            print(f"  Site: {row['site_name']}")
            print(f"  Provider: {row['provider_name']}")
            print(f"  Status: {row['status']}")
            print(f"  Purpose: {row['circuit_purpose']}")
    else:
        print("  Not found in circuits table")
    
    # Search for similar names
    print("\n4. Similar Network Names:")
    cursor.execute("""
        SELECT DISTINCT network_name
        FROM meraki_inventory
        WHERE network_name ILIKE '%las%'
        ORDER BY network_name
    """)
    
    similar_results = cursor.fetchall()
    if similar_results:
        for row in similar_results:
            print(f"  {row['network_name']}")
    
    conn.close()