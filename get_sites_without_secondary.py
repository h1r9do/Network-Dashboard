#!/usr/bin/env python3
"""
Get the actual list of sites without secondary circuits from the database
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import csv

# Check config.py for database settings
import sys
sys.path.append('/usr/local/bin')

try:
    from config import Config
    db_config = {
        'host': Config.DB_HOST,
        'database': Config.DB_NAME,
        'user': Config.DB_USER,
        'password': Config.DB_PASS
    }
    print(f"Using config from config.py: {Config.DB_NAME}")
except:
    # Try default from SQLALCHEMY_DATABASE_URI
    db_config = {
        'host': 'localhost',
        'database': 'dsrcircuits',
        'user': 'dsruser',
        'password': 'dsrpass123'
    }
    print("Using default config")

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
                COUNT(DISTINCT CASE WHEN circuit_type = 'Primary' THEN circuit_id END) as primary_count,
                COUNT(DISTINCT CASE WHEN circuit_type = 'Secondary' THEN circuit_id END) as secondary_count,
                MAX(CASE WHEN circuit_type = 'Primary' THEN provider END) as primary_provider,
                MAX(CASE WHEN circuit_type = 'Primary' THEN public_ip END) as primary_ip,
                MAX(CASE WHEN circuit_type = 'Primary' THEN bandwidth_mbps END) as primary_bandwidth,
                MAX(CASE WHEN circuit_type = 'Secondary' THEN provider END) as secondary_provider,
                COUNT(*) as total_circuits
            FROM circuits
            WHERE circuit_status = 'Active'
              AND site_id NOT LIKE 'TST%'
              AND site_id NOT LIKE 'NEO%'
              AND site_id NOT LIKE 'TEST%'
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
        return []

if __name__ == '__main__':
    sites = get_sites_without_secondary()