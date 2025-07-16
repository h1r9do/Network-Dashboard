#!/usr/bin/env python3
"""Check meraki_inventory table thoroughly for CAL 24"""

import psycopg2

# Database connection
db_host = 'localhost'
db_name = 'dsrcircuits'
db_user = 'dsruser'
db_pass = 'dsrpass123'

try:
    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_pass
    )
    cur = conn.cursor()
    
    print("=== Checking meraki_inventory for CAL 24 ===\n")
    
    # 1. Check all data for CAL 24
    print("1. Complete meraki_inventory record for CAL 24:")
    cur.execute("""
        SELECT 
            id,
            organization_name,
            network_id,
            network_name,
            device_serial,
            device_model,
            device_name,
            device_tags,
            wan1_ip,
            wan2_ip,
            wan1_public_ip,
            wan2_public_ip,
            wan1_assignment,
            wan2_assignment,
            wan1_arin_provider,
            wan2_arin_provider,
            wan1_provider_label,
            wan2_provider_label,
            ddns_enabled,
            ddns_url,
            device_notes,
            last_updated
        FROM meraki_inventory 
        WHERE LOWER(network_name) = 'cal 24'
    """)
    
    columns = [desc[0] for desc in cur.description]
    records = cur.fetchall()
    
    print(f"Found {len(records)} records for CAL 24\n")
    for record in records:
        for i, col in enumerate(columns):
            print(f"  {col}: {record[i]}")
        print()
    
    # 2. Check if device serial exists with different network name
    print("\n2. Checking device serial Q2QN-YZRA-UCYJ across all networks:")
    cur.execute("""
        SELECT network_name, device_serial, wan1_ip, wan2_ip, last_updated
        FROM meraki_inventory 
        WHERE device_serial = 'Q2QN-YZRA-UCYJ'
    """)
    
    serials = cur.fetchall()
    print(f"Found {len(serials)} records with this serial:")
    for row in serials:
        print(f"  Network: {row[0]}, Serial: {row[1]}")
        print(f"  WAN1: {row[2]}, WAN2: {row[3]}")
        print(f"  Last Updated: {row[4]}\n")
    
    # 3. Check for similar network names
    print("\n3. Checking for similar network names (fuzzy match):")
    cur.execute("""
        SELECT DISTINCT network_name, device_serial, wan1_ip, wan2_ip
        FROM meraki_inventory 
        WHERE network_name ILIKE '%cal%24%' 
           OR network_name ILIKE '%cal%' AND network_name LIKE '%24%'
        ORDER BY network_name
    """)
    
    similar = cur.fetchall()
    print(f"Found {len(similar)} similar network names:")
    for row in similar:
        print(f"  Network: {row[0]}, Serial: {row[1]}")
        print(f"  WAN1: {row[2]}, WAN2: {row[3]}\n")
    
    # 4. Check when CAL 24 was last successfully updated with IPs
    print("\n4. Historical check - When did CAL 24 last have IP addresses?")
    cur.execute("""
        SELECT 
            network_name,
            device_serial,
            wan1_ip,
            wan2_ip,
            wan1_arin_provider,
            wan2_arin_provider,
            last_updated
        FROM meraki_inventory 
        WHERE network_name = 'CAL 24'
        ORDER BY last_updated DESC
    """)
    
    history = cur.fetchall()
    for row in history:
        print(f"  {row[6]}: WAN1={row[2]}, WAN2={row[3]}")
        print(f"  Providers: WAN1={row[4]}, WAN2={row[5]}\n")
    
    # 5. Check latest updates across all CAL sites
    print("\n5. Latest updates for all CAL sites (sample):")
    cur.execute("""
        SELECT 
            network_name,
            wan1_ip,
            wan2_ip,
            last_updated
        FROM meraki_inventory 
        WHERE network_name LIKE 'CAL %' 
          AND network_name NOT LIKE '%CALLCNTR%'
        ORDER BY network_name
        LIMIT 10
    """)
    
    cal_sites = cur.fetchall()
    for row in cal_sites:
        has_ips = "✓ Has IPs" if (row[1] or row[2]) else "✗ No IPs"
        print(f"  {row[0]}: {has_ips} (Updated: {row[3]})")
    
    # 6. Check network_id to see if it's a valid Meraki network
    print("\n6. Network ID analysis:")
    cur.execute("""
        SELECT network_id, network_name, COUNT(*) as device_count
        FROM meraki_inventory 
        WHERE network_name = 'CAL 24'
        GROUP BY network_id, network_name
    """)
    
    network_ids = cur.fetchall()
    for row in network_ids:
        print(f"  Network ID: {row[0]}")
        print(f"  Network Name: {row[1]}")
        print(f"  Device Count: {row[2]}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")