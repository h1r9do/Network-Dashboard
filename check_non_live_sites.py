#!/usr/bin/env python3
"""
Check characteristics of sites that appear on dsrcircuits but shouldn't (not live)
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
                wan2_provider, wan2_speed, wan2_ip,
                device_status, device_tags
            FROM enriched_circuits
            WHERE network_name = %s
        """, (site,))
        
        result = cursor.fetchone()
        if result:
            print(f"  Network: {result[0]}")
            print(f"  WAN1: Provider={result[1]}, Speed={result[2]}, IP={result[3]}")
            print(f"  WAN2: Provider={result[4]}, Speed={result[5]}, IP={result[6]}")
            print(f"  Device Status: {result[7]}")
            print(f"  Device Tags: {result[8]}")
        else:
            print("  NOT FOUND in enriched_circuits")
        
        # Check meraki_inventory
        print("\n2. MERAKI_INVENTORY DATA:")
        cursor.execute("""
            SELECT 
                network_name, network_id,
                device_serial, device_status,
                wan1_status, wan1_ip,
                wan2_status, wan2_ip,
                device_tags
            FROM meraki_inventory
            WHERE network_name = %s
        """, (site,))
        
        result = cursor.fetchone()
        if result:
            print(f"  Network: {result[0]}")
            print(f"  Network ID: {result[1]}")
            print(f"  Device Serial: {result[2]}")
            print(f"  Device Status: {result[3]}")
            print(f"  WAN1: Status={result[4]}, IP={result[5]}")
            print(f"  WAN2: Status={result[6]}, IP={result[7]}")
            print(f"  Tags: {result[8]}")
        else:
            print("  NOT FOUND in meraki_inventory")
        
        # Check circuits table
        print("\n3. CIRCUITS TABLE DATA:")
        cursor.execute("""
            SELECT 
                site_name, provider_name, status,
                ip_address_start, billing_monthly_cost
            FROM circuits
            WHERE site_name = %s
        """, (site,))
        
        circuits = cursor.fetchall()
        if circuits:
            for circuit in circuits:
                print(f"  Provider: {circuit[1]}, Status: {circuit[2]}, IP: {circuit[3]}, Cost: ${circuit[4] or 0}")
        else:
            print("  NOT FOUND in circuits table")
    
    # Now let's find common characteristics of sites without IPs
    print("\n\n=== SITES WITHOUT IP ADDRESSES ===")
    cursor.execute("""
        SELECT 
            network_name,
            wan1_ip,
            wan2_ip,
            device_status,
            wan1_provider,
            wan2_provider
        FROM enriched_circuits
        WHERE (wan1_ip IS NULL OR wan1_ip = '' OR wan1_ip = 'N/A')
        AND (wan2_ip IS NULL OR wan2_ip = '' OR wan2_ip = 'N/A')
        ORDER BY network_name
        LIMIT 20
    """)
    
    no_ip_sites = cursor.fetchall()
    print(f"\nFound {cursor.rowcount} sites without any IP addresses (showing first 20):")
    for site in no_ip_sites:
        print(f"  {site[0]}: Status={site[3]}, WAN1={site[4]}, WAN2={site[5]}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_non_live_sites()