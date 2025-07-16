#!/usr/bin/env python3
"""
Check what data exists for CAL 24 in the database
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/usr/local/bin/meraki.env')

# Database connection
DB_HOST = 'localhost'
DB_NAME = 'dsrcircuits'
DB_USER = 'dsruser'
DB_PASS = 'dsrpass123'

print("Checking database for CAL 24 data...")
print("="*80)

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    cur = conn.cursor()
    
    # Check circuits table
    print("\n1. Circuits table:")
    cur.execute("""
        SELECT site_id, site_name, circuit_purpose, provider_name, 
               details_ordered_service_speed, billing_monthly_cost, status
        FROM circuits 
        WHERE site_name = 'CAL 24'
    """)
    
    circuits = cur.fetchall()
    if circuits:
        for circuit in circuits:
            print(f"  Site ID: {circuit[0] or 'None'}")
            print(f"  Site Name: {circuit[1]}")
            print(f"  Purpose: {circuit[2]}")
            print(f"  Provider: {circuit[3]}")
            print(f"  Speed: {circuit[4] or 'None'}")
            print(f"  Cost: ${circuit[5] or 0}")
            print(f"  Status: {circuit[6]}")
            print()
    else:
        print("  No circuits found for CAL 24")
    
    # Check enriched_circuits table
    print("\n2. Enriched circuits table:")
    cur.execute("""
        SELECT network_name, wan1_ip, wan2_ip, wan1_arin_org, wan2_arin_org,
               wan1_provider, wan2_provider
        FROM enriched_circuits 
        WHERE network_name = 'CAL 24'
    """)
    
    enriched = cur.fetchall()
    if enriched:
        for row in enriched:
            print(f"  Network Name: {row[0]}")
            print(f"  WAN1 IP: {row[1] or 'None'}")
            print(f"  WAN2 IP: {row[2] or 'None'}")
            print(f"  WAN1 ARIN Org: {row[3] or 'None'}")
            print(f"  WAN2 ARIN Org: {row[4] or 'None'}")
            print(f"  WAN1 Provider: {row[5] or 'None'}")
            print(f"  WAN2 Provider: {row[6] or 'None'}")
            print()
    else:
        print("  No enriched circuits found for CAL 24")
    
    # Check meraki_inventory table
    print("\n3. Meraki inventory table:")
    cur.execute("""
        SELECT network_name, device_serial, wan1_ip, wan2_ip,
               wan1_arin_provider, wan2_arin_provider
        FROM meraki_inventory 
        WHERE network_name = 'CAL 24'
    """)
    
    meraki = cur.fetchall()
    if meraki:
        for row in meraki:
            print(f"  Network: {row[0]}")
            print(f"  Serial: {row[1]}")
            print(f"  WAN1 IP: {row[2] or 'None'}")
            print(f"  WAN2 IP: {row[3] or 'None'}")
            print(f"  WAN1 ARIN: {row[4] or 'None'}")
            print(f"  WAN2 ARIN: {row[5] or 'None'}")
            print()
    else:
        print("  No Meraki device found for CAL 24")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")

print("="*80)