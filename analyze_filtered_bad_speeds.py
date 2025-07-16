#!/usr/bin/env python3
"""
Detailed analysis of the filtered bad speed circuits
"""

import psycopg2
import pandas as pd

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def analyze_filtered_bad_speeds():
    """Analyze the filtered bad speed circuits in detail"""
    
    # Read the output CSV
    csv_path = '/usr/local/bin/bad_speed_circuits_analysis_20250709_104339.csv'
    df = pd.read_csv(csv_path)
    
    print("=== FILTERED BAD SPEED CIRCUITS ANALYSIS ===\n")
    print(f"Total circuits analyzed: {len(df)}")
    
    # Filter for corrupted speeds
    corrupted_df = df[df['Enriched Speed'].str.contains(r'^\d+\.?\d* M$', na=False)]
    print(f"Circuits with corrupted speed format: {len(corrupted_df)}")
    print(f"Corruption rate: {len(corrupted_df)/len(df)*100:.1f}%\n")
    
    # Analyze patterns
    print("=== CORRUPTION PATTERNS ===\n")
    
    # 1. Check provider mismatches
    provider_mismatch = corrupted_df[
        (corrupted_df['Circuits Table Provider'] != corrupted_df['Enriched Provider']) &
        (corrupted_df['Circuits Table Provider'].notna())
    ]
    
    print(f"1. Provider Mismatches:")
    print(f"   Corrupted entries where Circuit Provider != Enriched Provider: {len(provider_mismatch)}")
    print(f"   That's {len(provider_mismatch)/len(corrupted_df)*100:.1f}% of corrupted entries\n")
    
    # Show examples
    if len(provider_mismatch) > 0:
        print("   Examples:")
        for idx, row in provider_mismatch.head(5).iterrows():
            print(f"   - {row['Site Name']}: '{row['Circuits Table Provider']}' → '{row['Enriched Provider']}'")
    
    # 2. Check if DSR data exists
    print(f"\n2. DSR Data Availability:")
    has_dsr = corrupted_df['DSR Speed'].notna().sum()
    no_dsr = corrupted_df['DSR Speed'].isna().sum()
    print(f"   With DSR data: {has_dsr} ({has_dsr/len(corrupted_df)*100:.1f}%)")
    print(f"   Without DSR data: {no_dsr} ({no_dsr/len(corrupted_df)*100:.1f}%)")
    
    # 3. Check speed format in circuits table vs enriched
    print(f"\n3. Speed Format Comparison:")
    correct_format_in_circuits = df['Circuits Table Speed'].str.contains(r'\d+\.?\d*M\s*x\s*\d+\.?\d*M', na=False).sum()
    print(f"   Circuits with correct format in circuits table: {correct_format_in_circuits}")
    print(f"   But corrupted in enriched table: {len(corrupted_df)}")
    
    # 4. Most affected providers
    print(f"\n4. Most Affected Providers (by corruption count):")
    provider_counts = corrupted_df['Enriched Provider'].value_counts().head(10)
    for provider, count in provider_counts.items():
        # Get total for this provider
        total = len(df[df['Enriched Provider'] == provider])
        pct = count/total*100 if total > 0 else 0
        print(f"   {provider}: {count} corrupted out of {total} ({pct:.1f}%)")
    
    # 5. Sample detailed analysis
    print(f"\n=== DETAILED EXAMPLES ===\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get 5 examples with different patterns
    examples = corrupted_df.head(5)
    
    for idx, row in examples.iterrows():
        site = row['Site Name']
        purpose = row['Circuit Purpose']
        
        print(f"\n{site} ({purpose}):")
        print(f"  Circuits Table: {row['Circuits Table Provider']} - '{row['Circuits Table Speed']}'")
        print(f"  Enriched Table: {row['Enriched Provider']} - '{row['Enriched Speed']}' ← CORRUPTED")
        
        if pd.notna(row['DSR Speed']):
            print(f"  DSR Data: {row['DSR Provider']} - '{row['DSR Speed']}'")
        else:
            print(f"  DSR Data: NOT AVAILABLE")
        
        # Query for the enrichment process details
        cursor.execute("""
            SELECT 
                mi.network_name,
                mi.wan1_ip,
                mi.wan2_ip,
                mi.wan1_arin_provider,
                mi.wan2_arin_provider,
                SUBSTRING(mi.device_notes, 1, 200) as notes
            FROM meraki_inventory mi
            WHERE mi.network_name = %s OR mi.network_name = REPLACE(%s, ' ', '_')
            LIMIT 1
        """, (site, site))
        
        meraki_data = cursor.fetchone()
        if meraki_data:
            print(f"  Meraki IPs: WAN1={meraki_data[1]}, WAN2={meraki_data[2]}")
            print(f"  ARIN Providers: WAN1={meraki_data[3]}, WAN2={meraki_data[4]}")
            if meraki_data[5]:
                # Extract speed from notes
                import re
                speed_match = re.search(r'(\d+(?:\.\d+)?M?\s*x\s*\d+(?:\.\d+)?M?)', meraki_data[5])
                if speed_match:
                    print(f"  Speed in Meraki notes: '{speed_match.group(1)}'")
    
    cursor.close()
    conn.close()
    
    # Summary
    print(f"\n=== SUMMARY ===\n")
    print(f"Out of {len(df)} circuits in the filtered bad speed file:")
    print(f"- {len(corrupted_df)} have corrupted speed format (missing upload speed)")
    print(f"- {len(provider_mismatch)} have provider mismatches")
    print(f"- {no_dsr} have no DSR data to reference")
    print(f"- Comcast and AT&T Broadband II are most affected")
    print(f"\nThe enrichment process is corrupting the speed format when:")
    print(f"1. Provider names don't match exactly (normalization issue)")
    print(f"2. No DSR data exists for reference")
    print(f"3. Complex matching logic is applied instead of simple data copying")

if __name__ == "__main__":
    analyze_filtered_bad_speeds()