#!/usr/bin/env python3
"""
Export remaining sites with WAN1 $0.00 costs to CSV for review
"""

import sys
sys.path.insert(0, '.')
from config import Config
from sqlalchemy import create_engine, text
import json
import glob
import os
import csv
from datetime import datetime

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

# Load master circuit data
master_files = glob.glob('/var/www/html/circuitinfo/master_circuit_data_*.json')
if master_files:
    latest_master = max(master_files, key=os.path.getmtime)
    with open(latest_master, 'r') as f:
        master_data = json.load(f)
    
    master_lookup = {}
    for item in master_data:
        store = item.get('Store', '')
        if store:
            store = store.upper().strip()
            master_lookup[store] = item
else:
    master_lookup = {}

def main():
    with engine.connect() as conn:
        # Get all remaining $0.00 sites with additional details
        result = conn.execute(text('''
            SELECT DISTINCT 
                ec.network_name, 
                ec.wan1_provider, 
                ec.wan1_speed,
                ec.wan2_provider,
                ec.wan2_speed
            FROM enriched_circuits ec
            WHERE ec.wan1_provider NOT LIKE '%Cell%'
            AND ec.wan1_provider NOT LIKE '%VZW%'
            AND ec.wan1_provider NOT LIKE '%T-Mobile%'
            AND ec.wan1_provider NOT LIKE '%TMO%'
            AND ec.wan1_provider NOT LIKE '%Starlink%'
            AND ec.wan1_provider != ''
            AND ec.wan1_provider IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM circuits c
                WHERE LOWER(c.site_name) = LOWER(ec.network_name)
                AND c.status = 'Enabled'
                AND c.billing_monthly_cost > 0
            )
            ORDER BY ec.network_name
        '''))
        
        sites = result.fetchall()
        
        # Create CSV file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"/tmp/remaining_zero_costs_{timestamp}.csv"
        
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow([
                'Site_Name',
                'WAN1_Provider', 
                'WAN1_Speed',
                'WAN2_Provider',
                'WAN2_Speed',
                'Category',
                'Master_Carrier_A',
                'Master_Cost_A',
                'Master_Carrier_B', 
                'Master_Cost_B',
                'DSR_Circuits_Found',
                'Notes'
            ])
            
            for site_name, wan1_provider, wan1_speed, wan2_provider, wan2_speed in sites:
                site_upper = site_name.upper().strip()
                
                # Get DSR circuit info
                dsr_result = conn.execute(text('''
                    SELECT circuit_purpose, provider_name, billing_monthly_cost, status
                    FROM circuits
                    WHERE LOWER(site_name) = LOWER(:site)
                    ORDER BY circuit_purpose
                '''), {'site': site_name})
                
                dsr_circuits = []
                for row in dsr_result:
                    purpose, provider, cost, status = row
                    dsr_circuits.append(f"{purpose}: {provider} ${cost if cost else '0.00'} ({status})")
                
                dsr_info = "; ".join(dsr_circuits) if dsr_circuits else "None"
                
                # Categorize and get master data
                category = ""
                master_carrier_a = ""
                master_cost_a = ""
                master_carrier_b = ""
                master_cost_b = ""
                notes = ""
                
                # Check for special provider patterns
                if any(pattern in wan1_provider.lower() for pattern in ['private customer', 'unknown', 'temp', 'test']):
                    category = "Special Provider"
                    notes = "Special provider type - likely legitimate $0.00"
                elif '_00' in site_name or 'W0' in site_name:
                    category = "Construction Site"
                    notes = "Appears to be construction/new site"
                elif any(keyword in site_name.lower() for keyword in ['callcntr', 'flight', 'office', 'ridge']):
                    category = "Special Facility"
                    notes = "Special facility - not standard store"
                elif site_upper in master_lookup:
                    master_item = master_lookup[site_upper]
                    master_carrier_a = master_item.get('Active A Circuit Carrier', '')
                    master_cost_a = master_item.get('MRC', '')
                    master_carrier_b = master_item.get('Active B Circuit Carrier', '')
                    master_cost_b = master_item.get('MRC3', '')
                    
                    if master_cost_a and str(master_cost_a).replace('$', '').replace(',', '').strip():
                        try:
                            cost_a = float(str(master_cost_a).replace('$', '').replace(',', ''))
                            if cost_a > 0:
                                category = "Provider Mismatch"
                                notes = f"Master has cost but provider mismatch: WAN1='{wan1_provider}' vs Master='{master_carrier_a}'"
                            else:
                                category = "Master No Cost"
                                notes = "In master list but no cost data"
                        except:
                            category = "Master No Cost"
                            notes = "In master list but invalid cost data"
                    else:
                        category = "Master No Cost"
                        notes = "In master list but no cost data"
                else:
                    category = "Not in Master"
                    notes = "Site not found in master circuit list"
                
                # Write row
                writer.writerow([
                    site_name,
                    wan1_provider,
                    wan1_speed or '',
                    wan2_provider or '',
                    wan2_speed or '',
                    category,
                    master_carrier_a,
                    master_cost_a,
                    master_carrier_b,
                    master_cost_b,
                    dsr_info,
                    notes
                ])
        
        print(f"✅ Exported {len(sites)} sites to: {csv_filename}")
        
        # Copy to a more accessible location
        accessible_path = f"/usr/local/bin/Main/remaining_zero_costs_{timestamp}.csv"
        import shutil
        shutil.copy2(csv_filename, accessible_path)
        print(f"✅ Also saved to: {accessible_path}")
        
        return accessible_path

if __name__ == "__main__":
    main()