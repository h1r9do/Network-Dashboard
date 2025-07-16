#!/usr/bin/env python3
"""
Analyze master circuit info Excel file and match with sites needing circuits
"""
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import re

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dtdsrcircuits',
    'user': 'dtdsrcircuits',
    'password': 'dtdsrcircuits'
}

def clean_site_id(site_id):
    """Normalize site ID for matching"""
    if not site_id:
        return ""
    # Remove extra spaces and standardize format
    site_id = str(site_id).strip().upper()
    # Handle variations like "AZP 30" vs "AZP30"
    site_id = re.sub(r'\s+', ' ', site_id)
    return site_id

def get_sites_needing_circuits():
    """Get sites from database that need circuit information"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get sites with missing or incomplete circuit information
    query = """
    SELECT DISTINCT
        c.site_id,
        c.site_name,
        c.provider,
        c.circuit_status,
        c.circuit_type,
        c.bandwidth_mbps,
        c.monthly_cost,
        c.account_number,
        c.circuit_id,
        c.has_circuit_id,
        c.public_ip,
        COUNT(*) as circuit_count
    FROM circuits c
    WHERE 
        -- Sites with missing critical information
        (c.circuit_id IS NULL OR c.circuit_id = '' OR c.circuit_id = 'N/A'
         OR c.provider IS NULL OR c.provider = '' OR c.provider = 'Unknown'
         OR c.bandwidth_mbps IS NULL OR c.bandwidth_mbps = ''
         OR c.monthly_cost IS NULL OR c.monthly_cost = 0)
        -- Exclude test networks
        AND c.site_id NOT LIKE 'TST%'
        AND c.site_id NOT LIKE 'NEO%'
    GROUP BY 
        c.site_id, c.site_name, c.provider, c.circuit_status, 
        c.circuit_type, c.bandwidth_mbps, c.monthly_cost,
        c.account_number, c.circuit_id, c.has_circuit_id, c.public_ip
    ORDER BY c.site_id
    """
    
    cur.execute(query)
    sites = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return sites

def analyze_excel_file(file_path):
    """Analyze the Excel file and extract circuit information"""
    print(f"\nAnalyzing Excel file: {file_path}")
    
    # Read all sheets
    excel_file = pd.ExcelFile(file_path)
    print(f"Available sheets: {excel_file.sheet_names}")
    
    all_circuit_data = []
    
    for sheet_name in excel_file.sheet_names:
        print(f"\nAnalyzing sheet: {sheet_name}")
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        print(f"Columns in {sheet_name}: {list(df.columns)}")
        print(f"Number of rows: {len(df)}")
        
        # Show first few rows to understand structure
        if len(df) > 0:
            print(f"\nFirst 3 rows of {sheet_name}:")
            print(df.head(3).to_string())
        
        # Try to identify site/circuit columns
        site_columns = [col for col in df.columns if any(x in str(col).lower() for x in ['site', 'location', 'store'])]
        circuit_columns = [col for col in df.columns if any(x in str(col).lower() for x in ['circuit', 'wan', 'mpls'])]
        provider_columns = [col for col in df.columns if any(x in str(col).lower() for x in ['provider', 'carrier', 'vendor'])]
        bandwidth_columns = [col for col in df.columns if any(x in str(col).lower() for x in ['bandwidth', 'speed', 'mbps', 'gbps'])]
        cost_columns = [col for col in df.columns if any(x in str(col).lower() for x in ['cost', 'price', 'mrc', 'monthly'])]
        
        print(f"\nIdentified columns:")
        print(f"  Site columns: {site_columns}")
        print(f"  Circuit columns: {circuit_columns}")
        print(f"  Provider columns: {provider_columns}")
        print(f"  Bandwidth columns: {bandwidth_columns}")
        print(f"  Cost columns: {cost_columns}")
        
        # Store sheet data for matching
        sheet_data = {
            'sheet_name': sheet_name,
            'dataframe': df,
            'site_columns': site_columns,
            'circuit_columns': circuit_columns,
            'provider_columns': provider_columns,
            'bandwidth_columns': bandwidth_columns,
            'cost_columns': cost_columns
        }
        all_circuit_data.append(sheet_data)
    
    return all_circuit_data

def match_sites_with_excel(sites_needing_circuits, excel_data):
    """Match sites from database with Excel data"""
    matches = []
    no_matches = []
    
    for site in sites_needing_circuits:
        site_id = clean_site_id(site['site_id'])
        found_match = False
        
        for sheet_data in excel_data:
            df = sheet_data['dataframe']
            
            # Try to find site in each identified site column
            for site_col in sheet_data['site_columns']:
                if site_col in df.columns:
                    # Clean the column values for matching
                    df['cleaned_site'] = df[site_col].apply(lambda x: clean_site_id(x) if pd.notna(x) else '')
                    
                    # Look for exact match or partial match
                    exact_matches = df[df['cleaned_site'] == site_id]
                    partial_matches = df[df['cleaned_site'].str.contains(site_id, na=False)] if len(exact_matches) == 0 else pd.DataFrame()
                    
                    if len(exact_matches) > 0 or len(partial_matches) > 0:
                        matched_df = exact_matches if len(exact_matches) > 0 else partial_matches
                        
                        for _, row in matched_df.iterrows():
                            match_info = {
                                'site_id': site['site_id'],
                                'site_name': site['site_name'],
                                'current_provider': site['provider'],
                                'current_circuit_id': site['circuit_id'],
                                'current_bandwidth': site['bandwidth_mbps'],
                                'current_cost': site['monthly_cost'],
                                'sheet_name': sheet_data['sheet_name'],
                                'excel_site_id': row.get(site_col, ''),
                                'excel_data': {}
                            }
                            
                            # Extract circuit information from Excel
                            for col_type, col_list in [
                                ('circuit', sheet_data['circuit_columns']),
                                ('provider', sheet_data['provider_columns']),
                                ('bandwidth', sheet_data['bandwidth_columns']),
                                ('cost', sheet_data['cost_columns'])
                            ]:
                                for col in col_list:
                                    if col in row.index and pd.notna(row[col]):
                                        match_info['excel_data'][col] = str(row[col])
                            
                            # Get all columns for this row in case we missed something
                            for col in df.columns:
                                if col not in ['cleaned_site'] and pd.notna(row[col]):
                                    match_info['excel_data'][f'other_{col}'] = str(row[col])
                            
                            matches.append(match_info)
                            found_match = True
        
        if not found_match:
            no_matches.append({
                'site_id': site['site_id'],
                'site_name': site['site_name'],
                'current_info': {
                    'provider': site['provider'],
                    'circuit_id': site['circuit_id'],
                    'bandwidth': site['bandwidth_mbps'],
                    'cost': site['monthly_cost']
                }
            })
    
    return matches, no_matches

def generate_report(sites_needing_circuits, excel_data, matches, no_matches):
    """Generate comprehensive report"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'/usr/local/bin/circuit_matching_report_{timestamp}.md'
    
    with open(report_file, 'w') as f:
        f.write("# Circuit Information Matching Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Summary\n")
        f.write(f"- Total sites needing circuit information: {len(sites_needing_circuits)}\n")
        f.write(f"- Sites matched in Excel file: {len(set(m['site_id'] for m in matches))}\n")
        f.write(f"- Sites not found in Excel: {len(no_matches)}\n")
        f.write(f"- Total matches found: {len(matches)}\n\n")
        
        f.write("## Excel File Structure\n")
        for sheet_data in excel_data:
            f.write(f"\n### Sheet: {sheet_data['sheet_name']}\n")
            df = sheet_data['dataframe']
            f.write(f"- Rows: {len(df)}\n")
            f.write(f"- Columns: {len(df.columns)}\n")
            f.write(f"- Column names: {', '.join(df.columns)}\n")
        
        f.write("\n## Matched Sites\n")
        if matches:
            # Group by site
            sites_dict = {}
            for match in matches:
                site_id = match['site_id']
                if site_id not in sites_dict:
                    sites_dict[site_id] = []
                sites_dict[site_id].append(match)
            
            for site_id, site_matches in sorted(sites_dict.items()):
                f.write(f"\n### {site_id} - {site_matches[0]['site_name']}\n")
                f.write(f"**Current Database Info:**\n")
                f.write(f"- Provider: {site_matches[0]['current_provider']}\n")
                f.write(f"- Circuit ID: {site_matches[0]['current_circuit_id']}\n")
                f.write(f"- Bandwidth: {site_matches[0]['current_bandwidth']}\n")
                f.write(f"- Monthly Cost: ${site_matches[0]['current_cost']}\n")
                
                f.write(f"\n**Excel Matches:**\n")
                for i, match in enumerate(site_matches, 1):
                    f.write(f"\n*Match {i} from sheet '{match['sheet_name']}'*\n")
                    
                    # Show relevant data
                    circuit_info = [v for k, v in match['excel_data'].items() if 'circuit' in k.lower()]
                    provider_info = [v for k, v in match['excel_data'].items() if 'provider' in k.lower() or 'carrier' in k.lower()]
                    bandwidth_info = [v for k, v in match['excel_data'].items() if 'bandwidth' in k.lower() or 'speed' in k.lower()]
                    cost_info = [v for k, v in match['excel_data'].items() if 'cost' in k.lower() or 'price' in k.lower() or 'mrc' in k.lower()]
                    
                    if circuit_info:
                        f.write(f"- Circuit Info: {', '.join(set(circuit_info))}\n")
                    if provider_info:
                        f.write(f"- Provider Info: {', '.join(set(provider_info))}\n")
                    if bandwidth_info:
                        f.write(f"- Bandwidth Info: {', '.join(set(bandwidth_info))}\n")
                    if cost_info:
                        f.write(f"- Cost Info: {', '.join(set(cost_info))}\n")
                    
                    # Show first 5 other fields
                    other_fields = [(k, v) for k, v in match['excel_data'].items() 
                                   if not any(x in k.lower() for x in ['circuit', 'provider', 'carrier', 'bandwidth', 'speed', 'cost', 'price', 'mrc'])]
                    if other_fields:
                        f.write("- Other fields: ")
                        f.write(", ".join([f"{k}: {v}" for k, v in other_fields[:5]]))
                        if len(other_fields) > 5:
                            f.write(f" ... and {len(other_fields) - 5} more fields")
                        f.write("\n")
        
        f.write("\n## Sites Not Found in Excel\n")
        if no_matches:
            f.write("These sites need circuit information but were not found in the Excel file:\n\n")
            for site in no_matches:
                f.write(f"- **{site['site_id']}** ({site['site_name']})")
                if site['current_info']['provider'] and site['current_info']['provider'] != 'Unknown':
                    f.write(f" - Current: {site['current_info']['provider']}")
                f.write("\n")
        
        f.write("\n## Recommendations\n")
        f.write("1. Review matched sites to verify Excel data accuracy\n")
        f.write("2. Update database with confirmed Excel information\n")
        f.write("3. Investigate sites not found in Excel file\n")
        f.write("4. Consider requesting updated circuit inventory for missing sites\n")
    
    return report_file

