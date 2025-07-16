#!/usr/bin/env python3
"""Query circuits for 9 Frontier sites"""

import psycopg2
from config import Config
import pandas as pd
import re

def get_db_connection():
    """Get database connection"""
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database
    )

def query_frontier_circuits():
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query for the 9 Frontier sites
    sites = ['CAL 13', 'CAL 17', 'CAL 20', 'CAL 24', 'CAN 16', 'CAS 35', 'CAS 40', 'CAS 41', 'CAS 48']
    sites_str = ', '.join([f"'{site}'" for site in sites])
    
    query = f'''
    SELECT 
        site_name,
        provider_name,
        data_source,
        status,
        details_ordered_service_speed,
        billing_monthly_cost,
        circuit_purpose,
        record_number,
        circuit_type,
        billing_install_cost
    FROM circuits
    WHERE site_name IN ({sites_str})
    ORDER BY site_name, data_source, provider_name
    '''
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Get column names
    columns = [desc[0] for desc in cursor.description]
    
    # Create DataFrame for better display
    df = pd.DataFrame(results, columns=columns)
    
    # Display results grouped by site
    for site in sites:
        site_data = df[df['site_name'] == site]
        if not site_data.empty:
            print(f'\n{"="*80}')
            print(f'SITE: {site}')
            print(f'{"="*80}')
            
            # Separate DSR and Non-DSR circuits
            dsr_circuits = site_data[site_data['data_source'] == 'DSR Global']
            non_dsr_circuits = site_data[site_data['data_source'] != 'DSR Global']
            
            if not dsr_circuits.empty:
                print('\n--- DSR CIRCUITS ---')
                for idx, row in dsr_circuits.iterrows():
                    print(f'  Provider: {row["provider_name"]}')
                    print(f'  Status: {row["status"]}')
                    print(f'  Speed: {row["details_ordered_service_speed"]}')
                    print(f'  Monthly Cost: ${row["billing_monthly_cost"]:.2f}' if pd.notna(row["billing_monthly_cost"]) else '  Monthly Cost: N/A')
                    print(f'  Purpose: {row["circuit_purpose"]}')
                    print(f'  Circuit ID: {row["record_number"]}')
                    print()
            
            if not non_dsr_circuits.empty:
                print('\n--- NON-DSR CIRCUITS ---')
                for idx, row in non_dsr_circuits.iterrows():
                    print(f'  Provider: {row["provider_name"]}')
                    print(f'  Data Source: {row["data_source"]}')
                    print(f'  Status: {row["status"]}')
                    print(f'  Speed: {row["details_ordered_service_speed"]}')
                    print(f'  Monthly Cost: ${row["billing_monthly_cost"]:.2f}' if pd.notna(row["billing_monthly_cost"]) else '  Monthly Cost: N/A')
                    print(f'  Purpose: {row["circuit_purpose"]}')
                    print(f'  Circuit ID: {row["record_number"]}')
                    print()
        else:
            print(f'\n{"="*80}')
            print(f'SITE: {site} - NO CIRCUITS FOUND')
            print(f'{"="*80}')
    
    # Summary statistics
    print(f'\n{"="*80}')
    print('SUMMARY STATISTICS')
    print(f'{"="*80}')
    print(f'Total circuits found: {len(df)}')
    print(f'DSR circuits: {len(df[df["data_source"] == "DSR Global"])}')
    print(f'Non-DSR circuits: {len(df[df["data_source"] != "DSR Global"])}')
    print(f'Enabled circuits: {len(df[df["status"] == "Enabled"])}')
    print(f'Disabled circuits: {len(df[df["status"] == "Disabled"])}')
    
    # Provider breakdown
    print(f'\nProvider breakdown:')
    provider_counts = df.groupby(['provider_name', 'data_source']).size().reset_index(name='count')
    for idx, row in provider_counts.iterrows():
        print(f'  {row["provider_name"]} ({row["data_source"]}): {row["count"]} circuits')
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    query_frontier_circuits()