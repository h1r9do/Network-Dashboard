#!/usr/bin/env python3
"""
Detailed analysis of CSV files to understand actual enablement patterns
"""

import pandas as pd
import glob
from datetime import datetime

def analyze_all_csvs():
    # Get all CSV files since 4/28
    csv_files = sorted(glob.glob('/var/www/html/circuitinfo/tracking_data_*.csv'))
    csv_files = [f for f in csv_files if '2025-04-28' <= f.split('tracking_data_')[1][:10] <= '2025-06-27']
    
    print(f'Analyzing {len(csv_files)} CSV files from 4/28 to 6/27\n')
    
    previous_df = None
    daily_results = []
    
    for csv_file in csv_files:
        date = csv_file.split('tracking_data_')[1][:10]
        df = pd.read_csv(csv_file, low_memory=False)
        
        # Count current statuses
        ready_count = 0
        enabled_count = 0
        
        # Track by site name for transitions
        ready_to_enabled = []
        
        if 'status' in df.columns:
            for _, row in df.iterrows():
                status = str(row.get('status', '')).lower().strip()
                site_name = str(row.get('Site Name', '')).strip()
                
                if 'ready for enablement' in status:
                    ready_count += 1
                elif 'enabled' in status:
                    enabled_count += 1
                
                # Check transitions
                if previous_df is not None and site_name:
                    # Find this site in previous day
                    prev_row = previous_df[previous_df['Site Name'] == site_name]
                    if not prev_row.empty:
                        prev_status = str(prev_row.iloc[0].get('status', '')).lower().strip()
                        
                        # Check for Ready -> Enabled transition
                        if ('ready for enablement' in prev_status and 
                            'enabled' in status and 
                            'ready for enablement' not in status):
                            ready_to_enabled.append(site_name)
        
        daily_results.append({
            'date': date,
            'total': len(df),
            'ready': ready_count,
            'enabled': enabled_count,
            'transitions': len(ready_to_enabled),
            'examples': ready_to_enabled[:3]
        })
        
        previous_df = df
    
    # Print all results
    print("Date       | Total | Ready | Enabled | Ready->Enabled | Examples")
    print("-" * 80)
    
    total_transitions = 0
    days_with_transitions = 0
    
    for result in daily_results:
        if result['transitions'] > 0:
            days_with_transitions += 1
            total_transitions += result['transitions']
            examples = ', '.join(result['examples'][:2])
            print(f"{result['date']} | {result['total']:5} | {result['ready']:5} | {result['enabled']:7} | {result['transitions']:14} | {examples}")
        else:
            print(f"{result['date']} | {result['total']:5} | {result['ready']:5} | {result['enabled']:7} | {result['transitions']:14} |")
    
    print("\nSummary:")
    print(f"Total days analyzed: {len(daily_results)}")
    print(f"Days with Ready->Enabled transitions: {days_with_transitions}")
    print(f"Total Ready->Enabled transitions: {total_transitions}")
    print(f"Average transitions per day: {total_transitions / len(daily_results):.2f}")
    print(f"Average transitions on days with transitions: {total_transitions / days_with_transitions:.2f}")

if __name__ == "__main__":
    analyze_all_csvs()