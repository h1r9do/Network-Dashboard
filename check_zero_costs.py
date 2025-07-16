#!/usr/bin/env python3
"""
Check for $0.00 WAN1 costs on non-cell circuits
"""

import sys
sys.path.insert(0, '.')
from config import Config
from sqlalchemy import create_engine, text
import json
import csv

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

# First, let's see what circuits have $0.00 on WAN1 that aren't cell
with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT ec.network_name, ec.wan1_provider, ec.wan1_speed, ec.wan1_monthly_cost,
               c.provider_name, c.billing_monthly_cost, c.circuit_purpose
        FROM enriched_circuits ec
        LEFT JOIN circuits c ON LOWER(ec.network_name) = LOWER(c.site_name)
            AND c.status = 'Enabled'
        WHERE (ec.wan1_monthly_cost = '$0.00' OR ec.wan1_monthly_cost IS NULL)
        AND ec.wan1_provider NOT LIKE '%Cell%'
        AND ec.wan1_provider NOT LIKE '%VZW%'
        AND ec.wan1_provider NOT LIKE '%T-Mobile%'
        AND ec.wan1_provider NOT LIKE '%TMO%'
        AND ec.wan1_provider != ''
        ORDER BY ec.network_name
        LIMIT 30
    '''))
    
    print('WAN1 $0.00 Non-Cell Circuits:')
    print('=' * 80)
    zero_cost_sites = []
    for row in result:
        print(f'{row[0]}: {row[1]} / {row[2]}')
        print(f'  Enriched Cost: {row[3]}')
        if row[4]:
            print(f'  DSR Circuit: {row[6]} - {row[4]} / ${row[5] if row[5] else "0.00"}')
        zero_cost_sites.append({
            'site': row[0],
            'provider': row[1],
            'speed': row[2]
        })
        print()

# Now check the master JSON file
print('\nChecking Master Circuit List JSON...')
print('=' * 80)
try:
    with open('/usr/local/bin/Main/master_circuit_list.json', 'r') as f:
        master_data = json.load(f)
    
    # Create lookup by store name
    master_lookup = {}
    for item in master_data:
        store = item.get('Store', '').upper()
        if store:
            if store not in master_lookup:
                master_lookup[store] = []
            master_lookup[store].append(item)
    
    # Check our zero cost sites
    for site in zero_cost_sites[:10]:  # Just check first 10
        site_upper = site['site'].upper()
        if site_upper in master_lookup:
            print(f"\n{site['site']}:")
            for master_item in master_lookup[site_upper]:
                # Check if provider matches
                for carrier_key in ['Carrier 1', 'Carrier 2', 'Carrier 3', 'Carrier 4']:
                    carrier = master_item.get(carrier_key, '')
                    mrc_key = carrier_key.replace('Carrier', 'MRC')
                    mrc = master_item.get(mrc_key, '')
                    if carrier and site['provider'].upper() in carrier.upper():
                        print(f"  Found in Master: {carrier} - ${mrc}")
                        break
except Exception as e:
    print(f"Error reading master JSON: {e}")

# Check last night's tracking CSV
print('\n\nChecking Last Night\'s Tracking CSV...')
print('=' * 80)
try:
    # Find the most recent tracking file
    import os
    import glob
    tracking_files = glob.glob('/var/www/html/circuitinfo/DT-CIRCUIT-TRACKING-DATA-*.csv')
    if tracking_files:
        latest_tracking = max(tracking_files, key=os.path.getmtime)
        print(f"Using: {latest_tracking}")
        
        with open(latest_tracking, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            tracking_data = list(reader)
        
        # Check our zero cost sites
        for site in zero_cost_sites[:10]:  # Just check first 10
            found = False
            for row in tracking_data:
                if row.get('Site Name', '').upper() == site['site'].upper():
                    if site['provider'].upper() in row.get('Provider Name', '').upper():
                        cost = row.get('Billing - Monthly Cost', '0')
                        status = row.get('Status', '')
                        print(f"\n{site['site']}: {row.get('Provider Name')} - ${cost} ({status})")
                        found = True
            if not found:
                print(f"\n{site['site']}: Not found in tracking with matching provider")
except Exception as e:
    print(f"Error reading tracking CSV: {e}")