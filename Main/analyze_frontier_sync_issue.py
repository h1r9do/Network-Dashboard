#!/usr/bin/env python3
"""
Analyze why Frontier non-DSR circuits aren't getting synced from enriched_circuits
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

def analyze_sync_issue():
    """Analyze the sync issue for Frontier sites"""
    
    # Sites to check
    sites = ['CAL 13', 'CAL 17', 'CAL 20', 'CAL 24', 'CAN 16', 'CAS 35', 'CAS 40', 'CAS 41', 'CAS 48']
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        print('Analyzing Frontier sync issue...')
        print('=' * 80)
        
        # First, check which sites are considered "dsr_sites" by the sync logic
        print('\n1. Sites excluded from sync (have DSR Primary circuits):')
        print('-' * 40)
        
        query = """
        SELECT DISTINCT site_name 
        FROM circuits 
        WHERE circuit_purpose = 'Primary' 
        AND status = 'Enabled'
        AND provider_name NOT LIKE '%Unknown%'
        AND provider_name IS NOT NULL
        AND provider_name != ''
        AND site_name = ANY(%s)
        ORDER BY site_name
        """
        
        cur.execute(query, (sites,))
        results = cur.fetchall()
        dsr_sites = [row[0] for row in results]
        
        for site in dsr_sites:
            print(f"  - {site} (EXCLUDED from sync)")
        
        print(f"\nTotal: {len(dsr_sites)} sites excluded from sync")
        
        # Check what's in enriched_circuits for these sites
        print('\n2. Enriched data available but not synced:')
        print('-' * 40)
        
        for site in sites:
            query = """
            SELECT 
                network_name,
                wan1_provider,
                wan1_speed,
                wan1_confirmed,
                wan2_provider,
                wan2_speed,
                wan2_confirmed
            FROM enriched_circuits
            WHERE network_name = %s
            """
            
            cur.execute(query, (site,))
            enriched = cur.fetchone()
            
            if enriched:
                print(f"\n{site}:")
                print(f"  WAN1: {enriched[1]} ({enriched[2]}) - Confirmed: {enriched[3]}")
                print(f"  WAN2: {enriched[4]} ({enriched[5]}) - Confirmed: {enriched[6]}")
                
                # Check if this site is excluded
                if site in dsr_sites:
                    print(f"  ⚠️  Site EXCLUDED from sync because it has DSR Primary circuits")
                else:
                    print(f"  ✓ Site eligible for sync")
        
        # Show what the sync query would return
        print('\n3. Circuits that WOULD be synced if not for the exclusion:')
        print('-' * 40)
        
        query = """
        SELECT 
            c.site_name,
            c.circuit_purpose,
            c.provider_name as current_provider,
            c.data_source,
            CASE 
                WHEN c.circuit_purpose = 'Primary' THEN e.wan1_provider
                ELSE e.wan2_provider
            END as enriched_provider,
            CASE 
                WHEN c.circuit_purpose = 'Primary' THEN e.wan1_confirmed
                ELSE e.wan2_confirmed
            END as is_confirmed
        FROM circuits c
        JOIN enriched_circuits e ON c.site_name = e.network_name
        WHERE c.status = 'Enabled'
        AND c.manual_override IS NOT TRUE
        AND c.site_name = ANY(%s)
        AND c.data_source = 'Non-DSR'
        AND (
            (c.circuit_purpose = 'Primary' AND e.wan1_confirmed = TRUE) OR
            (c.circuit_purpose = 'Secondary' AND e.wan2_confirmed = TRUE)
        )
        ORDER BY c.site_name, c.circuit_purpose
        """
        
        cur.execute(query, (sites,))
        results = cur.fetchall()
        
        for row in results:
            excluded = " (BLOCKED BY DSR EXCLUSION)" if row[0] in dsr_sites else ""
            print(f"  {row[0]} ({row[1]}): "
                  f"'{row[2]}' -> '{row[4]}'"
                  f"{excluded}")
        
        # Proposed fix - show what would happen without the exclusion
        print('\n4. Proposed fix - sync non-DSR circuits regardless of DSR presence:')
        print('-' * 40)
        
        query = """
        SELECT COUNT(*) as count
        FROM circuits c
        JOIN enriched_circuits e ON c.site_name = e.network_name
        WHERE c.status = 'Enabled'
        AND c.manual_override IS NOT TRUE
        AND c.data_source IN ('Non-DSR', 'new_stores_manual')
        AND (
            (c.circuit_purpose = 'Primary' AND e.wan1_confirmed = TRUE) OR
            (c.circuit_purpose = 'Secondary' AND e.wan2_confirmed = TRUE)
        )
        """
        
        cur.execute(query)
        result = cur.fetchone()
        print(f"  Total non-DSR circuits that could be updated: {result[0]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    analyze_sync_issue()