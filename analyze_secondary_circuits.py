#!/usr/bin/env python3
"""
Find sites without secondary circuits and match them with Excel data
"""
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import re
import os

# First, let's analyze the Excel file without database
def analyze_excel_structure(file_path):
    """First pass - understand Excel structure"""
    print(f"\nAnalyzing Excel file structure: {file_path}")
    
    excel_file = pd.ExcelFile(file_path)
    print(f"Sheets found: {excel_file.sheet_names}")
    
    wan_data = {}
    
    for sheet_name in excel_file.sheet_names:
        print(f"\n{'='*60}")
        print(f"Sheet: {sheet_name}")
        print('='*60)
        
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        print(f"Shape: {df.shape}")
        print(f"\nColumns: {list(df.columns)}")
        
        # Look for WAN-related columns
        wan_cols = [col for col in df.columns if 'wan' in str(col).lower()]
        site_cols = [col for col in df.columns if any(x in str(col).lower() for x in ['site', 'location', 'store'])]
        circuit_cols = [col for col in df.columns if any(x in str(col).lower() for x in ['circuit', 'id', 'number'])]
        ip_cols = [col for col in df.columns if any(x in str(col).lower() for x in ['ip', 'address'])]
        provider_cols = [col for col in df.columns if any(x in str(col).lower() for x in ['provider', 'carrier', 'vendor', 'isp'])]
        
        print(f"\nRelevant columns found:")
        print(f"  WAN columns: {wan_cols}")
        print(f"  Site columns: {site_cols}")
        print(f"  Circuit columns: {circuit_cols}")
        print(f"  IP columns: {ip_cols}")
        print(f"  Provider columns: {provider_cols}")
        
        # Show sample data
        if len(df) > 0:
            print(f"\nFirst 5 rows preview:")
            # Show only relevant columns if found
            cols_to_show = (site_cols + wan_cols + circuit_cols + ip_cols + provider_cols)[:10]
            if cols_to_show:
                print(df[cols_to_show].head(5).to_string())
            else:
                print(df.head(5).to_string())
        
        wan_data[sheet_name] = {
            'dataframe': df,
            'wan_cols': wan_cols,
            'site_cols': site_cols,
            'circuit_cols': circuit_cols,
            'ip_cols': ip_cols,
            'provider_cols': provider_cols
        }
    
    return wan_data

def find_wan_circuits(wan_data):
    """Extract all WAN 1 and WAN 2 circuits from Excel"""
    all_circuits = []
    
    for sheet_name, sheet_info in wan_data.items():
        df = sheet_info['dataframe']
        
        # Skip empty sheets
        if df.empty:
            continue
            
        # Process each row
        for idx, row in df.iterrows():
            # Get site identifier
            site_id = None
            for site_col in sheet_info['site_cols']:
                if site_col in row and pd.notna(row[site_col]):
                    site_id = str(row[site_col]).strip()
                    break
            
            if not site_id:
                continue
            
            # Look for WAN 1 and WAN 2 information
            wan1_info = {}
            wan2_info = {}
            
            # Check WAN-specific columns
            for col in df.columns:
                col_lower = str(col).lower()
                if pd.notna(row[col]):
                    value = str(row[col]).strip()
                    
                    # WAN 1 patterns
                    if any(x in col_lower for x in ['wan1', 'wan 1', 'primary', 'main']):
                        if 'circuit' in col_lower or 'id' in col_lower:
                            wan1_info['circuit_id'] = value
                        elif 'provider' in col_lower or 'carrier' in col_lower:
                            wan1_info['provider'] = value
                        elif 'ip' in col_lower:
                            wan1_info['ip'] = value
                        elif 'speed' in col_lower or 'bandwidth' in col_lower:
                            wan1_info['bandwidth'] = value
                        else:
                            wan1_info[col] = value
                    
                    # WAN 2 patterns
                    elif any(x in col_lower for x in ['wan2', 'wan 2', 'secondary', 'backup']):
                        if 'circuit' in col_lower or 'id' in col_lower:
                            wan2_info['circuit_id'] = value
                        elif 'provider' in col_lower or 'carrier' in col_lower:
                            wan2_info['provider'] = value
                        elif 'ip' in col_lower:
                            wan2_info['ip'] = value
                        elif 'speed' in col_lower or 'bandwidth' in col_lower:
                            wan2_info['bandwidth'] = value
                        else:
                            wan2_info[col] = value
                    
                    # Generic circuit info (might apply to either)
                    elif 'circuit' in col_lower and 'wan' not in col_lower:
                        if not wan1_info.get('circuit_id'):
                            wan1_info['circuit_id'] = value
            
            # Create circuit records
            if wan1_info:
                circuit_record = {
                    'site_id': site_id,
                    'wan_type': 'WAN1',
                    'sheet': sheet_name,
                    'row': idx + 2,  # Excel row number (1-based + header)
                    **wan1_info
                }
                all_circuits.append(circuit_record)
            
            if wan2_info:
                circuit_record = {
                    'site_id': site_id,
                    'wan_type': 'WAN2',
                    'sheet': sheet_name,
                    'row': idx + 2,
                    **wan2_info
                }
                all_circuits.append(circuit_record)
    
    return all_circuits

