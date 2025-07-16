#!/usr/bin/env python3
"""
Query database for exact circuits from the web page export
Show backend data for each WAN1 circuit
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

def analyze_exact_circuits():
    """Show backend database data for exact circuits from the export"""
    
    # Read the Excel file (web page export)
    excel_path = '/tmp/bad_speed_circuits_filtered.xlsx'
    df = pd.read_excel(excel_path)
    print(f"=== BACKEND DATABASE ANALYSIS ===")
    print(f"Analyzing {len(df)} circuits from web page export\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Analyze each circuit
    for idx, row in df.iterrows():
        site_name = row.get('Site Name', '')
        if not site_name:
            continue
            
        print(f"\n{'='*100}")
        print(f"{idx+1}. {site_name} (WAN1)")
        print('='*100)
        
        # Query all relevant backend data for this site
        cursor.execute("""
            -- Get all data for this specific site
            SELECT 
                -- Circuits table data
                'circuits' as source_table,
                c.site_name,
                c.circuit_purpose,
                c.provider_name,
                c.details_ordered_service_speed,
                c.status,
                c.ip_address_start,
                NULL::text as wan1_provider,
                NULL::text as wan1_speed,
                NULL::text as device_notes,
                NULL::text as wan1_ip,
                NULL::text as wan1_arin_provider
            FROM circuits c
            WHERE c.site_name = %s 
            AND c.status = 'Enabled'
            AND c.circuit_purpose = 'Primary'
            
            UNION ALL
            
            -- Get enriched circuits data
            SELECT 
                'enriched_circuits' as source_table,
                ec.network_name as site_name,
                'Primary' as circuit_purpose,
                NULL::text as provider_name,
                NULL::text as details_ordered_service_speed,
                NULL::text as status,
                NULL::text as ip_address_start,
                ec.wan1_provider,
                ec.wan1_speed,
                NULL::text as device_notes,
                NULL::text as wan1_ip,
                NULL::text as wan1_arin_provider
            FROM enriched_circuits ec
            WHERE (ec.network_name = %s OR ec.network_name = REPLACE(%s, ' ', '_'))
            
            UNION ALL
            
            -- Get Meraki inventory data
            SELECT 
                'meraki_inventory' as source_table,
                mi.network_name as site_name,
                NULL::text as circuit_purpose,
                NULL::text as provider_name,
                NULL::text as details_ordered_service_speed,
                NULL::text as status,
                NULL::text as ip_address_start,
                NULL::text as wan1_provider,
                NULL::text as wan1_speed,
                mi.device_notes,
                mi.wan1_ip,
                mi.wan1_arin_provider
            FROM meraki_inventory mi
            WHERE (mi.network_name = %s OR mi.network_name = REPLACE(%s, ' ', '_'))
            AND mi.device_model LIKE 'MX%'
            
            ORDER BY source_table
        """, (site_name, site_name, site_name, site_name, site_name))
        
        results = cursor.fetchall()
        
        # Organize data by source
        circuits_data = None
        enriched_data = None
        meraki_data = None
        
        for result in results:
            source = result[0]
            if source == 'circuits':
                circuits_data = result
            elif source == 'enriched_circuits':
                enriched_data = result
            elif source == 'meraki_inventory':
                meraki_data = result
        
        # Display backend data
        print("\nCIRCUITS TABLE:")
        if circuits_data:
            print(f"  Site Name: {circuits_data[1]}")
            print(f"  Provider: {circuits_data[3]}")
            print(f"  Speed: {circuits_data[4]}")
            print(f"  Status: {circuits_data[5]}")
            print(f"  IP: {circuits_data[6]}")
        else:
            print("  NO ENABLED PRIMARY CIRCUIT FOUND")
        
        print("\nENRICHED_CIRCUITS TABLE:")
        if enriched_data:
            print(f"  Network Name: {enriched_data[1]}")
            print(f"  WAN1 Provider: {enriched_data[7]}")
            print(f"  WAN1 Speed: {enriched_data[8]}")
        else:
            print("  NO ENRICHED DATA FOUND")
        
        print("\nMERAKI_INVENTORY TABLE:")
        if meraki_data:
            print(f"  Network Name: {meraki_data[1]}")
            print(f"  WAN1 IP: {meraki_data[10]}")
            print(f"  WAN1 ARIN Provider: {meraki_data[11]}")
            print(f"  Device Notes (first 200 chars):")
            if meraki_data[9]:
                notes = meraki_data[9][:200]
                print(f"    {notes}...")
                # Extract speed from notes
                import re
                speed_match = re.search(r'WAN\s*1[^W]*?(\d+(?:\.\d+)?M?\s*x\s*\d+(?:\.\d+)?M?)', notes, re.IGNORECASE)
                if speed_match:
                    print(f"  Speed in notes: {speed_match.group(1)}")
        else:
            print("  NO MERAKI DATA FOUND")
    
    # Summary query
    print(f"\n\n{'='*100}")
    print("SUMMARY - Speed Format Issues")
    print('='*100)
    
    # Get unique sites
    unique_sites = df['Site Name'].dropna().unique().tolist()
    
    # Create a simpler summary
    corrupted_count = 0
    total_with_circuits = 0
    total_with_enriched = 0
    
    for site in unique_sites:
        cursor.execute("""
            SELECT 
                c.details_ordered_service_speed as circuits_speed,
                ec.wan1_speed as enriched_speed
            FROM circuits c
            FULL OUTER JOIN enriched_circuits ec ON (
                ec.network_name = c.site_name OR 
                ec.network_name = REPLACE(c.site_name, ' ', '_')
            )
            WHERE (c.site_name = %s OR ec.network_name = %s OR ec.network_name = REPLACE(%s, ' ', '_'))
            AND (c.status = 'Enabled' OR c.status IS NULL)
            AND (c.circuit_purpose = 'Primary' OR c.circuit_purpose IS NULL)
            LIMIT 1
        """, (site, site, site))
        
        result = cursor.fetchone()
        if result:
            circuits_speed, enriched_speed = result
            if circuits_speed:
                total_with_circuits += 1
            if enriched_speed:
                total_with_enriched += 1
            if circuits_speed and 'x' in str(circuits_speed) and enriched_speed and 'x' not in str(enriched_speed) and ' M' in str(enriched_speed):
                corrupted_count += 1
    
    print(f"\nTotal unique sites analyzed: {len(unique_sites)}")
    print(f"Sites with corrupted speed format: {corrupted_count}")
    print(f"Sites with circuits table data: {total_with_circuits}")
    print(f"Sites with enriched table data: {total_with_enriched}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    analyze_exact_circuits()