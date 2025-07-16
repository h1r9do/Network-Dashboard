#!/usr/bin/env python3
"""
Analyze specifically the corrupted entries from the bad speed circuits
"""

import psycopg2
import pandas as pd
import os

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def analyze_corrupted_entries():
    """Focus on entries with corrupted speed format"""
    
    # Read the CSV output
    csv_path = '/usr/local/bin/bad_speed_circuits_analysis_20250709_103510.csv'
    df = pd.read_csv(csv_path)
    
    # Filter for corrupted speeds (format "XXX.X M" instead of "XXX.XM x XXX.XM")
    corrupted_df = df[df['Enriched Speed'].str.contains(r'^\d+\.?\d* M$', na=False)]
    
    print(f"=== CORRUPTED SPEED ANALYSIS ===")
    print(f"Total corrupted entries: {len(corrupted_df)}")
    print(f"Out of total entries: {len(df)}")
    print(f"Corruption rate: {len(corrupted_df)/len(df)*100:.1f}%\n")
    
    # Group by site to see patterns
    print("=== SITES WITH CORRUPTED SPEEDS ===\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get unique sites with corrupted speeds
    corrupted_sites = corrupted_df['Site Name'].unique()
    
    for site in sorted(corrupted_sites)[:20]:  # First 20 sites
        site_data = corrupted_df[corrupted_df['Site Name'] == site]
        
        print(f"\n{site}:")
        print("-" * 80)
        
        for _, row in site_data.iterrows():
            purpose = row['Circuit Purpose']
            
            # Query for more details
            cursor.execute("""
                SELECT 
                    c.site_name,
                    c.circuit_purpose,
                    c.provider_name as dsr_provider,
                    c.details_ordered_service_speed as dsr_speed,
                    c.ip_address_start,
                    mi.wan1_ip,
                    mi.wan2_ip,
                    CASE 
                        WHEN c.ip_address_start = mi.wan1_ip THEN 'Matched to WAN1'
                        WHEN c.ip_address_start = mi.wan2_ip THEN 'Matched to WAN2'
                        ELSE 'No IP Match'
                    END as ip_match_status,
                    SUBSTRING(mi.device_notes, 1, 300) as notes
                FROM circuits c
                LEFT JOIN meraki_inventory mi ON (
                    mi.network_name = c.site_name OR
                    mi.network_name = REPLACE(c.site_name, ' ', '_')
                )
                WHERE c.site_name = %s 
                AND c.circuit_purpose = %s
                AND c.status = 'Enabled'
                LIMIT 1
            """, (site, purpose))
            
            result = cursor.fetchone()
            
            if result:
                print(f"\n  {purpose} Circuit:")
                print(f"    DSR Provider: {result[2]}")
                print(f"    DSR Speed: {result[3]}")
                print(f"    DSR IP: {result[4]}")
                print(f"    Enriched Provider: {row['Enriched Provider']}")
                print(f"    Enriched Speed: {row['Enriched Speed']} ← CORRUPTED")
                print(f"    IP Match Status: {result[7]}")
                
                if result[8]:
                    # Parse notes to show what's in Meraki
                    notes = result[8]
                    if 'WAN' in notes:
                        print(f"    Meraki Notes Preview:")
                        # Extract WAN1 info
                        import re
                        wan1_match = re.search(r'WAN\s*1\s*([^W]*)', notes, re.IGNORECASE)
                        if wan1_match:
                            wan1_info = wan1_match.group(1).strip()
                            # Clean up the info
                            wan1_lines = wan1_info.split('\n')[:3]  # First 3 lines after WAN 1
                            for line in wan1_lines:
                                if line.strip():
                                    print(f"      {line.strip()}")
    
    # Provider analysis
    print("\n\n=== PROVIDER CORRUPTION ANALYSIS ===\n")
    provider_stats = corrupted_df.groupby('Enriched Provider').size().sort_values(ascending=False)
    
    print("Provider                        | Corrupted Count")
    print("-" * 50)
    for provider, count in provider_stats.items():
        print(f"{provider:<30} | {count}")
    
    # Check if DSR data exists
    print("\n\n=== DSR DATA AVAILABILITY ===\n")
    has_dsr_speed = corrupted_df['DSR Speed'].notna().sum()
    no_dsr_speed = corrupted_df['DSR Speed'].isna().sum()
    
    print(f"Corrupted entries WITH DSR speed data: {has_dsr_speed}")
    print(f"Corrupted entries WITHOUT DSR speed data: {no_dsr_speed}")
    
    # Pattern analysis
    print("\n\n=== CORRUPTION PATTERNS ===\n")
    
    # Check if corruption happens when DSR provider != Enriched provider
    provider_mismatch = corrupted_df[
        (corrupted_df['DSR Provider'].notna()) & 
        (corrupted_df['DSR Provider'] != corrupted_df['Enriched Provider'])
    ]
    
    print(f"Corrupted entries where DSR Provider != Enriched Provider: {len(provider_mismatch)}")
    print(f"That's {len(provider_mismatch)/len(corrupted_df)*100:.1f}% of corrupted entries")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    analyze_corrupted_entries()