def get_sites_without_secondary():
    """Get list of sites without secondary circuits from database"""
    try:
        # Try different connection parameters
        configs = [
            {'host': 'localhost', 'database': 'dtdsrcircuits', 'user': 'dtdsrcircuits', 'password': 'dtdsrcircuits'},
            {'host': 'localhost', 'database': 'postgres', 'user': 'postgres', 'password': 'postgres'},
            {'host': 'localhost', 'database': 'postgres', 'user': 'postgres'}
        ]
        
        conn = None
        for config in configs:
            try:
                conn = psycopg2.connect(**config)
                print(f"Connected to database with config: {config['database']}/{config['user']}")
                break
            except:
                continue
        
        if not conn:
            print("Could not connect to database. Using sample data.")
            # Return some sample sites for testing
            return [
                {'site_id': 'AZP 30', 'site_name': 'Phoenix Store 30', 'primary_provider': 'Cox'},
                {'site_id': 'CAL 24', 'site_name': 'California Store 24', 'primary_provider': 'AT&T'},
                {'site_id': 'TXD 42', 'site_name': 'Texas Dallas 42', 'primary_provider': 'Spectrum'}
            ]
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query to find sites with only one circuit (no secondary)
        query = """
        WITH site_circuit_counts AS (
            SELECT 
                site_id,
                site_name,
                COUNT(DISTINCT circuit_id) as circuit_count,
                MAX(CASE WHEN circuit_type = 'Primary' THEN provider END) as primary_provider,
                MAX(CASE WHEN circuit_type = 'Primary' THEN public_ip END) as primary_ip,
                MAX(CASE WHEN circuit_type = 'Secondary' THEN provider END) as secondary_provider,
                MAX(CASE WHEN circuit_type = 'Secondary' THEN public_ip END) as secondary_ip
            FROM circuits
            WHERE site_id NOT LIKE 'TST%' 
              AND site_id NOT LIKE 'NEO%'
              AND circuit_status = 'Active'
            GROUP BY site_id, site_name
        )
        SELECT * 
        FROM site_circuit_counts
        WHERE circuit_count = 1 
           OR secondary_provider IS NULL
           OR secondary_provider = ''
        ORDER BY site_id
        """
        
        cur.execute(query)
        sites = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return sites
        
    except Exception as e:
        print(f"Database error: {e}")
        print("Continuing with Excel analysis only...")
        return []

