#!/usr/bin/env python3
"""Update specific sites with ARIN providers using the fixed parser"""

import sys
sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import get_provider_for_ip
from sqlalchemy import create_engine, text
from config import Config
import time
from datetime import datetime

def main():
    # List of specific sites to update
    sites_to_update = [
        'ALB 01', 'ALB 03', 'ALM 01', 'ALM 02', 'ALM 03', 'ALM 04',
        'ALN 01', 'ALN 02', 'ALS 01', 'ALS 02', 'ARL 01', 'ARL 02',
        'ARL 05', 'ARL 06', 'ARO 01', 'ARO 02', 'ARO 03', 'ARO 04',
        'ARO 05', 'ARO 06', 'AZC 01', 'AZF 02', 'AZH 01', 'AZM 01',
        'AZN 02', 'AZN 03', 'AZN 04', 'AZN 06', 'AZP 01', 'AZP 03',
        'AZP 05', 'AZP 07', 'AZP 08', 'AZP 09', 'AZP 10', 'AZP 11',
        'AZP 13', 'AZP 14', 'AZP 16', 'AZP 17', 'AZP 18', 'AZP 19',
        'AZP 20', 'AZP 21', 'AZP 22', 'AZP 23', 'AZP_00'
    ]
    
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    cache = {}
    missing_set = set()
    
    print(f"Updating ARIN providers for {len(sites_to_update)} sites...")
    print("="*70)
    
    with engine.connect() as conn:
        for i, site_name in enumerate(sites_to_update):
            # Get current data
            result = conn.execute(text('''
                SELECT wan1_ip, wan1_arin_provider, wan2_ip, wan2_arin_provider
                FROM meraki_inventory
                WHERE network_name = :site_name
                AND device_model LIKE 'MX%'
                LIMIT 1
            '''), {'site_name': site_name})
            
            row = result.fetchone()
            if not row:
                print(f"{i+1}. {site_name:<15} - Not found in database")
                continue
            
            wan1_ip, wan1_old, wan2_ip, wan2_old = row
            
            # Get new ARIN providers
            wan1_new = None
            wan2_new = None
            
            if wan1_ip and not any(wan1_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
                wan1_new = get_provider_for_ip(wan1_ip, cache, missing_set)
            
            if wan2_ip and not any(wan2_ip.startswith(prefix) for prefix in ['192.168', '10.', '172.']):
                wan2_new = get_provider_for_ip(wan2_ip, cache, missing_set)
            
            # Update if changed
            updates = []
            params = {'site_name': site_name, 'updated': datetime.now()}
            
            if wan1_new and wan1_new != wan1_old:
                updates.append("wan1_arin_provider = :wan1_provider")
                params['wan1_provider'] = wan1_new
            
            if wan2_new and wan2_new != wan2_old:
                updates.append("wan2_arin_provider = :wan2_provider")
                params['wan2_provider'] = wan2_new
            
            if updates:
                update_sql = f'''
                    UPDATE meraki_inventory
                    SET {', '.join(updates)}, last_updated = :updated
                    WHERE network_name = :site_name
                    AND device_model LIKE 'MX%'
                '''
                conn.execute(text(update_sql), params)
                conn.commit()
                
                print(f"{i+1}. {site_name:<15} - Updated: ", end='')
                if 'wan1_provider' in params:
                    print(f"WAN1={params['wan1_provider']}", end=' ')
                if 'wan2_provider' in params:
                    print(f"WAN2={params['wan2_provider']}", end='')
                print()
            else:
                print(f"{i+1}. {site_name:<15} - No changes needed")
            
            # Rate limit
            if (i + 1) % 10 == 0:
                time.sleep(1)
    
    print("\n" + "="*70)
    print("Update complete!")
    print(f"Cache size: {len(cache)} IPs")
    print(f"Missing IPs: {len(missing_set)}")
    
    # Verify AZN 02 specifically
    print("\nVerifying AZN 02:")
    with engine.connect() as conn:
        result = conn.execute(text('''
            SELECT network_name, wan1_ip, wan1_arin_provider, wan2_ip, wan2_arin_provider
            FROM meraki_inventory
            WHERE network_name = 'AZN 02'
            AND device_model LIKE 'MX%'
        '''))
        
        row = result.fetchone()
        if row:
            print(f"  Network: {row[0]}")
            print(f"  WAN1: {row[1]} → {row[2]}")
            print(f"  WAN2: {row[3]} → {row[4]}")

if __name__ == "__main__":
    main()