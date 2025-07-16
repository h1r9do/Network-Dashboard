#!/usr/bin/env python3
"""
Analyze the pattern of speed corruption to understand why some are corrupted and others aren't
"""

import psycopg2
import re

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def analyze_corruption_pattern():
    """Deep dive into corruption patterns"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("=== ANALYZING CORRUPTION PATTERNS ===\n")
    
    # Pattern 1: Check if corruption happens when DSR data doesn't match
    print("1. Checking DSR data availability for corrupted vs non-corrupted sites...")
    
    cursor.execute("""
        WITH corrupted_sites AS (
            SELECT network_name, 
                   wan1_speed LIKE '%% M' as wan1_corrupted,
                   wan2_speed LIKE '%% M' as wan2_corrupted
            FROM enriched_circuits
            WHERE wan1_speed LIKE '%% M' OR wan2_speed LIKE '%% M'
        )
        SELECT 
            cs.network_name,
            cs.wan1_corrupted,
            cs.wan2_corrupted,
            c1.details_ordered_service_speed as dsr_primary_speed,
            c2.details_ordered_service_speed as dsr_secondary_speed,
            mi.device_notes IS NOT NULL as has_meraki_notes
        FROM corrupted_sites cs
        LEFT JOIN circuits c1 ON c1.site_name = REPLACE(cs.network_name, '_', '')
            AND c1.circuit_purpose = 'Primary' AND c1.status = 'Enabled'
        LEFT JOIN circuits c2 ON c2.site_name = REPLACE(cs.network_name, '_', '')
            AND c2.circuit_purpose = 'Secondary' AND c2.status = 'Enabled'
        LEFT JOIN meraki_inventory mi ON mi.network_name = cs.network_name
        LIMIT 20
    """)
    
    dsr_match_stats = {
        'corrupted_with_dsr': 0,
        'corrupted_without_dsr': 0,
        'has_meraki_notes': 0
    }
    
    print("Sample of corrupted sites and their DSR data:")
    for row in cursor.fetchall():
        network = row[0]
        wan1_corrupted = row[1]
        wan2_corrupted = row[2]
        dsr_primary = row[3]
        dsr_secondary = row[4]
        has_notes = row[5]
        
        print(f"\n{network}:")
        if wan1_corrupted:
            print(f"  WAN1 corrupted - DSR Primary: {dsr_primary or 'NO DSR DATA'}")
            if dsr_primary:
                dsr_match_stats['corrupted_with_dsr'] += 1
            else:
                dsr_match_stats['corrupted_without_dsr'] += 1
        if wan2_corrupted:
            print(f"  WAN2 corrupted - DSR Secondary: {dsr_secondary or 'NO DSR DATA'}")
        if has_notes:
            dsr_match_stats['has_meraki_notes'] += 1
    
    # Pattern 2: Check specific examples to understand the issue
    print("\n\n2. Examining specific cases in detail...")
    
    # Look at CAN_00 specifically
    cursor.execute("""
        SELECT 
            ec.network_name,
            ec.wan1_provider, ec.wan1_speed,
            ec.wan2_provider, ec.wan2_speed,
            c1.site_name as dsr_site_primary,
            c1.provider_name as dsr_provider_primary,
            c1.details_ordered_service_speed as dsr_speed_primary,
            c2.site_name as dsr_site_secondary,
            c2.provider_name as dsr_provider_secondary,
            c2.details_ordered_service_speed as dsr_speed_secondary,
            mi.wan1_ip, mi.wan2_ip,
            SUBSTRING(mi.device_notes, 1, 100) as notes_preview
        FROM enriched_circuits ec
        LEFT JOIN circuits c1 ON c1.site_name IN ('CAN00', 'CAN_00', REPLACE(ec.network_name, '_', ''))
            AND c1.circuit_purpose = 'Primary' AND c1.status = 'Enabled'
        LEFT JOIN circuits c2 ON c2.site_name IN ('CAN00', 'CAN_00', REPLACE(ec.network_name, '_', ''))
            AND c2.circuit_purpose = 'Secondary' AND c2.status = 'Enabled'
        LEFT JOIN meraki_inventory mi ON mi.network_name = ec.network_name
        WHERE ec.network_name = 'CAN_00'
    """)
    
    row = cursor.fetchone()
    if row:
        print("\nDetailed analysis of CAN_00:")
        print(f"Network Name: {row[0]}")
        print(f"\nEnriched Circuits Data:")
        print(f"  WAN1: {row[1]} - Speed: '{row[2]}'")
        print(f"  WAN2: {row[3]} - Speed: '{row[4]}'")
        print(f"\nDSR Primary Circuit:")
        print(f"  Site: {row[5]}, Provider: {row[6]}, Speed: '{row[7]}'")
        print(f"\nDSR Secondary Circuit:")
        print(f"  Site: {row[8]}, Provider: {row[9]}, Speed: '{row[10]}'")
        print(f"\nMeraki IPs:")
        print(f"  WAN1: {row[11]}, WAN2: {row[12]}")
        print(f"\nDevice Notes Preview: {row[13]}...")
    
    # Pattern 3: Check if there's a difference in how data is stored
    print("\n\n3. Checking for patterns in speed values...")
    
    cursor.execute("""
        SELECT 
            wan1_speed,
            COUNT(*) as count
        FROM enriched_circuits
        WHERE wan1_speed LIKE '%% M'
        GROUP BY wan1_speed
        ORDER BY count DESC
        LIMIT 10
    """)
    
    print("\nMost common corrupted speed values:")
    for row in cursor.fetchall():
        print(f"  '{row[0]}' - {row[1]} occurrences")
    
    # Pattern 4: Check the exact format differences
    print("\n\n4. Comparing corrupted vs non-corrupted formats...")
    
    cursor.execute("""
        SELECT 
            network_name,
            wan1_speed,
            LENGTH(wan1_speed) as speed_length,
            wan1_speed LIKE '%% M' as has_space_m,
            wan1_speed LIKE '%%x%%' as has_x
        FROM enriched_circuits
        WHERE wan1_speed IS NOT NULL 
        AND wan1_speed NOT IN ('Cell', 'Satellite', '')
        AND (wan1_speed LIKE '%% M' OR wan1_speed LIKE '%%x%%')
        LIMIT 10
    """)
    
    print("\nFormat comparison:")
    print("Network            | Speed              | Length | Space+M | Has 'x'")
    print("-" * 70)
    for row in cursor.fetchall():
        print(f"{row[0]:<17} | {row[1]:<18} | {row[2]:<6} | {row[3]:<7} | {row[4]}")
    
    # Pattern 5: Check if specific providers are more affected
    print("\n\n5. Provider-specific corruption analysis...")
    
    cursor.execute("""
        SELECT 
            wan1_provider,
            COUNT(*) FILTER (WHERE wan1_speed LIKE '%% M') as corrupted,
            COUNT(*) FILTER (WHERE wan1_speed LIKE '%%x%%') as correct,
            COUNT(*) as total
        FROM enriched_circuits
        WHERE wan1_speed IS NOT NULL 
        AND wan1_speed NOT IN ('Cell', 'Satellite', '')
        GROUP BY wan1_provider
        HAVING COUNT(*) > 5
        ORDER BY COUNT(*) FILTER (WHERE wan1_speed LIKE '%% M') DESC
        LIMIT 15
    """)
    
    print("\nProvider corruption statistics:")
    print("Provider                        | Corrupted | Correct | Total | % Corrupted")
    print("-" * 80)
    for row in cursor.fetchall():
        provider = row[0] or "Unknown"
        corrupted = row[1]
        correct = row[2]
        total = row[3]
        percentage = (corrupted / total * 100) if total > 0 else 0
        print(f"{provider:<30} | {corrupted:>9} | {correct:>7} | {total:>5} | {percentage:>10.1f}%")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    analyze_corruption_pattern()