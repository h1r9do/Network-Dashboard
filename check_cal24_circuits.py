#!/usr/bin/env python3
"""
Check CAL 24 circuits to see why there are duplicates
"""

import psycopg2

def check_cal24_circuits():
    # Connect to database
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    print("=== CAL 24 CIRCUITS ANALYSIS ===\n")
    
    # Get all CAL 24 records
    cursor.execute("""
        SELECT 
            id,
            site_name,
            provider_name,
            details_ordered_service_speed,
            billing_monthly_cost,
            circuit_purpose,
            status,
            data_source,
            created_at,
            updated_at
        FROM circuits
        WHERE site_name = 'CAL 24'
        ORDER BY created_at, id
    """)
    
    results = cursor.fetchall()
    
    print(f"Found {len(results)} records for CAL 24:")
    print("-" * 120)
    print(f"{'ID':<6} {'Provider':<20} {'Speed':<15} {'Cost':<10} {'Purpose':<12} {'Status':<20} {'Source':<12} {'Created':<20}")
    print("-" * 120)
    
    for row in results:
        cost_str = f"${row[4]:.2f}" if row[4] else "$0.00"
        created_str = row[8].strftime('%Y-%m-%d %H:%M') if row[8] else 'N/A'
        print(f"{row[0]:<6} {(row[2] or 'N/A'):<20} {(row[3] or 'N/A'):<15} {cost_str:<10} {(row[5] or 'N/A'):<12} {(row[6] or 'N/A'):<20} {(row[7] or 'N/A'):<12} {created_str:<20}")
    
    # Check if there are duplicates by provider
    print(f"\n=== DUPLICATE ANALYSIS ===")
    cursor.execute("""
        SELECT 
            provider_name,
            COUNT(*) as count,
            string_agg(CAST(id AS TEXT), ', ') as ids
        FROM circuits
        WHERE site_name = 'CAL 24'
        GROUP BY provider_name
        HAVING COUNT(*) > 1
        ORDER BY provider_name
    """)
    
    duplicates = cursor.fetchall()
    
    if duplicates:
        print("Duplicate providers found:")
        for dup in duplicates:
            print(f"  {dup[0]}: {dup[1]} records (IDs: {dup[2]})")
    else:
        print("No duplicate providers found")
    
    # Check enriched circuits for CAL 24
    print(f"\n=== ENRICHED CIRCUITS ===")
    cursor.execute("""
        SELECT 
            network_name,
            wan1_provider,
            wan1_speed,
            wan2_provider,
            wan2_speed
        FROM enriched_circuits
        WHERE network_name = 'CAL 24'
    """)
    
    enriched = cursor.fetchone()
    if enriched:
        print(f"WAN1: {enriched[1] or 'N/A'} - {enriched[2] or 'N/A'}")
        print(f"WAN2: {enriched[3] or 'N/A'} - {enriched[4] or 'N/A'}")
    else:
        print("No enriched circuit record found")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_cal24_circuits()