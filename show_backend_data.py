#!/usr/bin/env python3
"""
Show backend database data for circuits from web export
"""

import psycopg2
import pandas as pd
import re

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def show_backend_data():
    """Show backend data for each circuit"""
    
    # Read the Excel file
    excel_path = '/tmp/bad_speed_circuits_filtered.xlsx'
    df = pd.read_excel(excel_path)
    print(f"=== BACKEND DATABASE DATA FOR BAD SPEED CIRCUITS ===")
    print(f"Showing database content for {len(df)} circuits\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Process each site
    for idx, row in df.head(20).iterrows():  # First 20 for readability
        site_name = row.get('Site Name', '')
        if not site_name:
            continue
            
        print(f"\n{'='*80}")
        print(f"{idx+1}. {site_name}")
        print('='*80)
        
        # 1. Circuits table data
        cursor.execute("""
            SELECT 
                provider_name,
                details_ordered_service_speed,
                status,
                ip_address_start,
                circuit_purpose
            FROM circuits
            WHERE site_name = %s 
            AND status = 'Enabled'
            AND circuit_purpose = 'Primary'
        """, (site_name,))
        
        circuits_data = cursor.fetchone()
        
        print("\nCIRCUITS TABLE (Primary/Enabled):")
        if circuits_data:
            print(f"  Provider: {circuits_data[0]}")
            print(f"  Speed: {circuits_data[1]}")
            print(f"  Status: {circuits_data[2]}")
            print(f"  IP: {circuits_data[3]}")
        else:
            print("  NO DATA FOUND")
        
        # 2. Enriched circuits data
        cursor.execute("""
            SELECT 
                wan1_provider,
                wan1_speed,
                wan1_confirmed,
                network_name
            FROM enriched_circuits
            WHERE network_name = %s OR network_name = %s
        """, (site_name, site_name.replace(' ', '_')))
        
        enriched_data = cursor.fetchone()
        
        print("\nENRICHED_CIRCUITS TABLE:")
        if enriched_data:
            print(f"  Network Name: {enriched_data[3]}")
            print(f"  WAN1 Provider: {enriched_data[0]}")
            print(f"  WAN1 Speed: {enriched_data[1]}")
            print(f"  WAN1 Confirmed: {enriched_data[2]}")
        else:
            print("  NO DATA FOUND")
        
        # 3. Meraki inventory data
        cursor.execute("""
            SELECT 
                network_name,
                wan1_ip,
                wan1_arin_provider,
                device_notes
            FROM meraki_inventory
            WHERE (network_name = %s OR network_name = %s)
            AND device_model LIKE 'MX%%'
        """, (site_name, site_name.replace(' ', '_')))
        
        meraki_data = cursor.fetchone()
        
        print("\nMERAKI_INVENTORY TABLE:")
        if meraki_data:
            print(f"  Network Name: {meraki_data[0]}")
            print(f"  WAN1 IP: {meraki_data[1]}")
            print(f"  WAN1 ARIN Provider: {meraki_data[2]}")
            if meraki_data[3]:
                # Extract WAN1 info from notes
                notes = meraki_data[3]
                wan1_match = re.search(r'WAN\s*1[^W]*?([^\n]+)\n([^\n]+)', notes, re.IGNORECASE)
                if wan1_match:
                    print(f"  Notes WAN1 Info:")
                    print(f"    Provider: {wan1_match.group(1).strip()}")
                    print(f"    Speed: {wan1_match.group(2).strip()}")
        else:
            print("  NO DATA FOUND")
        
        # Check for speed corruption
        if circuits_data and enriched_data:
            circuits_speed = circuits_data[1]
            enriched_speed = enriched_data[1]
            if circuits_speed and 'x' in str(circuits_speed) and enriched_speed and 'x' not in str(enriched_speed):
                print("\n*** SPEED CORRUPTION DETECTED ***")
                print(f"    Circuits table has: {circuits_speed}")
                print(f"    Enriched table has: {enriched_speed}")
    
    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print('='*80)
    
    total_sites = len(df['Site Name'].dropna().unique())
    
    # Count corrupted speeds
    cursor.execute("""
        SELECT COUNT(DISTINCT c.site_name)
        FROM circuits c
        JOIN enriched_circuits ec ON (
            ec.network_name = c.site_name OR 
            ec.network_name = REPLACE(c.site_name, ' ', '_')
        )
        WHERE c.status = 'Enabled'
        AND c.circuit_purpose = 'Primary'
        AND c.details_ordered_service_speed LIKE '%%x%%'
        AND ec.wan1_speed NOT LIKE '%%x%%'
        AND ec.wan1_speed LIKE '%% M'
        AND c.site_name IN %s
    """, (tuple(df['Site Name'].dropna().unique()),))
    
    corrupted_count = cursor.fetchone()[0]
    
    print(f"Total sites in file: {total_sites}")
    print(f"Sites with speed corruption in database: {corrupted_count}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    show_backend_data()