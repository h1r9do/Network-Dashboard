#!/usr/bin/env python3
"""
Check enriched_circuits table data for bad speed circuits
This is where the web page gets its data from
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

def check_enriched_data():
    """Show what's actually in enriched_circuits table"""
    
    # Read the Excel file
    excel_path = '/tmp/bad_speed_circuits_filtered.xlsx'
    df = pd.read_excel(excel_path)
    print(f"=== ENRICHED_CIRCUITS TABLE DATA (SOURCE FOR WEB PAGE) ===")
    print(f"Checking {len(df)} circuits from your export\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check a sample of sites
    for idx, row in df.head(20).iterrows():
        site_name = row.get('Site Name', '')
        if not site_name:
            continue
            
        print(f"\n{idx+1}. {site_name}")
        print("-" * 60)
        
        # Query enriched_circuits table (this is what the web page uses)
        cursor.execute("""
            SELECT 
                network_name,
                wan1_provider,
                wan1_speed,
                wan1_circuit_role,
                wan1_confirmed,
                wan2_provider,
                wan2_speed,
                wan2_circuit_role,
                wan2_confirmed,
                device_tags,
                last_updated
            FROM enriched_circuits
            WHERE network_name = %s OR network_name = %s
        """, (site_name, site_name.replace(' ', '_')))
        
        result = cursor.fetchone()
        
        if result:
            print(f"  Network Name: {result[0]}")
            print(f"  WAN1 Provider: {result[1]}")
            print(f"  WAN1 Speed: {result[2]} {'← CORRUPTED' if result[2] and ' M' in result[2] and ' x ' not in result[2] else ''}")
            print(f"  WAN1 Role: {result[3]}")
            print(f"  WAN1 Confirmed: {result[4]}")
            print(f"  WAN2 Provider: {result[5]}")
            print(f"  WAN2 Speed: {result[6]}")
            print(f"  Device Tags: {result[9]}")
            print(f"  Last Updated: {result[10]}")
        else:
            print("  NOT FOUND IN ENRICHED_CIRCUITS TABLE")
    
    # Summary of corruption
    print("\n\n" + "="*60)
    print("CORRUPTION SUMMARY")
    print("="*60)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN wan1_speed LIKE '%% M' THEN 1 END) as wan1_corrupted,
            COUNT(CASE WHEN wan2_speed LIKE '%% M' THEN 1 END) as wan2_corrupted
        FROM enriched_circuits
        WHERE network_name IN %s OR network_name IN %s
    """, (tuple(df['Site Name'].dropna().unique()), 
          tuple([s.replace(' ', '_') for s in df['Site Name'].dropna().unique()])))
    
    summary = cursor.fetchone()
    if summary:
        print(f"Total sites found: {summary[0]}")
        print(f"WAN1 corrupted speeds: {summary[1]}")
        print(f"WAN2 corrupted speeds: {summary[2]}")
    
    # Show the view query that the web page uses
    print("\n\n" + "="*60)
    print("HOW THE WEB PAGE GETS DATA")
    print("="*60)
    print("The /dsrcircuits page queries the 'v_circuit_summary' view which:")
    print("1. Pulls ALL data from enriched_circuits table")
    print("2. Only joins to circuits table for cost information")
    print("3. Filters out hub/lab/test sites")
    print("\nSo the speed corruption you see on the web page comes directly")
    print("from the enriched_circuits table, NOT from the circuits table!")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_enriched_data()