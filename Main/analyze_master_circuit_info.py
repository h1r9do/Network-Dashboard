#!/usr/bin/env python3
"""
Analyze master circuit info to find sites with less than 2 circuits
and check for available non-DSR circuit information
"""

import pandas as pd
import psycopg2
from datetime import datetime
import json

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123',
    'port': 5432
}

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DB_CONFIG)

def analyze_circuit_data():
    """Analyze circuit data from database and Excel file"""
    
    # First, let's get all sites and their circuit counts from database
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get circuit counts per site
    cur.execute("""
        SELECT 
            site_name,
            COUNT(*) as circuit_count,
            array_agg(DISTINCT data_source) as data_sources,
            array_agg(DISTINCT provider_name) as providers,
            array_agg(DISTINCT details_ordered_service_speed) as speeds,
            array_agg(DISTINCT status) as statuses
        FROM circuits
        WHERE site_name IS NOT NULL 
        AND site_name != ''
        GROUP BY site_name
        ORDER BY site_name
    """)
    
    db_sites = {}
    for row in cur.fetchall():
        db_sites[row[0]] = {
            'count': row[1],
            'data_sources': row[2],
            'providers': row[3],
            'speeds': row[4],
            'statuses': row[5]
        }
    
    # Find sites with less than 2 circuits
    sites_needing_circuits = {}
    for site, info in db_sites.items():
        if info['count'] < 2:
            sites_needing_circuits[site] = info
    
    print(f"Found {len(sites_needing_circuits)} sites with less than 2 circuits")
    
    # Now read the Excel file
    try:
        # First try the copied file
        excel_path = '/tmp/master_circuit_info.xlsx'
        if not pd.io.common.file_exists(excel_path):
            # Try original path with sudo
            import subprocess
            subprocess.run(['sudo', 'cp', '/usr/local/bin/Main/master circuit info cleaned.xlsx', excel_path], check=True)
        
        df = pd.read_excel(excel_path)
        print(f"\nSuccessfully loaded Excel file with {len(df)} rows")
        print(f"Columns: {list(df.columns)}")
        
        # Try to identify the site name column
        site_col = None
        for col in df.columns:
            if 'site' in col.lower() or 'location' in col.lower():
                site_col = col
                break
        
        if site_col:
            print(f"\nUsing column '{site_col}' as site identifier")
        
        # Print first few rows to understand structure
        print("\nFirst 5 rows of Excel data:")
        print(df.head())
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        df = None
    
    # Generate report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_sites_in_db': len(db_sites),
        'sites_with_less_than_2_circuits': len(sites_needing_circuits),
        'sites_needing_circuits': []
    }
    
    for site, info in sorted(sites_needing_circuits.items()):
        site_report = {
            'site_name': site,
            'current_circuit_count': info['count'],
            'existing_providers': info['providers'],
            'existing_speeds': info['speeds'],
            'existing_data_sources': info['data_sources'],
            'excel_data_found': False,
            'potential_circuits': []
        }
        
        # Try to find this site in Excel data if available
        if df is not None and site_col:
            # Search for site in Excel
            site_matches = df[df[site_col].astype(str).str.contains(site, case=False, na=False)]
            if len(site_matches) > 0:
                site_report['excel_data_found'] = True
                site_report['excel_rows_found'] = len(site_matches)
                
                # Extract circuit info from Excel
                for idx, row in site_matches.iterrows():
                    circuit_info = {
                        'row_index': idx,
                        'raw_data': row.to_dict()
                    }
                    
                    # Try to extract provider, speed, cost from various possible columns
                    for col in row.index:
                        col_lower = col.lower()
                        if 'provider' in col_lower or 'carrier' in col_lower:
                            circuit_info['provider'] = str(row[col])
                        elif 'speed' in col_lower or 'bandwidth' in col_lower:
                            circuit_info['speed'] = str(row[col])
                        elif 'cost' in col_lower or 'price' in col_lower or 'monthly' in col_lower:
                            circuit_info['cost'] = str(row[col])
                    
                    site_report['potential_circuits'].append(circuit_info)
        
        report['sites_needing_circuits'].append(site_report)
    
    # Save report
    report_path = '/usr/local/bin/Main/circuit_analysis_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_path}")
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY OF SITES NEEDING CIRCUITS")
    print("="*80)
    
    for site_info in report['sites_needing_circuits'][:10]:  # Show first 10
        print(f"\nSite: {site_info['site_name']}")
        print(f"  Current circuits: {site_info['current_circuit_count']}")
        print(f"  Excel data found: {site_info['excel_data_found']}")
        if site_info['excel_data_found']:
            print(f"  Excel rows found: {site_info['excel_rows_found']}")
    
    if len(report['sites_needing_circuits']) > 10:
        print(f"\n... and {len(report['sites_needing_circuits']) - 10} more sites")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    analyze_circuit_data()