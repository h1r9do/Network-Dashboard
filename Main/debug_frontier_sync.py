#!/usr/bin/env python3
"""
Debug the Frontier sync issue
"""

import psycopg2

# Database configuration
db_config = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

def debug_sync():
    """Debug the sync issue"""
    
    # Sites to check
    sites = ['CAL 13', 'CAL 17', 'CAL 20', 'CAL 24', 'CAN 16', 'CAS 35', 'CAS 40', 'CAS 41', 'CAS 48']
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        print('1. DSR Primary circuits at these sites:')
        print('-' * 40)
        
        # Simple query first
        for site in sites:
            cur.execute("""
                SELECT site_name, provider_name, status
                FROM circuits 
                WHERE site_name = %s
                AND circuit_purpose = 'Primary'
                AND status = 'Enabled'
                AND provider_name NOT LIKE '%%Unknown%%'
                AND provider_name IS NOT NULL
                AND provider_name != ''
            """, (site,))
            
            result = cur.fetchone()
            if result:
                print(f"{site}: Has DSR Primary - {result[1]} ({result[2]})")
            else:
                print(f"{site}: No DSR Primary")
        
        print('\n2. Enriched data for these sites:')
        print('-' * 40)
        
        for site in sites:
            cur.execute("""
                SELECT wan1_provider, wan1_confirmed, wan2_provider, wan2_confirmed
                FROM enriched_circuits
                WHERE network_name = %s
            """, (site,))
            
            result = cur.fetchone()
            if result:
                print(f"{site}: WAN1={result[0]} (confirmed={result[1]}), WAN2={result[2]} (confirmed={result[3]})")
        
        print('\n3. Non-DSR circuits at these sites:')
        print('-' * 40)
        
        for site in sites:
            cur.execute("""
                SELECT site_name, provider_name, data_source, circuit_purpose
                FROM circuits 
                WHERE site_name = %s
                AND data_source IN ('Non-DSR', 'new_stores_manual')
            """, (site,))
            
            results = cur.fetchall()
            for row in results:
                print(f"{row[0]}: {row[1]} (source={row[2]}, purpose={row[3]})")
        
        print('\n4. The sync exclusion issue:')
        print('-' * 40)
        
        # Show how many sites are excluded
        cur.execute("""
            WITH dsr_sites AS (
                SELECT DISTINCT site_name 
                FROM circuits 
                WHERE circuit_purpose = 'Primary' 
                AND status = 'Enabled'
                AND provider_name NOT LIKE '%%Unknown%%'
                AND provider_name IS NOT NULL
                AND provider_name != ''
                AND site_name = ANY(%s)
            )
            SELECT site_name FROM dsr_sites ORDER BY site_name
        """, (sites,))
        
        excluded = cur.fetchall()
        print(f"Sites excluded from sync: {len(excluded)}")
        for row in excluded:
            print(f"  - {row[0]}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    debug_sync()