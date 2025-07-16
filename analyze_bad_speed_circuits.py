#!/usr/bin/env python3
"""
Analyze circuits from "Circuits with bad speed.xlsx" file
Shows provider/speed from circuits table, notes from enriched table, and DSR info
"""

import psycopg2
import pandas as pd
import os
from datetime import datetime

def get_db_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )

def analyze_bad_speed_circuits():
    """Read the Excel file and analyze the circuits"""
    
    # Path to the uploaded file
    excel_path = '/tmp/bad_speed_circuits_filtered.xlsx'
    
    if not os.path.exists(excel_path):
        print(f"Error: File not found at {excel_path}")
        return
    
    # Read the Excel file
    print("Reading Excel file...")
    df = pd.read_excel(excel_path)
    print(f"Found {len(df)} circuits in the file\n")
    
    # Get database connection
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create output data
    output_data = []
    
    print("Analyzing circuits from database...\n")
    print("=" * 150)
    
    for idx, row in df.iterrows():
        site_name = row.get('Site Name', row.get('site_name', ''))
        
        if not site_name:
            continue
        
        # Query for circuit data
        cursor.execute("""
            SELECT 
                -- Circuits table data
                c.site_name,
                c.circuit_purpose,
                c.provider_name as circuits_provider,
                c.details_ordered_service_speed as circuits_speed,
                c.status,
                c.ip_address_start,
                
                -- Enriched circuits data
                ec.network_name,
                ec.wan1_provider,
                ec.wan1_speed,
                ec.wan2_provider,
                ec.wan2_speed,
                
                -- Meraki inventory notes
                mi.device_notes,
                
                -- DSR circuit matches
                dsr1.provider_name as dsr_primary_provider,
                dsr1.details_ordered_service_speed as dsr_primary_speed,
                dsr2.provider_name as dsr_secondary_provider,
                dsr2.details_ordered_service_speed as dsr_secondary_speed
                
            FROM circuits c
            LEFT JOIN enriched_circuits ec ON (
                ec.network_name = c.site_name OR
                ec.network_name = REPLACE(c.site_name, ' ', '_') OR
                ec.network_name = c.site_name || '_00' OR
                REPLACE(ec.network_name, '_', '') = c.site_name OR
                REPLACE(ec.network_name, '_', ' ') = c.site_name
            )
            LEFT JOIN meraki_inventory mi ON mi.network_name = ec.network_name
            LEFT JOIN circuits dsr1 ON dsr1.site_name = c.site_name 
                AND dsr1.circuit_purpose = 'Primary' 
                AND dsr1.status = 'Enabled'
            LEFT JOIN circuits dsr2 ON dsr2.site_name = c.site_name 
                AND dsr2.circuit_purpose = 'Secondary' 
                AND dsr2.status = 'Enabled'
            WHERE c.site_name = %s OR c.site_name = %s
            ORDER BY c.circuit_purpose
        """, (site_name, site_name.replace('_', ' ')))
        
        results = cursor.fetchall()
        
        if results:
            print(f"\n{idx+1}. Site: {site_name}")
            print("-" * 140)
            
            for result in results:
                # Parse the result
                site = result[0]
                purpose = result[1]
                circuits_provider = result[2]
                circuits_speed = result[3]
                status = result[4]
                ip = result[5]
                
                network_name = result[6]
                wan1_provider = result[7]
                wan1_speed = result[8]
                wan2_provider = result[9]
                wan2_speed = result[10]
                
                device_notes = result[11]
                
                dsr_primary_provider = result[12]
                dsr_primary_speed = result[13]
                dsr_secondary_provider = result[14]
                dsr_secondary_speed = result[15]
                
                # Determine which WAN port to show based on circuit purpose
                if purpose == 'Primary':
                    enriched_provider = wan1_provider
                    enriched_speed = wan1_speed
                else:
                    enriched_provider = wan2_provider
                    enriched_speed = wan2_speed
                
                print(f"\n  Circuit Purpose: {purpose}")
                print(f"  Status: {status}")
                print(f"  IP Address: {ip}")
                print(f"\n  From Circuits Table:")
                print(f"    Provider: {circuits_provider}")
                print(f"    Speed: {circuits_speed}")
                
                print(f"\n  From Enriched Table (Network: {network_name}):")
                print(f"    Provider: {enriched_provider}")
                print(f"    Speed: {enriched_speed}")
                
                if purpose == 'Primary' and dsr_primary_provider:
                    print(f"\n  DSR Primary Circuit:")
                    print(f"    Provider: {dsr_primary_provider}")
                    print(f"    Speed: {dsr_primary_speed}")
                elif purpose == 'Secondary' and dsr_secondary_provider:
                    print(f"\n  DSR Secondary Circuit:")
                    print(f"    Provider: {dsr_secondary_provider}")
                    print(f"    Speed: {dsr_secondary_speed}")
                
                if device_notes:
                    print(f"\n  Meraki Device Notes (first 200 chars):")
                    print(f"    {device_notes[:200]}...")
                
                # Add to output data
                output_data.append({
                    'Site Name': site,
                    'Circuit Purpose': purpose,
                    'Status': status,
                    'IP Address': ip,
                    'Circuits Table Provider': circuits_provider,
                    'Circuits Table Speed': circuits_speed,
                    'Enriched Network Name': network_name,
                    'Enriched Provider': enriched_provider,
                    'Enriched Speed': enriched_speed,
                    'DSR Provider': dsr_primary_provider if purpose == 'Primary' else dsr_secondary_provider,
                    'DSR Speed': dsr_primary_speed if purpose == 'Primary' else dsr_secondary_speed,
                    'Has Meraki Notes': 'Yes' if device_notes else 'No',
                    'Notes Preview': device_notes[:100] + '...' if device_notes else ''
                })
        else:
            print(f"\n{idx+1}. Site: {site_name} - NO DATA FOUND IN DATABASE")
    
    # Save to CSV
    if output_data:
        output_file = f'/usr/local/bin/bad_speed_circuits_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        output_df = pd.DataFrame(output_data)
        output_df.to_csv(output_file, index=False)
        print(f"\n\nAnalysis complete. Results saved to: {output_file}")
        
        # Summary statistics
        print("\n=== SUMMARY ===")
        print(f"Total circuits analyzed: {len(output_data)}")
        
        # Count corrupted speeds
        corrupted = sum(1 for d in output_data if d['Enriched Speed'] and ' M' in d['Enriched Speed'] and ' x ' not in d['Enriched Speed'])
        print(f"Circuits with corrupted speed format: {corrupted}")
        
        # Count by provider
        print("\nBy Provider (from enriched table):")
        provider_counts = {}
        for d in output_data:
            provider = d['Enriched Provider'] or 'Unknown'
            if provider not in provider_counts:
                provider_counts[provider] = {'total': 0, 'corrupted': 0}
            provider_counts[provider]['total'] += 1
            if d['Enriched Speed'] and ' M' in d['Enriched Speed'] and ' x ' not in d['Enriched Speed']:
                provider_counts[provider]['corrupted'] += 1
        
        for provider, counts in sorted(provider_counts.items()):
            print(f"  {provider}: {counts['total']} total, {counts['corrupted']} corrupted")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    analyze_bad_speed_circuits()