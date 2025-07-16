#!/usr/bin/env python3
"""
Investigate why Comcast has 97% corruption rate while Comcast Workplace has only 0.8%
"""

import psycopg2

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def investigate_provider_differences():
    """Deep dive into provider-specific corruption"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("=== INVESTIGATING PROVIDER-SPECIFIC CORRUPTION ===\n")
    
    # 1. Compare Comcast vs Comcast Workplace
    print("1. Comparing 'Comcast' vs 'Comcast Workplace' data sources...\n")
    
    # Check DSR data for both providers
    cursor.execute("""
        SELECT 
            provider_name,
            COUNT(*) as total,
            COUNT(CASE WHEN details_ordered_service_speed LIKE '%%x%%' THEN 1 END) as has_full_format,
            COUNT(CASE WHEN details_ordered_service_speed NOT LIKE '%%x%%' THEN 1 END) as missing_upload
        FROM circuits
        WHERE status = 'Enabled'
        AND provider_name IN ('Comcast', 'Comcast Workplace')
        GROUP BY provider_name
    """)
    
    print("DSR Circuits Table:")
    print("Provider            | Total | Full Format | Missing Upload")
    print("-" * 60)
    for row in cursor.fetchall():
        print(f"{row[0]:<18} | {row[1]:>5} | {row[2]:>11} | {row[3]:>14}")
    
    # Check enriched data
    print("\n\nEnriched Circuits Table:")
    cursor.execute("""
        SELECT 
            wan1_provider,
            COUNT(*) as total,
            COUNT(CASE WHEN wan1_speed LIKE '%%x%%' THEN 1 END) as has_full_format,
            COUNT(CASE WHEN wan1_speed LIKE '%% M' THEN 1 END) as corrupted
        FROM enriched_circuits
        WHERE wan1_provider IN ('Comcast', 'Comcast Workplace')
        GROUP BY wan1_provider
    """)
    
    print("Provider            | Total | Full Format | Corrupted")
    print("-" * 60)
    for row in cursor.fetchall():
        print(f"{row[0]:<18} | {row[1]:>5} | {row[2]:>11} | {row[3]:>9}")
    
    # 2. Check specific examples
    print("\n\n2. Examining specific Comcast sites...")
    
    cursor.execute("""
        SELECT 
            ec.network_name,
            ec.wan1_provider,
            ec.wan1_speed,
            c.site_name as dsr_site,
            c.provider_name as dsr_provider,
            c.details_ordered_service_speed as dsr_speed,
            mi.device_notes IS NOT NULL as has_meraki_notes,
            CASE 
                WHEN c.site_name IS NOT NULL THEN 'DSR Match Found'
                ELSE 'No DSR Match'
            END as dsr_status
        FROM enriched_circuits ec
        LEFT JOIN circuits c ON c.site_name = REPLACE(ec.network_name, '_', '')
            AND c.circuit_purpose = 'Primary' 
            AND c.status = 'Enabled'
            AND c.provider_name = ec.wan1_provider
        LEFT JOIN meraki_inventory mi ON mi.network_name = ec.network_name
        WHERE ec.wan1_provider = 'Comcast'
        AND ec.wan1_speed LIKE '%% M'
        LIMIT 10
    """)
    
    print("\nComcast sites with corrupted speeds:")
    for row in cursor.fetchall():
        print(f"\n{row[0]}:")
        print(f"  Enriched: {row[1]} - '{row[2]}'")
        print(f"  DSR Data: {row[7]} - Site: {row[3]}, Provider: {row[4]}, Speed: '{row[5]}'")
        print(f"  Has Meraki Notes: {row[6]}")
    
    # 3. Check if the issue is with site name matching
    print("\n\n3. Checking site name matching issues...")
    
    cursor.execute("""
        SELECT 
            ec.network_name,
            ec.wan1_provider,
            ec.wan1_speed,
            array_agg(DISTINCT c.site_name) as matching_dsr_sites,
            array_agg(DISTINCT c.provider_name) as dsr_providers,
            array_agg(DISTINCT c.details_ordered_service_speed) as dsr_speeds
        FROM enriched_circuits ec
        LEFT JOIN circuits c ON (
            c.site_name = ec.network_name OR
            c.site_name = REPLACE(ec.network_name, '_', '') OR
            c.site_name = REPLACE(ec.network_name, ' ', '') OR
            REPLACE(c.site_name, ' ', '') = REPLACE(ec.network_name, '_', '')
        )
        AND c.status = 'Enabled'
        WHERE ec.wan1_provider = 'Comcast'
        AND ec.wan1_speed LIKE '%% M'
        GROUP BY ec.network_name, ec.wan1_provider, ec.wan1_speed
        LIMIT 5
    """)
    
    print("\nSite name matching analysis:")
    for row in cursor.fetchall():
        print(f"\n{row[0]} (Provider: {row[1]}, Speed: '{row[2]}'):")
        print(f"  Matching DSR sites: {row[3]}")
        print(f"  DSR providers: {row[4]}")
        print(f"  DSR speeds: {row[5]}")
    
    # 4. Check the enrichment process flow
    print("\n\n4. Analyzing enrichment data flow...")
    
    cursor.execute("""
        WITH sample_site AS (
            SELECT network_name 
            FROM enriched_circuits 
            WHERE wan1_provider = 'Comcast' 
            AND wan1_speed LIKE '%% M' 
            LIMIT 1
        )
        SELECT 
            ec.network_name,
            ec.wan1_provider as enriched_provider,
            ec.wan1_speed as enriched_speed,
            mi.wan1_ip,
            mi.wan1_arin_provider,
            SUBSTRING(mi.device_notes, 1, 200) as notes_preview,
            c.site_name as dsr_site,
            c.provider_name as dsr_provider,
            c.details_ordered_service_speed as dsr_speed,
            c.ip_address_start as dsr_ip
        FROM enriched_circuits ec
        JOIN sample_site s ON s.network_name = ec.network_name
        LEFT JOIN meraki_inventory mi ON mi.network_name = ec.network_name
        LEFT JOIN circuits c ON c.ip_address_start = mi.wan1_ip
            AND c.status = 'Enabled'
    """)
    
    row = cursor.fetchone()
    if row:
        print(f"\nDetailed flow for {row[0]}:")
        print(f"\nEnriched Data:")
        print(f"  Provider: {row[1]}")
        print(f"  Speed: '{row[2]}'")
        print(f"\nMeraki Data:")
        print(f"  WAN1 IP: {row[3]}")
        print(f"  ARIN Provider: {row[4]}")
        print(f"  Notes: {row[5]}...")
        print(f"\nDSR Match by IP:")
        print(f"  Site: {row[6]}")
        print(f"  Provider: {row[7]}")
        print(f"  Speed: '{row[8]}'")
        print(f"  IP: {row[9]}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    investigate_provider_differences()