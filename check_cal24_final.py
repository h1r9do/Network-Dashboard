#!/usr/bin/env python3
"""Check CAL 24 data with proper table schemas"""

import psycopg2

# Database connection (from config.py)
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
    
    print("=== Checking CAL 24 data ===\n")
    
    # Check circuits table
    print("1. Circuits table data:")
    cur.execute("""
        SELECT id, site_name, site_id, status, provider_name, circuit_purpose
        FROM circuits 
        WHERE LOWER(site_name) = 'cal 24'
    """)
    circuits = cur.fetchall()
    print(f"Found {len(circuits)} circuits for CAL 24")
    for row in circuits:
        print(f"  ID: {row[0]}, Site: {row[1]}, Site ID: {row[2]}")
        print(f"  Status: {row[3]}, Provider: {row[4]}, Purpose: {row[5]}\n")
    
    # Check meraki_inventory table schema first
    print("\n2. Meraki Inventory table schema:")
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'meraki_inventory'
        ORDER BY ordinal_position
    """)
    meraki_cols = cur.fetchall()
    print("Columns:", [col[0] for col in meraki_cols])
    
    # Check meraki_inventory table
    print("\n2. Meraki Inventory table data:")
    cur.execute("""
        SELECT device_serial, network_name, wan1_ip, wan2_ip, 
               wan1_arin_provider, wan2_arin_provider, last_updated
        FROM meraki_inventory 
        WHERE LOWER(network_name) = 'cal 24'
    """)
    devices = cur.fetchall()
    print(f"Found {len(devices)} Meraki devices for CAL 24")
    for row in devices:
        print(f"  Serial: {row[0]}, Network: {row[1]}")
        print(f"  WAN1 IP: {row[2]}, WAN2 IP: {row[3]}")
        print(f"  WAN1 Provider: {row[4]}, WAN2 Provider: {row[5]}")
        print(f"  Last Updated: {row[6]}\n")
    
    # Check enriched_circuits schema
    print("\n3. Enriched Circuits table schema:")
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'enriched_circuits'
        ORDER BY ordinal_position
    """)
    enriched_cols = cur.fetchall()
    print("Columns:", [col[0] for col in enriched_cols])
    
    # Check enriched_circuits
    print("\n3. Enriched Circuits table data:")
    cur.execute("""
        SELECT id, network_name, wan1_ip, wan2_ip, 
               wan1_arin_org, wan2_arin_org, last_updated
        FROM enriched_circuits 
        WHERE LOWER(network_name) = 'cal 24'
    """)
    enriched = cur.fetchall()
    print(f"Found {len(enriched)} enriched circuits for CAL 24")
    for row in enriched:
        print(f"  ID: {row[0]}, Network: {row[1]}")
        print(f"  WAN1 IP: {row[2]}, WAN2 IP: {row[3]}")
        print(f"  WAN1 Org: {row[4]}, WAN2 Org: {row[5]}")
        print(f"  Last Updated: {row[6]}\n")
    
    # Check for CAL networks in Meraki
    print("\n4. All CAL networks in Meraki inventory:")
    cur.execute("""
        SELECT DISTINCT network_name 
        FROM meraki_inventory 
        WHERE network_name ILIKE '%cal%'
        ORDER BY network_name
    """)
    cal_networks = cur.fetchall()
    print(f"Found {len(cal_networks)} networks with 'CAL' in the name:")
    for row in cal_networks:
        print(f"  - {row[0]}")
    
    # Check what's in meraki_inventory for any device with serial Q2QN-YZRA-UCYJ
    print("\n5. Checking specific device serial Q2QN-YZRA-UCYJ:")
    cur.execute("""
        SELECT device_serial, network_name, wan1_ip, wan2_ip, 
               wan1_arin_provider, wan2_arin_provider
        FROM meraki_inventory 
        WHERE device_serial = 'Q2QN-YZRA-UCYJ'
    """)
    device = cur.fetchone()
    if device:
        print(f"  Found device: Serial={device[0]}, Network={device[1]}")
        print(f"  WAN1 IP: {device[2]}, WAN2 IP: {device[3]}")
        print(f"  WAN1 Provider: {device[4]}, WAN2 Provider: {device[5]}")
    else:
        print("  Device Q2QN-YZRA-UCYJ not found in meraki_inventory")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")