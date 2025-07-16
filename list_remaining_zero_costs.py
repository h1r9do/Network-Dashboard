#!/usr/bin/env python3
"""
List all remaining sites with WAN1 $0.00 costs
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
        # Get all remaining $0.00 sites
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
        print(f"Remaining {len(sites)} WAN1 circuits with $0.00 cost:\n")
        
        # Categorize the sites
        categories = {
            'has_master_data': [],
            'no_master_data': [],
            'provider_mismatch': [],
            'special_providers': []
        }
        
        for site_name, wan1_provider, wan1_speed in sites:
            site_upper = site_name.upper().strip()
            
            # Check for special provider patterns
            if any(pattern in wan1_provider.lower() for pattern in ['private customer', 'unknown', 'temp', 'test']):
                categories['special_providers'].append((site_name, wan1_provider, wan1_speed, 'Special provider'))
                continue
            
            if site_upper in master_lookup:
                master_item = master_lookup[site_upper]
                carrier_a = master_item.get('Active A Circuit Carrier', '')
                mrc_a = master_item.get('MRC', '')
                
                if mrc_a and str(mrc_a).replace('$', '').replace(',', '').strip():
                    try:
                        cost_a = float(str(mrc_a).replace('$', '').replace(',', ''))
                        if cost_a > 0:
                            # Has master data but didn't get imported (probably provider mismatch)
                            categories['provider_mismatch'].append((site_name, wan1_provider, wan1_speed, f'{carrier_a} (${cost_a})'))
                            continue
                    except:
                        pass
                
                categories['has_master_data'].append((site_name, wan1_provider, wan1_speed, f'{carrier_a} (${mrc_a})'))
            else:
                categories['no_master_data'].append((site_name, wan1_provider, wan1_speed, 'Not in master'))
        
        # Print categorized results
        print(f"📊 CATEGORY BREAKDOWN:")
        print(f"   Special Providers: {len(categories['special_providers'])}")
        print(f"   Provider Mismatches: {len(categories['provider_mismatch'])}")
        print(f"   Has Master Data: {len(categories['has_master_data'])}")
        print(f"   No Master Data: {len(categories['no_master_data'])}")
        print()
        
        # Show special providers
        if categories['special_providers']:
            print("🔸 SPECIAL PROVIDERS:")
            for site, provider, speed, note in categories['special_providers'][:10]:
                print(f"   {site}: {provider}")
            if len(categories['special_providers']) > 10:
                print(f"   ... and {len(categories['special_providers']) - 10} more")
            print()
        
        # Show provider mismatches  
        if categories['provider_mismatch']:
            print("⚠️  PROVIDER MISMATCHES (WAN1 vs Master):")
            for site, provider, speed, master_info in categories['provider_mismatch'][:20]:
                print(f"   {site}: '{provider}' vs {master_info}")
            if len(categories['provider_mismatch']) > 20:
                print(f"   ... and {len(categories['provider_mismatch']) - 20} more")
            print()
        
        # Show sites with master data but no costs
        if categories['has_master_data']:
            print("📋 HAS MASTER DATA (no cost):")
            for site, provider, speed, master_info in categories['has_master_data'][:10]:
                print(f"   {site}: {provider} -> {master_info}")
            if len(categories['has_master_data']) > 10:
                print(f"   ... and {len(categories['has_master_data']) - 10} more")
            print()
        
        # Show sites not in master
        if categories['no_master_data']:
            print("❌ NOT IN MASTER LIST:")
            for site, provider, speed, note in categories['no_master_data'][:20]:
                print(f"   {site}: {provider}")
            if len(categories['no_master_data']) > 20:
                print(f"   ... and {len(categories['no_master_data']) - 20} more")

if __name__ == "__main__":
    main()