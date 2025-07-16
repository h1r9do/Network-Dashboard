#!/usr/bin/env python3
"""Check if there's a join issue causing CAL 24 to get CAN 24's data"""

import psycopg2

# Database connection
db_host = 'localhost'
db_name = 'dsrcircuits'
db_user = 'dsruser' 
db_pass = 'dsrpass123'

def check_join():
    conn = psycopg2.connect(
        host=db_host,
        dbname=db_name,
        user=db_user,
        password=db_pass
    )
    cur = conn.cursor()
    
    print("=== Checking for Join Issues ===\n")
    
    # Check if there's a case sensitivity issue
    print("1. Check case sensitivity in joins:")
    cur.execute("""
        SELECT 
            ec1.network_name as ec_network,
            ec2.network_name as potential_match,
            ec2.wan1_ip,
            ec2.wan2_ip
        FROM enriched_circuits ec1
        JOIN enriched_circuits ec2 ON LOWER(ec1.network_name) = LOWER(ec2.network_name)
        WHERE ec1.network_name = 'CAL 24'
        ORDER BY ec2.network_name
    """)
    for row in cur.fetchall():
        print(f"  {row[0]} matches with {row[1]}: WAN1={row[2]}, WAN2={row[3]}")
    
    # Check CAN 24 IPs
    print("\n2. CAN 24 IP addresses:")
    cur.execute("""
        SELECT network_name, wan1_ip, wan2_ip
        FROM enriched_circuits
        WHERE network_name = 'CAN 24'
    """)
    result = cur.fetchone()
    if result:
        print(f"  Network: {result[0]}")
        print(f"  WAN1 IP: {result[1]}")
        print(f"  WAN2 IP: {result[2]}")
    
    # Check if CAN 24 has the IPs that CAL 24 is showing
    print("\n3. Looking for the mystery IPs (45.19.143.81, 96.81.191.61):")
    cur.execute("""
        SELECT network_name, wan1_ip, wan2_ip
        FROM enriched_circuits
        WHERE wan1_ip = '45.19.143.81' OR wan2_ip = '96.81.191.61'
           OR wan1_ip = '96.81.191.61' OR wan2_ip = '45.19.143.81'
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: WAN1={row[1]}, WAN2={row[2]}")
    
    # Check meraki_inventory for the same IPs
    print("\n4. Checking meraki_inventory for mystery IPs:")
    cur.execute("""
        SELECT network_name, device_serial, wan1_ip, wan2_ip
        FROM meraki_inventory
        WHERE wan1_ip = '45.19.143.81' OR wan2_ip = '96.81.191.61'
           OR wan1_ip = '96.81.191.61' OR wan2_ip = '45.19.143.81'
    """)
    for row in cur.fetchall():
        print(f"  {row[0]} ({row[1]}): WAN1={row[2]}, WAN2={row[3]}")
    
    # Check if it's a frontend issue - what does the ARIN refresh see?
    print("\n5. What ARIN refresh would see for CAL 24:")
    cur.execute("""
        SELECT 
            ec.network_name,
            ec.wan1_ip as ec_wan1,
            ec.wan2_ip as ec_wan2,
            mi.wan1_ip as mi_wan1,
            mi.wan2_ip as mi_wan2,
            mi.device_serial
        FROM enriched_circuits ec
        LEFT JOIN meraki_inventory mi ON LOWER(ec.network_name) = LOWER(mi.network_name)
        WHERE ec.network_name = 'CAL 24'
    """)
    result = cur.fetchone()
    if result:
        print(f"  Network: {result[0]}")
        print(f"  Enriched WAN1: {result[1]}")
        print(f"  Enriched WAN2: {result[2]}")
        print(f"  Meraki WAN1: {result[3]}")
        print(f"  Meraki WAN2: {result[4]}")
        print(f"  Device: {result[5]}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_join()