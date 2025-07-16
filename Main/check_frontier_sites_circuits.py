#!/usr/bin/env python3
"""
Check circuits for failing Frontier sites to identify DSR vs non-DSR circuits
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration
db_config = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

def check_frontier_sites():
    """Check circuits for the failing Frontier sites"""
    
    # Sites to check
    sites = ['CAL 13', 'CAL 17', 'CAL 20', 'CAL 24', 'CAN 16', 'CAS 35', 'CAS 40', 'CAS 41', 'CAS 48']
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print('Checking circuits for failing Frontier sites...')
        print('=' * 80)
        
        # Summary stats
        total_sites_with_non_dsr = 0
        
        for site in sites:
            print(f'\n{site}:')
            print('-' * 40)
            
            # Query all circuits for this site
            query = '''
            SELECT 
                site_id,
                site_name,
                data_source,
                provider_name,
                status,
                circuit_purpose
            FROM circuits
            WHERE site_name = %s
            ORDER BY data_source, circuit_purpose
            '''
            
            cur.execute(query, (site,))
            results = cur.fetchall()
            
            if results:
                # Group by data source type
                dsr_circuits = []
                non_dsr_circuits = []
                
                for row in results:
                    if row['data_source'] in ['csv_import', 'latest_csv_import', 'csv_import_fix']:
                        dsr_circuits.append(row)
                    else:
                        non_dsr_circuits.append(row)
                
                # Display DSR circuits
                if dsr_circuits:
                    print('  DSR Circuits:')
                    for row in dsr_circuits:
                        print(f"    - Site ID: {row['site_id']}, Purpose: {row['circuit_purpose']}, "
                              f"Provider: {row['provider_name']}, Status: {row['status']}, "
                              f"Source: {row['data_source']}")
                
                # Display non-DSR circuits
                if non_dsr_circuits:
                    print('  Non-DSR Circuits:')
                    total_sites_with_non_dsr += 1
                    for row in non_dsr_circuits:
                        print(f"    - Site ID: {row['site_id']}, Purpose: {row['circuit_purpose']}, "
                              f"Provider: {row['provider_name']}, Status: {row['status']}, "
                              f"Source: {row['data_source']}")
                
                # Summary
                print(f'  Total: {len(results)} circuits ({len(dsr_circuits)} DSR, {len(non_dsr_circuits)} non-DSR)')
                
                # Check for potential issues
                if non_dsr_circuits:
                    print('  ⚠️  Site has non-DSR circuits which may interfere with provider matching')
            else:
                print('  No circuits found')
        
        print('\n' + '=' * 80)
        print(f'Summary: {total_sites_with_non_dsr} sites have non-DSR circuits')
        
        # Now check what providers exist for these sites in any form
        print('\n\nChecking all provider names for these sites (including variations):')
        print('=' * 80)
        
        query = '''
        SELECT DISTINCT
            site_name,
            provider_name,
            data_source,
            COUNT(*) as circuit_count
        FROM circuits
        WHERE site_name = ANY(%s)
        GROUP BY site_name, provider_name, data_source
        ORDER BY site_name, provider_name
        '''
        
        cur.execute(query, (sites,))
        results = cur.fetchall()
        
        current_site = None
        for row in results:
            if row['site_name'] != current_site:
                current_site = row['site_name']
                print(f"\n{current_site}:")
            print(f"  - Provider: '{row['provider_name']}' ({row['circuit_count']} circuits, source: {row['data_source']})")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    check_frontier_sites()