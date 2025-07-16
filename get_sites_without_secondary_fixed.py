#!/usr/bin/env python3
"""
Get the actual list of sites without secondary circuits from the database
Using correct column names
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import csv

db_config = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

def get_sites_without_secondary():
    """Get sites without secondary circuits"""
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query to find sites with only primary circuits
        query = """
        WITH circuit_summary AS (
            SELECT 
                site_id,
                site_name,
                COUNT(DISTINCT CASE WHEN circuit_purpose = 'Primary' THEN id END) as primary_count,
                COUNT(DISTINCT CASE WHEN circuit_purpose = 'Secondary' THEN id END) as secondary_count,
                MAX(CASE WHEN circuit_purpose = 'Primary' THEN provider_name END) as primary_provider,
                MAX(CASE WHEN circuit_purpose = 'Primary' THEN ip_address_start END) as primary_ip,
                MAX(CASE WHEN circuit_purpose = 'Primary' THEN details_service_speed END) as primary_bandwidth,
                MAX(CASE WHEN circuit_purpose = 'Secondary' THEN provider_name END) as secondary_provider,
                COUNT(*) as total_circuits
            FROM circuits
            WHERE status = 'Enabled'
              AND site_id NOT LIKE 'TST%'
              AND site_id NOT LIKE 'NEO%'
              AND site_id NOT LIKE 'TEST%'
              AND site_id IS NOT NULL
              AND site_id != ''
            GROUP BY site_id, site_name
        )
        SELECT 
            site_id,
            site_name,
            primary_provider,
            primary_ip,
            primary_bandwidth,
            primary_count,
            secondary_count,
            total_circuits
        FROM circuit_summary
        WHERE secondary_count = 0
           OR secondary_provider IS NULL
        ORDER BY site_id;
        """
        
        cur.execute(query)
        results = cur.fetchall()
        
        print(f"\nFound {len(results)} sites without secondary circuits")
        
        # Show sample
        print("\nFirst 10 sites:")
        for i, site in enumerate(results[:10]):
            print(f"{i+1}. {site['site_id']} - {site['site_name']} (Primary: {site['primary_provider']})")
        
        # Also check for sites that might need secondary by looking at all sites
        print("\nChecking total site distribution...")
        cur.execute("""
            SELECT 
                circuit_purpose, 
                COUNT(DISTINCT site_id) as site_count,
                COUNT(*) as circuit_count
            FROM circuits
            WHERE status = 'Enabled'
              AND site_id NOT LIKE 'TST%'
              AND site_id NOT LIKE 'NEO%'
              AND site_id IS NOT NULL
            GROUP BY circuit_purpose
            ORDER BY circuit_purpose;
        """)
        
        print("\nCircuit purpose distribution:")
        for row in cur.fetchall():
            print(f"  {row['circuit_purpose']}: {row['site_count']} sites, {row['circuit_count']} circuits")
        
        # Save to CSV
        csv_file = '/usr/local/bin/sites_without_secondary.csv'
        with open(csv_file, 'w', newline='') as f:
            fieldnames = ['site_id', 'site_name', 'primary_provider', 'primary_ip', 'primary_bandwidth']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for site in results:
                writer.writerow({
                    'site_id': site['site_id'],
                    'site_name': site['site_name'],
                    'primary_provider': site['primary_provider'],
                    'primary_ip': site['primary_ip'],
                    'primary_bandwidth': site['primary_bandwidth']
                })
        
        print(f"\nSaved full list to: {csv_file}")
        
        cur.close()
        conn.close()
        
        return results
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == '__main__':
    sites = get_sites_without_secondary()