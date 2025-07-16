#!/usr/bin/env python3
"""Simple check for CAL 24 data"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

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
    
    # Check circuits table columns first
    print("1. Circuits table schema:")
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'circuits'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    print("Columns:", [col[0] for col in columns])
    
    # Check circuits table
    print("\n1. Circuits table data:")
    cur.execute("""
        SELECT id, site_name, site_id, status
        FROM circuits 
        WHERE LOWER(site_name) = 'cal 24'
    """)
    circuits = cur.fetchall()
    print(f"Found {len(circuits)} circuits for CAL 24")
    for row in circuits:
        print(f"  ID: {row[0]}, Site: {row[1]}, Site ID: {row[2]}")
        print(f"  Status: {row[3]}\n")
    
    # Check meraki_inventory
    print("\n2. Meraki Inventory table:")
    cur.execute("""
        SELECT device_serial, network_name, model, wan1_ip, wan2_ip, 
               wan1_arin_provider, wan2_arin_provider, last_updated
        FROM meraki_inventory 
        WHERE LOWER(network_name) = 'cal 24'
    """)
    devices = cur.fetchall()
    print(f"Found {len(devices)} Meraki devices for CAL 24")
    for row in devices:
        print(f"  Serial: {row[0]}, Network: {row[1]}, Model: {row[2]}")
        print(f"  WAN1 IP: {row[3]}, WAN2 IP: {row[4]}")
        print(f"  WAN1 Provider: {row[5]}, WAN2 Provider: {row[6]}")
        print(f"  Last Updated: {row[7]}\n")
    
    # Check enriched_circuits
    print("\n3. Enriched Circuits table:")
    cur.execute("""
        SELECT id, network_name, site_id, wan1_ip, wan2_ip, 
               wan1_arin_org, wan2_arin_org, last_updated
        FROM enriched_circuits 
        WHERE LOWER(network_name) = 'cal 24'
    """)
    enriched = cur.fetchall()
    print(f"Found {len(enriched)} enriched circuits for CAL 24")
    for row in enriched:
        print(f"  ID: {row[0]}, Network: {row[1]}, Site ID: {row[2]}")
        print(f"  WAN1 IP: {row[3]}, WAN2 IP: {row[4]}")
        print(f"  WAN1 Org: {row[5]}, WAN2 Org: {row[6]}")
        print(f"  Last Updated: {row[7]}\n")
    
    # Check for CAL networks
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
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")