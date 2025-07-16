#!/usr/bin/env python3
"""
Check WAN1 circuits with $0.00 cost against DSR and master list
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
else:
    master_lookup = {}
    print("No master circuit data found")

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
            AND (
                UPPER(c.provider_name) LIKE '%' || UPPER(SUBSTR(ec.wan1_provider, 1, 5)) || '%'
                OR UPPER(ec.wan1_provider) LIKE '%' || UPPER(SUBSTR(c.provider_name, 1, 5)) || '%'
            )
        )
        ORDER BY ec.network_name
    '''))
    
    sites = result.fetchall()
    print(f"\nFound {len(sites)} WAN1 circuits with $0.00 cost (non-cell/starlink)\n")
    
    # Process first site (skipping ALM 01 which we already know works)
    if sites:
        site_name, wan1_provider, wan1_speed = sites[9] if len(sites) > 9 else sites[0]
        print(f'=== {site_name} ===')
        print(f'WAN1: {wan1_provider} / {wan1_speed}')
        
        # Check DSR data
        print('\nDSR Circuits:')
        dsr_result = conn.execute(text('''
            SELECT provider_name, billing_monthly_cost, circuit_purpose
            FROM circuits
            WHERE LOWER(site_name) = LOWER(:site)
            AND status = 'Enabled'
            ORDER BY circuit_purpose
        '''), {'site': site_name})
        
        dsr_rows = dsr_result.fetchall()
        has_match = False
        for dsr_row in dsr_rows:
            provider, cost, purpose = dsr_row
            print(f'  {purpose}: {provider} - ${cost if cost else "0.00"}')
            
            # Check for provider match using enhanced logic from dsrcircuits.py
            if provider and wan1_provider:
                # Normalize for comparison
                dsr_provider = provider.upper().strip()
                wan1_provider_norm = wan1_provider.upper().strip()
                
                # Enhanced matching logic from dsrcircuits.py
                if (dsr_provider in wan1_provider_norm or wan1_provider_norm in dsr_provider or
                    # Spectrum/Charter variations
                    ('SPECTRUM' in dsr_provider and ('CHARTER' in wan1_provider_norm or 'SPECTRUM' in wan1_provider_norm)) or
                    ('CHARTER' in dsr_provider and ('SPECTRUM' in wan1_provider_norm or 'CHARTER' in wan1_provider_norm)) or
                    # AT&T variations
                    ('AT&T' in dsr_provider and 'AT&T' in wan1_provider_norm) or
                    ('ATT' in dsr_provider and 'AT&T' in wan1_provider_norm) or
                    # Cox variations
                    ('COX' in dsr_provider and 'COX' in wan1_provider_norm) or
                    # Comcast variations
                    ('COMCAST' in dsr_provider and 'COMCAST' in wan1_provider_norm) or
                    # Verizon variations
                    ('VERIZON' in dsr_provider and 'VERIZON' in wan1_provider_norm) or
                    # CenturyLink variations
                    ('CENTURYLINK' in dsr_provider and ('CENTURYLINK' in wan1_provider_norm or 'CENTURY LINK' in wan1_provider_norm)) or
                    ('CENTURY LINK' in dsr_provider and ('CENTURYLINK' in wan1_provider_norm or 'CENTURY LINK' in wan1_provider_norm)) or
                    ('QWEST' in dsr_provider and 'CENTURYLINK' in wan1_provider_norm) or
                    ('LUMEN' in dsr_provider and 'CENTURYLINK' in wan1_provider_norm) or
                    # Other providers
                    ('SPARKLIGHT' in dsr_provider and 'SPARKLIGHT' in wan1_provider_norm) or
                    ('FRONTIER' in dsr_provider and 'FRONTIER' in wan1_provider_norm) or
                    ('WINDSTREAM' in dsr_provider and 'WINDSTREAM' in wan1_provider_norm) or
                    ('OPTIMUM' in dsr_provider and ('OPTIMUM' in wan1_provider_norm or 'ALTICE' in wan1_provider_norm)) or
                    ('ALTICE' in dsr_provider and ('OPTIMUM' in wan1_provider_norm or 'ALTICE' in wan1_provider_norm))):
                    if cost and cost > 0:
                        has_match = True
                        print(f'    -> MATCH! Should be ${cost}')
        
        # Check master JSON
        site_upper = site_name.upper().strip()
        if site_upper in master_lookup:
            print(f'\nMaster Circuit List:')
            master_item = master_lookup[site_upper]
            if master_item.get('Active A Circuit Carrier'):
                mrc = master_item.get('MRC', '')
                print(f'  Carrier A: {master_item["Active A Circuit Carrier"]} - ${mrc}')
            if master_item.get('Active B Circuit Carrier'):
                mrc3 = master_item.get('MRC3', '')
                print(f'  Carrier B: {master_item["Active B Circuit Carrier"]} - ${mrc3}')
        else:
            print(f'\n{site_name} not found in master list')
        
        # Summary
        if has_match:
            print(f'\n✅ Found cost in DSR data')
        else:
            print(f'\n❌ No cost found in DSR data')
        
        print(f'\nRemaining sites to check: {len(sites) - 1}')