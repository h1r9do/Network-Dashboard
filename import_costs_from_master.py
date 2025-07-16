#!/usr/bin/env python3
"""
Import costs from master circuit list for sites with $0.00 costs
"""

import sys
sys.path.insert(0, '.')
from config import Config
from sqlalchemy import create_engine, text
import json
import glob
import os

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

# Load master circuit data
master_files = glob.glob('/var/www/html/circuitinfo/master_circuit_data_*.json')
if master_files:
    latest_master = max(master_files, key=os.path.getmtime)
    with open(latest_master, 'r') as f:
        master_data = json.load(f)
    
    # Create lookup
    master_lookup = {}
    for item in master_data:
        store = item.get('Store', '')
        if store:
            store = store.upper().strip()
            master_lookup[store] = item
    print(f"Loaded master data with {len(master_lookup)} stores")
else:
    master_lookup = {}
    print("No master circuit data found")

def main():
    with engine.connect() as conn:
        # Get all WAN1 $0.00 non-cell circuits
        result = conn.execute(text('''
            SELECT DISTINCT ec.network_name, ec.wan1_provider, ec.wan1_speed
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
        print(f"\nFound {len(sites)} sites with WAN1 $0.00 cost (non-cell/starlink)")
        
        import_candidates = []
        
        for site_name, wan1_provider, wan1_speed in sites:
            site_upper = site_name.upper().strip()
            if site_upper in master_lookup:
                master_item = master_lookup[site_upper]
                
                # Check if master has cost data
                carrier_a = master_item.get('Active A Circuit Carrier', '')
                mrc_a = master_item.get('MRC', '')
                carrier_b = master_item.get('Active B Circuit Carrier', '')
                mrc_b = master_item.get('MRC3', '')
                
                if mrc_a and str(mrc_a).replace('$', '').replace(',', '').strip():
                    try:
                        cost_a = float(str(mrc_a).replace('$', '').replace(',', ''))
                        if cost_a > 0:
                            import_candidates.append({
                                'site_name': site_name,
                                'wan1_provider': wan1_provider,
                                'master_carrier_a': carrier_a,
                                'master_cost_a': cost_a
                            })
                    except:
                        pass
        
        print(f"\nFound {len(import_candidates)} sites that could import costs from master:")
        
        for i, candidate in enumerate(import_candidates[:10], 1):  # Show first 10
            print(f"{i:2d}. {candidate['site_name']}: {candidate['wan1_provider']} -> {candidate['master_carrier_a']} (${candidate['master_cost_a']})")
        
        if len(import_candidates) > 10:
            print(f"    ... and {len(import_candidates) - 10} more")
        
        return import_candidates

if __name__ == "__main__":
    candidates = main()