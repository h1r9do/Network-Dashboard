#!/usr/bin/env python3
"""
Check characteristics of sites that appear on dsrcircuits but shouldn't (not live)
Focus on IP addresses as the indicator
"""

import psycopg2

def check_non_live_sites():
    # Connect to database
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    # Sites to check
    test_sites = ['VAW 04', 'MSG 01']
    
    print("=== CHECKING NON-LIVE SITES ===\n")
    
    for site in test_sites:
        print(f"\n{'='*60}")
        print(f"SITE: {site}")
        print('='*60)
        
        # Check enriched_circuits
        print("\n1. ENRICHED_CIRCUITS DATA:")
        cursor.execute("""
            SELECT 
                network_name,
                wan1_provider, wan1_speed, wan1_ip,
                wan2_provider, wan2_speed, wan2_ip
            FROM enriched_circuits
            WHERE network_name = %s
        """, (site,))
        
        result = cursor.fetchone()
        if result:
            print(f"  Network: {result[0]}")
            print(f"  WAN1: Provider='{result[1]}', Speed='{result[2]}', IP='{result[3]}'")
            print(f"  WAN2: Provider='{result[4]}', Speed='{result[5]}', IP='{result[6]}'")
            
            # Check if site has NO IPs
            has_no_ips = (not result[3] or result[3] == '') and (not result[6] or result[6] == '')
            print(f"  ⚠️  NO IP ADDRESSES: {has_no_ips}")
        else:
            print("  NOT FOUND in enriched_circuits")
        
        # Check meraki_inventory
        print("\n2. MERAKI_INVENTORY DATA:")
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
            print(f"  Network: {result[0]}")
            print(f"  WAN1 IP: '{result[1]}'")
            print(f"  WAN2 IP: '{result[2]}'")
            print(f"  Device Serial: {result[3]}")
        else:
            print("  NOT FOUND in meraki_inventory")
        
        # Check circuits table
        print("\n3. CIRCUITS TABLE DATA:")
        cursor.execute("""
            SELECT 
                site_name, provider_name, status,
                ip_address_start
            FROM circuits
            WHERE site_name = %s
        """, (site,))
        
        circuits = cursor.fetchall()
        if circuits:
            for circuit in circuits:
                print(f"  Provider: {circuit[1]}, Status: {circuit[2]}, IP: '{circuit[3]}'")
        else:
            print("  NOT FOUND in circuits table")
    
    # Count total sites without IPs that are showing
    print("\n\n=== SITES ON DSRCIRCUITS WITHOUT ANY IP ADDRESSES ===")
    cursor.execute("""
        SELECT 
            network_name,
            wan1_provider,
            wan2_provider,
            wan1_ip,
            wan2_ip
        FROM enriched_circuits
        WHERE (wan1_ip IS NULL OR wan1_ip = '')
        AND (wan2_ip IS NULL OR wan2_ip = '')
        AND network_name NOT ILIKE '%hub%'
        AND network_name NOT ILIKE '%lab%'
        AND network_name NOT ILIKE '%voice%'
        AND network_name NOT ILIKE '%test%'
        ORDER BY network_name
        LIMIT 30
    """)
    
    no_ip_sites = cursor.fetchall()
    print(f"\nSites without any IP addresses (showing first 30):")
    for site in no_ip_sites:
        print(f"  {site[0]}: WAN1='{site[1]}', WAN2='{site[2]}'")
    
    # Count total
    cursor.execute("""
        SELECT COUNT(*)
        FROM enriched_circuits
        WHERE (wan1_ip IS NULL OR wan1_ip = '')
        AND (wan2_ip IS NULL OR wan2_ip = '')
        AND network_name NOT ILIKE '%hub%'
        AND network_name NOT ILIKE '%lab%'
        AND network_name NOT ILIKE '%voice%'
        AND network_name NOT ILIKE '%test%'
    """)
    
    total = cursor.fetchone()[0]
    print(f"\n⚠️  Total sites without any IP addresses: {total}")
    print("\nThese sites should likely be filtered out from the dsrcircuits page")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_non_live_sites()