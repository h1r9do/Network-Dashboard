#!/usr/bin/env python3
"""
Import costs from master circuit list to DSR circuits table
"""

import sys
sys.path.insert(0, '.')
from config import Config
from sqlalchemy import create_engine, text
import json
import glob
import os
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
    print(f"Loaded master data from {latest_master}")
else:
    print("No master circuit data found")
    exit(1)

def normalize_provider_name(provider1, provider2):
    """Check if two provider names are similar enough to match"""
    if not provider1 or not provider2:
        return False
    
    p1 = provider1.upper().strip()
    p2 = provider2.upper().strip()
    
    # Direct match
    if p1 == p2:
        return True
    
    # Common variations
    variations = [
        (['AT&T', 'ATT'], ['AT&T BROADBAND II', 'AT&T']),
        (['FRONTIER', 'FRONTIER COMMUNICATIONS'], ['FRONTIER FIOS', 'FRONTIER DEDICATED']),
        (['CHARTER', 'CHARTER COMMUNICATIONS'], ['SPECTRUM']),
        (['COMCAST'], ['COMCAST - ISP', 'COMCAST WORKPLACE']),
        (['COX', 'COX COMMUNICATIONS'], ['COX BUSINESS']),
    ]
    
    for group1, group2 in variations:
        if any(v in p1 for v in group1) and any(v in p2 for v in group2):
            return True
        if any(v in p2 for v in group1) and any(v in p1 for v in group2):
            return True
    
    # Substring match
    if len(p1) >= 4 and len(p2) >= 4:
        if p1[:4] in p2 or p2[:4] in p1:
            return True
    
    return False

def main():
    with engine.connect() as conn:
        # Get sites with $0.00 costs that have master data
        result = conn.execute(text('''
            SELECT DISTINCT ec.network_name, ec.wan1_provider
            FROM enriched_circuits ec
            WHERE ec.wan1_provider NOT LIKE '%Cell%'
            AND ec.wan1_provider NOT LIKE '%VZW%'
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
        imported_count = 0
        
        for site_name, wan1_provider in sites:
            site_upper = site_name.upper().strip()
            if site_upper not in master_lookup:
                continue
                
            master_item = master_lookup[site_upper]
            carrier_a = master_item.get('Active A Circuit Carrier', '')
            mrc_a = master_item.get('MRC', '')
            
            if not mrc_a:
                continue
                
            try:
                cost_a = float(str(mrc_a).replace('$', '').replace(',', ''))
                if cost_a <= 0:
                    continue
            except:
                continue
            
            # Check if provider names match
            if not normalize_provider_name(wan1_provider, carrier_a):
                print(f"⚠️  {site_name}: Provider mismatch - WAN1: '{wan1_provider}' vs Master: '{carrier_a}' (${cost_a})")
                continue
            
            # Check if circuit already exists
            existing = conn.execute(text('''
                SELECT id FROM circuits 
                WHERE LOWER(site_name) = LOWER(:site)
                AND LOWER(circuit_purpose) = 'primary'
            '''), {'site': site_name}).fetchone()
            
            if existing:
                # Update existing circuit
                conn.execute(text('''
                    UPDATE circuits 
                    SET billing_monthly_cost = :cost,
                        provider_name = :provider,
                        status = 'Enabled',
                        date_record_updated = CURRENT_TIMESTAMP
                    WHERE id = :id
                '''), {
                    'cost': cost_a,
                    'provider': carrier_a,
                    'id': existing[0]
                })
                print(f"✅ {site_name}: Updated existing circuit - {carrier_a} ${cost_a}")
            else:
                # Create new circuit
                conn.execute(text('''
                    INSERT INTO circuits (
                        site_name, circuit_purpose, provider_name, 
                        billing_monthly_cost, status, date_record_updated
                    ) VALUES (
                        :site, 'Primary', :provider, :cost, 'Enabled', CURRENT_TIMESTAMP
                    )
                '''), {
                    'site': site_name,
                    'provider': carrier_a,
                    'cost': cost_a
                })
                print(f"✅ {site_name}: Created new circuit - {carrier_a} ${cost_a}")
            
            imported_count += 1
            
            if imported_count >= 50:  # Limit to first 50 for safety
                break
        
        conn.commit()
        print(f"\n📊 Imported costs for {imported_count} sites from master circuit list")

if __name__ == "__main__":
    main()