def main():
    print("Starting circuit information analysis...")
    
    # Get sites needing circuit information
    print("\nFetching sites from database that need circuit information...")
    sites_needing_circuits = get_sites_needing_circuits()
    print(f"Found {len(sites_needing_circuits)} sites needing circuit information")
    
    # Analyze Excel file
    excel_file = '/tmp/master_circuit_info.xlsx'
    excel_data = analyze_excel_file(excel_file)
    
    # Match sites with Excel data
    print("\nMatching sites with Excel data...")
    matches, no_matches = match_sites_with_excel(sites_needing_circuits, excel_data)
    
    print(f"\nMatching complete:")
    print(f"- Matched sites: {len(set(m['site_id'] for m in matches))}")
    print(f"- Total matches: {len(matches)}")
    print(f"- No matches: {len(no_matches)}")
    
    # Generate report
    report_file = generate_report(sites_needing_circuits, excel_data, matches, no_matches)
    print(f"\nReport generated: {report_file}")
    
    # Also create a CSV for easy import
    if matches:
        csv_file = report_file.replace('.md', '_matches.csv')
        import csv
        
        with open(csv_file, 'w', newline='') as f:
            fieldnames = ['site_id', 'site_name', 'sheet_name', 'excel_circuit_id', 
                         'excel_provider', 'excel_bandwidth', 'excel_cost', 'all_excel_data']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for match in matches:
                # Extract specific fields
                circuit_ids = [v for k, v in match['excel_data'].items() if 'circuit' in k.lower()]
                providers = [v for k, v in match['excel_data'].items() if 'provider' in k.lower() or 'carrier' in k.lower()]
                bandwidths = [v for k, v in match['excel_data'].items() if 'bandwidth' in k.lower() or 'speed' in k.lower()]
                costs = [v for k, v in match['excel_data'].items() if 'cost' in k.lower() or 'price' in k.lower()]
                
                writer.writerow({
                    'site_id': match['site_id'],
                    'site_name': match['site_name'],
                    'sheet_name': match['sheet_name'],
                    'excel_circuit_id': ', '.join(circuit_ids) if circuit_ids else '',
                    'excel_provider': ', '.join(providers) if providers else '',
                    'excel_bandwidth': ', '.join(bandwidths) if bandwidths else '',
                    'excel_cost': ', '.join(costs) if costs else '',
                    'all_excel_data': json.dumps(match['excel_data'])
                })
        
        print(f"CSV file created: {csv_file}")

if __name__ == '__main__':
    main()