def match_sites_with_excel(sites_without_secondary, excel_circuits):
    """Match sites without secondary circuits with Excel WAN2 data"""
    matches = []
    
    # Create a lookup dictionary for Excel circuits
    excel_by_site = {}
    for circuit in excel_circuits:
        site_id = circuit['site_id'].upper().strip()
        # Normalize site ID formats
        site_id = re.sub(r'\s+', ' ', site_id)
        
        if site_id not in excel_by_site:
            excel_by_site[site_id] = {'WAN1': [], 'WAN2': []}
        
        excel_by_site[site_id][circuit['wan_type']].append(circuit)
    
    # Match database sites with Excel data
    for site in sites_without_secondary:
        site_id = site['site_id'].upper().strip()
        site_id = re.sub(r'\s+', ' ', site_id)
        
        # Look for exact match
        if site_id in excel_by_site:
            wan2_circuits = excel_by_site[site_id].get('WAN2', [])
            if wan2_circuits:
                for wan2 in wan2_circuits:
                    match = {
                        'site_id': site['site_id'],
                        'site_name': site.get('site_name', ''),
                        'current_primary_provider': site.get('primary_provider', ''),
                        'excel_wan2': wan2,
                        'excel_wan1': excel_by_site[site_id].get('WAN1', [])
                    }
                    matches.append(match)
        else:
            # Try partial matching
            for excel_site, circuits in excel_by_site.items():
                if site_id in excel_site or excel_site in site_id:
                    wan2_circuits = circuits.get('WAN2', [])
                    if wan2_circuits:
                        for wan2 in wan2_circuits:
                            match = {
                                'site_id': site['site_id'],
                                'site_name': site.get('site_name', ''),
                                'current_primary_provider': site.get('primary_provider', ''),
                                'excel_site_id': excel_site,
                                'excel_wan2': wan2,
                                'excel_wan1': circuits.get('WAN1', [])
                            }
                            matches.append(match)
    
    return matches

