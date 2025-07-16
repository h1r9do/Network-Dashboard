#!/usr/bin/env python3
"""
Check Non-DSR circuits in the database for the provided sites
"""

import psycopg2
from tabulate import tabulate

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
    
    results = []
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
            for row in rows:
                results.append([
                    row[0],  # site_name
                    row[1],  # provider_name
                    row[2],  # speed
                    f"${row[3]:.2f}" if row[3] else "$0.00",  # cost
                    row[4],  # circuit_purpose
                    row[5],  # status
                    row[6]   # data_source
                ])
        else:
            results.append([site, "NOT FOUND", "", "", "", "", ""])
    
    headers = ["Site", "Provider", "Speed", "Cost", "Purpose", "Status", "Source"]
    print(tabulate(results, headers=headers, tablefmt="grid"))
    
    # Check enriched_circuits table
    print("\n2. ENRICHED_CIRCUITS TABLE DATA:")
    print("-" * 80)
    
    enriched_results = []
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
            enriched_results.append([
                row[0],  # network_name
                row[1] or "N/A",  # wan1_provider
                row[2] or "N/A",  # wan1_speed
                row[3] or "N/A",  # wan2_provider
                row[4] or "N/A"   # wan2_speed
            ])
        else:
            enriched_results.append([site, "NOT FOUND", "", "", ""])
    
    headers = ["Site", "WAN1 Provider", "WAN1 Speed", "WAN2 Provider", "WAN2 Speed"]
    print(tabulate(enriched_results, headers=headers, tablefmt="grid"))
    
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
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_non_dsr_circuits()