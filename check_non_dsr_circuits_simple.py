#!/usr/bin/env python3
"""
Check Non-DSR circuits in the database for the provided sites
"""

import psycopg2

def check_non_dsr_circuits():
    # Connect to database
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    # List of sites to check
    sites = [
        'AZK 01', 'AZN 04', 'AZP 41', 'CAL 17', 'CAL 20', 'CAL 24', 'CAL 29',
        'CAN 16', 'CAO 01', 'CAS 35', 'CAS 40', 'CAS 41', 'CAS 46', 'COD 41',
        'GAA 43', 'MOO 04', 'MOS 02', 'TXA 12'
    ]
    
    print("=== NON-DSR CIRCUITS DATABASE CHECK ===\n")
    
    # Check circuits table
    print("1. CIRCUITS TABLE DATA:")
    print("-" * 80)
    print(f"{'Site':<8} {'Provider':<15} {'Speed':<15} {'Cost':<10} {'Purpose':<15} {'Status':<8} {'Source':<10}")
    print("-" * 80)
    
    found_sites = []
    for site in sites:
        cursor.execute("""
            SELECT 
                site_name,
                provider_name,
                details_ordered_service_speed,
                billing_monthly_cost,
                circuit_purpose,
                status,
                data_source
            FROM circuits
            WHERE site_name = %s
            ORDER BY provider_name
        """, (site,))
        
        rows = cursor.fetchall()
        if rows:
            found_sites.append(site)
            for row in rows:
                cost = f"${row[3]:.2f}" if row[3] else "$0.00"
                print(f"{row[0]:<8} {(row[1] or 'N/A'):<15} {(row[2] or 'N/A'):<15} {cost:<10} {(row[4] or 'N/A'):<15} {(row[5] or 'N/A'):<8} {(row[6] or 'N/A'):<10}")
        else:
            print(f"{site:<8} {'NOT FOUND':<15} {'':<15} {'':<10} {'':<15} {'':<8} {'':<10}")
    
    # Check enriched_circuits table
    print("\n2. ENRICHED_CIRCUITS TABLE DATA:")
    print("-" * 80)
    print(f"{'Site':<8} {'WAN1 Provider':<20} {'WAN1 Speed':<15} {'WAN2 Provider':<20} {'WAN2 Speed':<15}")
    print("-" * 80)
    
    enriched_found = []
    for site in sites:
        cursor.execute("""
            SELECT 
                network_name,
                wan1_provider,
                wan1_speed,
                wan2_provider,
                wan2_speed
            FROM enriched_circuits
            WHERE network_name = %s
        """, (site,))
        
        row = cursor.fetchone()
        if row:
            enriched_found.append(site)
            print(f"{row[0]:<8} {(row[1] or 'N/A'):<20} {(row[2] or 'N/A'):<15} {(row[3] or 'N/A'):<20} {(row[4] or 'N/A'):<15}")
        else:
            print(f"{site:<8} {'NOT FOUND':<20} {'':<15} {'':<20} {'':<15}")
    
    # Summary statistics
    print("\n3. SUMMARY:")
    print("-" * 40)
    
    cursor.execute("""
        SELECT COUNT(*) FROM circuits 
        WHERE site_name = ANY(%s)
    """, (sites,))
    circuits_count = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM circuits 
        WHERE site_name = ANY(%s) AND data_source = 'Non-DSR'
    """, (sites,))
    non_dsr_count = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) FROM enriched_circuits 
        WHERE network_name = ANY(%s)
    """, (sites,))
    enriched_count = cursor.fetchone()[0]
    
    print(f"Total circuits records: {circuits_count}")
    print(f"Non-DSR circuits: {non_dsr_count}")
    print(f"Enriched circuits records: {enriched_count}")
    print(f"Sites checked: {len(sites)}")
    print(f"Sites found in circuits: {len(found_sites)}")
    print(f"Sites found in enriched: {len(enriched_found)}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_non_dsr_circuits()