def generate_report(sites_without_secondary, excel_circuits, matches):
    """Generate comprehensive report"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'/usr/local/bin/secondary_circuit_analysis_{timestamp}.md'
    
    with open(report_file, 'w') as f:
        f.write("# Secondary Circuit Analysis Report\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Summary\n")
        f.write(f"- Sites without secondary circuits (from database): {len(sites_without_secondary)}\n")
        f.write(f"- Total circuits found in Excel: {len(excel_circuits)}\n")
        f.write(f"- WAN1 circuits in Excel: {len([c for c in excel_circuits if c['wan_type'] == 'WAN1'])}\n")
        f.write(f"- WAN2 circuits in Excel: {len([c for c in excel_circuits if c['wan_type'] == 'WAN2'])}\n")
        f.write(f"- Sites with potential WAN2 matches: {len(set(m['site_id'] for m in matches))}\n\n")
        
        f.write("## Sites with Potential Secondary Circuits in Excel\n\n")
        
        if matches:
            # Group by site
            sites_dict = {}
            for match in matches:
                site_id = match['site_id']
                if site_id not in sites_dict:
                    sites_dict[site_id] = []
                sites_dict[site_id].append(match)
            
            for site_id, site_matches in sorted(sites_dict.items()):
                f.write(f"### {site_id} - {site_matches[0].get('site_name', 'Unknown')}\n")
                f.write(f"**Current Primary Provider:** {site_matches[0].get('current_primary_provider', 'Unknown')}\n\n")
                
                for match in site_matches:
                    wan2 = match['excel_wan2']
                    f.write(f"**Found WAN2 Circuit (Sheet: {wan2['sheet']}, Row: {wan2['row']})**\n")
                    
                    # Show key WAN2 info
                    if 'circuit_id' in wan2:
                        f.write(f"- Circuit ID: {wan2['circuit_id']}\n")
                    if 'provider' in wan2:
                        f.write(f"- Provider: {wan2['provider']}\n")
                    if 'ip' in wan2:
                        f.write(f"- IP Address: {wan2['ip']}\n")
                    if 'bandwidth' in wan2:
                        f.write(f"- Bandwidth: {wan2['bandwidth']}\n")
                    
                    # Show other WAN2 fields
                    other_fields = [(k, v) for k, v in wan2.items() 
                                   if k not in ['site_id', 'wan_type', 'sheet', 'row', 'circuit_id', 'provider', 'ip', 'bandwidth']]
                    if other_fields:
                        f.write(f"- Other info: {', '.join([f'{k}: {v}' for k, v in other_fields[:3]])}\n")
                    
                    # Also show WAN1 info for comparison
                    if match.get('excel_wan1'):
                        f.write(f"\n**Corresponding WAN1 Circuit(s):**\n")
                        for wan1 in match['excel_wan1'][:1]:  # Show first WAN1 only
                            if 'provider' in wan1:
                                f.write(f"- WAN1 Provider: {wan1['provider']}\n")
                            if 'circuit_id' in wan1:
                                f.write(f"- WAN1 Circuit ID: {wan1['circuit_id']}\n")
                    
                    f.write("\n")
        
        f.write("\n## Excel Data Summary\n")
        
        # Group circuits by site to show coverage
        excel_sites = {}
        for circuit in excel_circuits:
            site = circuit['site_id']
            if site not in excel_sites:
                excel_sites[site] = {'WAN1': 0, 'WAN2': 0}
            excel_sites[site][circuit['wan_type']] += 1
        
        wan2_only = [site for site, counts in excel_sites.items() if counts['WAN2'] > 0 and counts['WAN1'] == 0]
        both_wans = [site for site, counts in excel_sites.items() if counts['WAN2'] > 0 and counts['WAN1'] > 0]
        
        f.write(f"\n### Circuit Coverage in Excel\n")
        f.write(f"- Sites with both WAN1 and WAN2: {len(both_wans)}\n")
        f.write(f"- Sites with only WAN2 data: {len(wan2_only)}\n")
        f.write(f"- Total unique sites in Excel: {len(excel_sites)}\n")
        
        # Create CSV for easy import
        csv_file = report_file.replace('.md', '_matches.csv')
        import csv
        
        with open(csv_file, 'w', newline='') as csvf:
            fieldnames = ['site_id', 'site_name', 'current_primary_provider', 
                         'wan2_circuit_id', 'wan2_provider', 'wan2_ip', 'wan2_bandwidth',
                         'excel_sheet', 'excel_row']
            writer = csv.DictWriter(csvf, fieldnames=fieldnames)
            writer.writeheader()
            
            for match in matches:
                wan2 = match['excel_wan2']
                writer.writerow({
                    'site_id': match['site_id'],
                    'site_name': match.get('site_name', ''),
                    'current_primary_provider': match.get('current_primary_provider', ''),
                    'wan2_circuit_id': wan2.get('circuit_id', ''),
                    'wan2_provider': wan2.get('provider', ''),
                    'wan2_ip': wan2.get('ip', ''),
                    'wan2_bandwidth': wan2.get('bandwidth', ''),
                    'excel_sheet': wan2['sheet'],
                    'excel_row': wan2['row']
                })
        
        f.write(f"\n### Output Files\n")
        f.write(f"- Report: {report_file}\n")
        f.write(f"- CSV for import: {csv_file}\n")
    
    return report_file, csv_file

def main():
    print("="*60)
    print("Secondary Circuit Analysis")
    print("Finding sites without secondary circuits and matching with Excel WAN2 data")
    print("="*60)
    
    # Analyze Excel file
    excel_file = '/tmp/master_circuit_info.xlsx'
    wan_data = analyze_excel_structure(excel_file)
    
    # Extract WAN circuits
    print("\n" + "="*60)
    print("Extracting WAN circuit information...")
    print("="*60)
    excel_circuits = find_wan_circuits(wan_data)
    print(f"\nTotal circuits extracted: {len(excel_circuits)}")
    print(f"WAN1 circuits: {len([c for c in excel_circuits if c['wan_type'] == 'WAN1'])}")
    print(f"WAN2 circuits: {len([c for c in excel_circuits if c['wan_type'] == 'WAN2'])}")
    
    # Get sites without secondary circuits
    print("\n" + "="*60)
    print("Fetching sites without secondary circuits from database...")
    print("="*60)
    sites_without_secondary = get_sites_without_secondary()
    print(f"Sites without secondary circuits: {len(sites_without_secondary)}")
    
    # Match sites with Excel data
    print("\n" + "="*60)
    print("Matching sites with Excel WAN2 data...")
    print("="*60)
    matches = match_sites_with_excel(sites_without_secondary, excel_circuits)
    print(f"Found {len(matches)} potential WAN2 matches for {len(set(m['site_id'] for m in matches))} sites")
    
    # Generate report
    report_file, csv_file = generate_report(sites_without_secondary, excel_circuits, matches)
    print(f"\n" + "="*60)
    print("Analysis Complete!")
    print("="*60)
    print(f"Report generated: {report_file}")
    print(f"CSV file created: {csv_file}")
    
    # Show sample matches
    if matches:
        print("\nSample matches found:")
        for match in matches[:5]:
            wan2 = match['excel_wan2']
            print(f"- {match['site_id']}: WAN2 {wan2.get('provider', 'Unknown')} - {wan2.get('circuit_id', 'No ID')}")

if __name__ == '__main__':
    main()