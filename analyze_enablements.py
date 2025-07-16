#!/usr/bin/env python3
"""
Manual enablement analysis tool to verify the math
"""

import pandas as pd
import os
from collections import defaultdict

def analyze_enablements():
    """Analyze enablement transitions manually"""
    
    csv_files = [
        '/var/www/html/circuitinfo/tracking_data_2025-06-23.csv',
        '/var/www/html/circuitinfo/tracking_data_2025-06-24.csv', 
        '/var/www/html/circuitinfo/tracking_data_2025-06-25.csv'
    ]
    
    daily_data = {}
    
    for csv_file in csv_files:
        print(f"\n=== Analyzing {csv_file} ===")
        
        # Extract date from filename
        date = csv_file.split('_')[-1].replace('.csv', '')
        
        # Read CSV
        df = pd.read_csv(csv_file, low_memory=False)
        print(f"Total rows: {len(df)}")
        
        # Create circuit tracking key (Site Name + Site ID + Circuit Purpose)
        circuits = {}
        ready_count = 0
        enabled_count = 0
        
        for _, row in df.iterrows():
            site_name = str(row.get('Site Name', '')).strip()
            site_id = str(row.get('Site ID', '')).strip()
            circuit_purpose = str(row.get('Circuit Purpose', '')).strip()
            status = str(row.get('status', '')).strip()
            
            if not site_name or not site_id or not circuit_purpose:
                continue
                
            # Create unique key
            key = f"{site_name}||{site_id}||{circuit_purpose}"
            
            circuits[key] = {
                'site_name': site_name,
                'site_id': site_id, 
                'circuit_purpose': circuit_purpose,
                'status': status
            }
            
            # Count statuses
            status_lower = status.lower()
            if 'ready for enablement' in status_lower:
                ready_count += 1
                print(f"  READY: {site_name} ({site_id}) - {circuit_purpose}")
            elif any(word in status_lower for word in ['enabled', 'activated', 'service activated']):
                enabled_count += 1
        
        print(f"Ready for enablement: {ready_count}")
        print(f"Enabled circuits: {enabled_count}")
        
        daily_data[date] = {
            'circuits': circuits,
            'ready_count': ready_count,
            'enabled_count': enabled_count
        }
    
    # Now compare day-to-day for actual enablements
    print(f"\n=== ENABLEMENT TRANSITIONS ===")
    
    dates = sorted(daily_data.keys())
    for i in range(1, len(dates)):
        prev_date = dates[i-1]
        curr_date = dates[i]
        
        prev_circuits = daily_data[prev_date]['circuits']
        curr_circuits = daily_data[curr_date]['circuits']
        
        enablements = 0
        
        print(f"\n{prev_date} → {curr_date}:")
        
        for key in curr_circuits:
            if key in prev_circuits:
                prev_status = prev_circuits[key]['status'].lower()
                curr_status = curr_circuits[key]['status'].lower()
                
                # Check for transition from "ready for enablement" to "enabled"
                if ('ready for enablement' in prev_status and 
                    any(word in curr_status for word in ['enabled', 'activated', 'service activated'])):
                    
                    circuit = curr_circuits[key]
                    print(f"  ENABLEMENT: {circuit['site_name']} ({circuit['site_id']}) - {circuit['circuit_purpose']}")
                    print(f"    {prev_status} → {curr_status}")
                    enablements += 1
        
        print(f"Total enablements: {enablements}")
        print(f"Ready queue on {curr_date}: {daily_data[curr_date]['ready_count']}")

if __name__ == "__main__":
    analyze_enablements()