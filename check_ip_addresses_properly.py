#!/usr/bin/env python3
"""
Check IP addresses from meraki_inventory table where they're actually stored
"""

import psycopg2

def check_ip_addresses():
    # Connect to database
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    print("=== CHECKING IP ADDRESSES IN MERAKI_INVENTORY ===\n")
    
    # First check specific sites
    test_sites = ['VAW 04', 'MSG 01', 'ALB 01', 'AZK 01']
    
    for site in test_sites:
        cursor.execute("""
            SELECT 
                network_name,
                wan1_ip,
                wan2_ip,
                device_serial
            FROM meraki_inventory
            WHERE network_name = %s
        """, (site,))
        
        result = cursor.fetchone()
        if result:
            print(f"{result[0]}: WAN1_IP='{result[1]}', WAN2_IP='{result[2]}', Serial={result[3]}")
        else:
            print(f"{site}: NOT FOUND in meraki_inventory")
    
    # Count sites with no IPs in meraki_inventory
    print("\n=== SITES WITHOUT IPs IN MERAKI_INVENTORY ===")
    cursor.execute("""
        SELECT COUNT(*)
        FROM meraki_inventory
        WHERE (wan1_ip IS NULL OR wan1_ip = '' OR wan1_ip = 'None')
        AND (wan2_ip IS NULL OR wan2_ip = '' OR wan2_ip = 'None')
    """)
    
    no_ip_count = cursor.fetchone()[0]
    print(f"Sites with no IPs: {no_ip_count}")
    
    # Get some examples
    cursor.execute("""
        SELECT network_name, wan1_ip, wan2_ip
        FROM meraki_inventory
        WHERE (wan1_ip IS NULL OR wan1_ip = '' OR wan1_ip = 'None')
        AND (wan2_ip IS NULL OR wan2_ip = '' OR wan2_ip = 'None')
        LIMIT 20
    """)
    
    examples = cursor.fetchall()
    print("\nExamples of sites without IPs:")
    for ex in examples:
        print(f"  {ex[0]}: WAN1='{ex[1]}', WAN2='{ex[2]}'")
    
    # Check how IPs are stored in enriched_circuits
    print("\n=== CHECKING IP STORAGE IN ENRICHED_CIRCUITS ===")
    cursor.execute("""
        SELECT 
            ec.network_name,
            ec.wan1_ip,
            ec.wan2_ip,
            mi.wan1_ip as mi_wan1_ip,
            mi.wan2_ip as mi_wan2_ip
        FROM enriched_circuits ec
        LEFT JOIN meraki_inventory mi ON mi.network_name = ec.network_name
        WHERE ec.network_name IN ('VAW 04', 'MSG 01', 'ALB 01', 'AZK 01')
    """)
    
    results = cursor.fetchall()
    print("\nComparing enriched_circuits vs meraki_inventory IPs:")
    for r in results:
        print(f"{r[0]}:")
        print(f"  enriched_circuits: WAN1='{r[1]}', WAN2='{r[2]}'")
        print(f"  meraki_inventory:  WAN1='{r[3]}', WAN2='{r[4]}'")
    
    # Check if enriched_circuits IPs come from meraki_inventory
    print("\n=== CHECKING IF ENRICHED_CIRCUITS HAS IPs ===")
    cursor.execute("""
        SELECT COUNT(*)
        FROM enriched_circuits
        WHERE wan1_ip IS NOT NULL AND wan1_ip != '' AND wan1_ip != 'None'
    """)
    has_wan1_ip = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM enriched_circuits
    """)
    total_enriched = cursor.fetchone()[0]
    
    print(f"Enriched circuits with WAN1 IP: {has_wan1_ip} out of {total_enriched}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_ip_addresses()