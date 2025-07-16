#!/usr/bin/env python3
"""Debug CAL 24 enriched data"""

import psycopg2

# Database connection
db_host = 'localhost'
db_name = 'dsrcircuits'
db_user = 'dsruser' 
db_pass = 'dsrpass123'

def debug_cal24():
    conn = psycopg2.connect(
        host=db_host,
        dbname=db_name,
        user=db_user,
        password=db_pass
    )
    cur = conn.cursor()
    
    print("=== Debugging CAL 24 Enriched Data ===\n")
    
    # Check enriched_circuits
    print("1. Enriched Circuits data for CAL 24:")
    cur.execute("""
        SELECT network_name, wan1_ip, wan2_ip, wan1_provider, wan2_provider,
               last_updated
        FROM enriched_circuits
        WHERE network_name = 'CAL 24'
    """)
    result = cur.fetchone()
    if result:
        print(f"  Network: {result[0]}")
        print(f"  WAN1 IP: {result[1]}")
        print(f"  WAN2 IP: {result[2]}")
        print(f"  WAN1 Provider: {result[3]}")
        print(f"  WAN2 Provider: {result[4]}")
        print(f"  Last Updated: {result[5]}")
    else:
        print("  No enriched data found for CAL 24")
    
    # Check if there's any confusion with similar names
    print("\n2. Sites with similar names:")
    cur.execute("""
        SELECT network_name, wan1_ip, wan2_ip 
        FROM enriched_circuits 
        WHERE network_name LIKE 'CA% 24'
        ORDER BY network_name
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: WAN1={row[1]}, WAN2={row[2]}")
    
    # Check meraki_inventory join
    print("\n3. Meraki inventory join data:")
    cur.execute("""
        SELECT 
            mi.network_name,
            mi.wan1_ip as mi_wan1_ip, 
            mi.wan2_ip as mi_wan2_ip,
            ec.wan1_ip as ec_wan1_ip,
            ec.wan2_ip as ec_wan2_ip,
            ec.network_name as ec_network_name
        FROM meraki_inventory mi
        LEFT JOIN enriched_circuits ec ON LOWER(mi.network_name) = LOWER(ec.network_name)
        WHERE mi.network_name = 'CAL 24'
    """)
    result = cur.fetchone()
    if result:
        print(f"  MI Network: {result[0]}")
        print(f"  MI WAN1 IP: {result[1]}")
        print(f"  MI WAN2 IP: {result[2]}")
        print(f"  EC WAN1 IP: {result[3]}")
        print(f"  EC WAN2 IP: {result[4]}")
        print(f"  EC Network: {result[5]}")
    
    # Check the actual query used by confirm_site
    print("\n4. Confirm site query result:")
    cur.execute("""
        SELECT 
            mi.device_serial, mi.device_model, mi.device_name, mi.device_tags,
            mi.wan1_ip, mi.wan1_arin_provider, ec.wan1_provider, ec.wan1_speed,
            mi.wan2_ip, mi.wan2_arin_provider, ec.wan2_provider, ec.wan2_speed
        FROM meraki_inventory mi
        LEFT JOIN enriched_circuits ec ON mi.network_name = ec.network_name
        WHERE LOWER(mi.network_name) = LOWER('CAL 24')
        AND mi.device_model LIKE 'MX%'
    """)
    result = cur.fetchone()
    if result:
        print(f"  Device: {result[0]}")
        print(f"  Model: {result[1]}")
        print(f"  WAN1 IP: {result[4]} (from meraki_inventory)")
        print(f"  WAN2 IP: {result[8]} (from meraki_inventory)")
        print(f"  WAN1 Provider: {result[6]} (from enriched_circuits)")
        print(f"  WAN2 Provider: {result[10]} (from enriched_circuits)")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    debug_cal24()