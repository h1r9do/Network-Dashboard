#!/usr/bin/env python3
"""Fix CAL 24 data in the database"""

import psycopg2
from datetime import datetime

# Database connection
db_host = 'localhost'
db_name = 'dsrcircuits'
db_user = 'dsruser' 
db_pass = 'dsrpass123'

def fix_cal24():
    conn = psycopg2.connect(
        host=db_host,
        dbname=db_name,
        user=db_user,
        password=db_pass
    )
    cur = conn.cursor()
    
    print("=== Fixing CAL 24 Data ===\n")
    
    # First, verify the current state
    print("1. Current CAL 24 data in meraki_inventory:")
    cur.execute("""
        SELECT network_name, device_serial, wan1_ip, wan2_ip, wan1_arin_provider, wan2_arin_provider
        FROM meraki_inventory
        WHERE network_name = 'CAL 24'
    """)
    result = cur.fetchone()
    if result:
        print(f"  Network: {result[0]}")
        print(f"  Device: {result[1]}")
        print(f"  WAN1 IP: {result[2]} (should be 47.176.12.58)")
        print(f"  WAN2 IP: {result[3]} (should be 166.211.206.131)")
        print(f"  WAN1 ARIN: {result[4]}")
        print(f"  WAN2 ARIN: {result[5]}")
    
    # Update the data with correct IPs
    print("\n2. Updating CAL 24 with correct IP addresses...")
    cur.execute("""
        UPDATE meraki_inventory
        SET wan1_ip = '47.176.12.58',
            wan2_ip = '166.211.206.131',
            wan1_assignment = 'static',
            wan2_assignment = 'dhcp',
            wan1_arin_provider = 'Frontier Communications Corporation',
            wan2_arin_provider = 'Verizon Business',
            last_updated = %s
        WHERE network_name = 'CAL 24'
    """, (datetime.now(),))
    
    # Also update enriched_circuits
    print("\n3. Updating enriched_circuits...")
    cur.execute("""
        UPDATE enriched_circuits
        SET wan1_ip = '47.176.12.58',
            wan2_ip = '166.211.206.131',
            last_updated = %s
        WHERE network_name = 'CAL 24'
    """, (datetime.now(),))
    
    # Commit the changes
    conn.commit()
    print("\n4. Changes committed!")
    
    # Verify the update
    print("\n5. Verifying the update:")
    cur.execute("""
        SELECT network_name, wan1_ip, wan2_ip, wan1_arin_provider, wan2_arin_provider
        FROM meraki_inventory
        WHERE network_name = 'CAL 24'
    """)
    result = cur.fetchone()
    if result:
        print(f"  Network: {result[0]}")
        print(f"  WAN1 IP: {result[1]} ✓")
        print(f"  WAN2 IP: {result[2]} ✓")
        print(f"  WAN1 ARIN: {result[3]}")
        print(f"  WAN2 ARIN: {result[4]}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    fix_cal24()