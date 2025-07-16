#!/usr/bin/env python3
"""
Export enriched_circuits data for specific circuits from the Excel file
Match on site name and extract both WAN1 and WAN2 data
"""

import psycopg2
import pandas as pd
from datetime import datetime

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def export_enriched_circuits():
    """Export enriched circuits data matching the Excel file"""
    
    # Read the Excel file
    excel_path = '/tmp/bad_speed_circuits_filtered.xlsx'
    df = pd.read_excel(excel_path)
    print(f"=== ENRICHED CIRCUITS EXPORT ===")
    print(f"Processing {len(df)} circuits from Excel file\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Prepare export data
    export_data = []
    
    # Get unique sites from Excel
    unique_sites = df['Site Name'].dropna().unique()
    
    for site_name in unique_sites:
        # Query enriched_circuits for this site
        cursor.execute("""
            SELECT 
                network_name,
                -- WAN1 data
                wan1_provider,
                wan1_speed,
                wan1_circuit_role,
                wan1_confirmed,
                -- WAN2 data
                wan2_provider,
                wan2_speed,
                wan2_circuit_role,
                wan2_confirmed,
                -- Additional data
                device_tags,
                last_updated
            FROM enriched_circuits
            WHERE network_name = %s OR network_name = %s
        """, (site_name, site_name.replace(' ', '_')))
        
        result = cursor.fetchone()
        
        if result:
            # Add WAN1 data
            wan1_data = {
                'Site Name': result[0],
                'WAN Port': 'WAN1',
                'Provider': result[1],
                'Speed': result[2],
                'Circuit Role': result[3],
                'Confirmed': result[4],
                'Speed Status': 'CORRUPTED' if result[2] and ' M' in result[2] and ' x ' not in result[2] else 'OK',
                'Device Tags': result[9],
                'Last Updated': result[10]
            }
            export_data.append(wan1_data)
            
            # Add WAN2 data
            wan2_data = {
                'Site Name': result[0],
                'WAN Port': 'WAN2',
                'Provider': result[5],
                'Speed': result[6],
                'Circuit Role': result[7],
                'Confirmed': result[8],
                'Speed Status': 'CORRUPTED' if result[6] and ' M' in result[6] and ' x ' not in result[6] else 'OK',
                'Device Tags': result[9],
                'Last Updated': result[10]
            }
            export_data.append(wan2_data)
    
    # Also query for additional backend data to help with analysis
    print("Adding additional backend data for analysis...\n")
    
    # Create a comprehensive export with all relevant data
    comprehensive_data = []
    
    for site_name in unique_sites:
        cursor.execute("""
            WITH site_data AS (
                SELECT %s as site_name
            )
            SELECT 
                sd.site_name,
                -- Enriched data
                ec.network_name,
                ec.wan1_provider as enriched_wan1_provider,
                ec.wan1_speed as enriched_wan1_speed,
                ec.wan1_circuit_role,
                ec.wan2_provider as enriched_wan2_provider,
                ec.wan2_speed as enriched_wan2_speed,
                ec.wan2_circuit_role,
                -- Meraki inventory data
                mi.wan1_ip,
                mi.wan2_ip,
                mi.wan1_arin_provider,
                mi.wan2_arin_provider,
                SUBSTRING(mi.device_notes, 1, 500) as meraki_notes,
                -- DSR circuits data
                c1.provider_name as dsr_primary_provider,
                c1.details_ordered_service_speed as dsr_primary_speed,
                c1.ip_address_start as dsr_primary_ip,
                c2.provider_name as dsr_secondary_provider,
                c2.details_ordered_service_speed as dsr_secondary_speed,
                c2.ip_address_start as dsr_secondary_ip
            FROM site_data sd
            LEFT JOIN enriched_circuits ec ON (
                ec.network_name = sd.site_name OR 
                ec.network_name = REPLACE(sd.site_name, ' ', '_')
            )
            LEFT JOIN meraki_inventory mi ON mi.network_name = ec.network_name
            LEFT JOIN circuits c1 ON c1.site_name = sd.site_name 
                AND c1.circuit_purpose = 'Primary' 
                AND c1.status = 'Enabled'
            LEFT JOIN circuits c2 ON c2.site_name = sd.site_name 
                AND c2.circuit_purpose = 'Secondary' 
                AND c2.status = 'Enabled'
        """, (site_name,))
        
        comp_result = cursor.fetchone()
        if comp_result:
            comprehensive_data.append({
                'Site Name': comp_result[0],
                'Network Name (Enriched)': comp_result[1],
                # Enriched data
                'Enriched WAN1 Provider': comp_result[2],
                'Enriched WAN1 Speed': comp_result[3],
                'Enriched WAN1 Role': comp_result[4],
                'Enriched WAN2 Provider': comp_result[5],
                'Enriched WAN2 Speed': comp_result[6],
                'Enriched WAN2 Role': comp_result[7],
                # Meraki data
                'Meraki WAN1 IP': comp_result[8],
                'Meraki WAN2 IP': comp_result[9],
                'Meraki WAN1 ARIN Provider': comp_result[10],
                'Meraki WAN2 ARIN Provider': comp_result[11],
                'Meraki Notes': comp_result[12],
                # DSR data
                'DSR Primary Provider': comp_result[13],
                'DSR Primary Speed': comp_result[14],
                'DSR Primary IP': comp_result[15],
                'DSR Secondary Provider': comp_result[16],
                'DSR Secondary Speed': comp_result[17],
                'DSR Secondary IP': comp_result[18]
            })
    
    # Save to CSV files instead of Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save enriched circuits data
    output_file1 = f'/usr/local/bin/enriched_circuits_export_{timestamp}.csv'
    if export_data:
        df_export = pd.DataFrame(export_data)
        df_export.to_csv(output_file1, index=False)
        print(f"\n✅ Enriched circuits data saved to: {output_file1}")
    
    # Save comprehensive analysis
    output_file2 = f'/usr/local/bin/enriched_circuits_full_analysis_{timestamp}.csv'
    if comprehensive_data:
        df_comprehensive = pd.DataFrame(comprehensive_data)
        df_comprehensive.to_csv(output_file2, index=False)
        print(f"✅ Full analysis saved to: {output_file2}")
    
    # Count corruptions for summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total_sites,
            COUNT(CASE WHEN wan1_speed LIKE '%% M' THEN 1 END) as wan1_corrupted,
            COUNT(CASE WHEN wan2_speed LIKE '%% M' THEN 1 END) as wan2_corrupted,
            COUNT(CASE WHEN wan1_speed LIKE '%%x%%' THEN 1 END) as wan1_correct,
            COUNT(CASE WHEN wan2_speed LIKE '%%x%%' THEN 1 END) as wan2_correct
        FROM enriched_circuits
        WHERE network_name IN %s OR network_name IN %s
    """, (tuple(unique_sites), tuple([s.replace(' ', '_') for s in unique_sites])))
    
    stats = cursor.fetchone()
    
    print(f"\n📊 Export Summary:")
    
    # Print summary
    if stats:
        print(f"\nSummary:")
        print(f"  Total sites: {stats[0]}")
        print(f"  WAN1 corrupted: {stats[1]} ({stats[1]/stats[0]*100:.1f}%)")
        print(f"  WAN2 corrupted: {stats[2]} ({stats[2]/stats[0]*100:.1f}%)")
    
    cursor.close()
    conn.close()
    
    return output_file1

if __name__ == "__main__":
    export_enriched_circuits()