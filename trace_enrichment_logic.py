#!/usr/bin/env python3
"""
Trace how the enrichment script is matching WAN1/WAN2 instead of just copying DSR data
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

def trace_enrichment_logic():
    """Trace the complex matching logic that's causing issues"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("=== TRACING ENRICHMENT LOGIC ===\n")
    
    # 1. Show what DSR has vs what enrichment produces
    print("1. DSR Data vs Enriched Data Comparison\n")
    
    cursor.execute("""
        SELECT 
            c.site_name,
            c.circuit_purpose,
            c.provider_name as dsr_provider,
            c.details_ordered_service_speed as dsr_speed,
            c.ip_address_start as dsr_ip,
            ec.network_name,
            CASE 
                WHEN c.circuit_purpose = 'Primary' THEN ec.wan1_provider
                ELSE ec.wan2_provider
            END as enriched_provider,
            CASE 
                WHEN c.circuit_purpose = 'Primary' THEN ec.wan1_speed
                ELSE ec.wan2_speed
            END as enriched_speed
        FROM circuits c
        LEFT JOIN enriched_circuits ec ON (
            ec.network_name = c.site_name OR
            ec.network_name = REPLACE(c.site_name, ' ', '_') OR
            ec.network_name = c.site_name || '_00' OR
            REPLACE(ec.network_name, '_', '') = c.site_name
        )
        WHERE c.status = 'Enabled'
        AND c.site_name IN ('CAN00', 'CAN 25', 'COD 01')
        ORDER BY c.site_name, c.circuit_purpose
    """)
    
    print("Site     | Purpose   | DSR Provider        | DSR Speed          | Enriched Provider | Enriched Speed")
    print("-" * 110)
    for row in cursor.fetchall():
        site = row[0]
        purpose = row[1]
        dsr_prov = row[2] or 'None'
        dsr_speed = row[3] or 'None'
        enr_prov = row[6] or 'None'
        enr_speed = row[7] or 'None'
        print(f"{site:<8} | {purpose:<9} | {dsr_prov:<18} | {dsr_speed:<18} | {enr_prov:<17} | {enr_speed}")
    
    # 2. Show how provider names differ
    print("\n\n2. Provider Name Mismatches\n")
    
    cursor.execute("""
        WITH provider_comparison AS (
            SELECT DISTINCT
                c.provider_name as dsr_provider,
                mi.device_notes,
                ec.wan1_provider as enriched_provider,
                CASE 
                    WHEN mi.device_notes LIKE '%WAN 1%Comcast%' THEN 'Has Comcast in notes'
                    WHEN mi.device_notes LIKE '%WAN 1%Comcast Workplace%' THEN 'Has Comcast Workplace in notes'
                    ELSE 'Other'
                END as notes_check
            FROM circuits c
            JOIN meraki_inventory mi ON c.ip_address_start = mi.wan1_ip
            JOIN enriched_circuits ec ON ec.network_name = mi.network_name
            WHERE c.provider_name LIKE 'Comcast%'
            AND c.status = 'Enabled'
        )
        SELECT 
            dsr_provider,
            enriched_provider,
            notes_check,
            COUNT(*) as count
        FROM provider_comparison
        GROUP BY dsr_provider, enriched_provider, notes_check
        ORDER BY count DESC
    """)
    
    print("DSR Provider        | Enriched Provider  | Notes Check                    | Count")
    print("-" * 85)
    for row in cursor.fetchall():
        print(f"{row[0]:<18} | {row[1]:<17} | {row[2]:<30} | {row[3]}")
    
    # 3. Show the matching logic problem
    print("\n\n3. WAN Port Assignment Logic Issues\n")
    
    cursor.execute("""
        SELECT 
            ec.network_name,
            mi.wan1_ip,
            mi.wan2_ip,
            c1.provider_name as ip1_dsr_provider,
            c1.circuit_purpose as ip1_purpose,
            c2.provider_name as ip2_dsr_provider,
            c2.circuit_purpose as ip2_purpose,
            ec.wan1_provider as enriched_wan1_provider,
            ec.wan2_provider as enriched_wan2_provider,
            SUBSTRING(mi.device_notes, 1, 100) as notes_preview
        FROM enriched_circuits ec
        JOIN meraki_inventory mi ON mi.network_name = ec.network_name
        LEFT JOIN circuits c1 ON c1.ip_address_start = mi.wan1_ip AND c1.status = 'Enabled'
        LEFT JOIN circuits c2 ON c2.ip_address_start = mi.wan2_ip AND c2.status = 'Enabled'
        WHERE ec.network_name IN ('CAN_00', 'CAN 25')
    """)
    
    for row in cursor.fetchall():
        print(f"\nNetwork: {row[0]}")
        print(f"  WAN1 IP: {row[1]} -> DSR: {row[3]} ({row[4]})")
        print(f"  WAN2 IP: {row[2]} -> DSR: {row[5]} ({row[6]})")
        print(f"  Enriched WAN1: {row[7]}")
        print(f"  Enriched WAN2: {row[8]}")
        print(f"  Notes: {row[9]}...")
    
    # 4. Show what happens when there's no IP match
    print("\n\n4. When IP Matching Fails\n")
    
    cursor.execute("""
        SELECT 
            c.site_name,
            c.circuit_purpose,
            c.provider_name,
            c.ip_address_start,
            EXISTS (
                SELECT 1 FROM meraki_inventory mi 
                WHERE c.ip_address_start IN (mi.wan1_ip, mi.wan2_ip)
            ) as ip_found_in_meraki
        FROM circuits c
        WHERE c.status = 'Enabled'
        AND c.provider_name LIKE 'Comcast%'
        AND c.site_name IN (
            SELECT REPLACE(network_name, '_', '') 
            FROM enriched_circuits 
            WHERE wan1_speed LIKE '% M' OR wan2_speed LIKE '% M'
        )
        LIMIT 10
    """)
    
    print("Site     | Purpose   | Provider            | IP              | IP in Meraki?")
    print("-" * 75)
    for row in cursor.fetchall():
        print(f"{row[0]:<8} | {row[1]:<9} | {row[2]:<18} | {row[3]:<15} | {row[4]}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    trace_enrichment_logic()