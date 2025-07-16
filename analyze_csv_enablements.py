#!/usr/bin/env python3
"""
Analyze CSV files to understand the actual enablement patterns
"""

import pandas as pd
import glob
from datetime import datetime

def analyze_csv_enablements():
    # Get all CSV files since 4/28
    csv_files = sorted(glob.glob('/var/www/html/circuitinfo/tracking_data_*.csv'))
    csv_files = [f for f in csv_files if '2025-04-28' <= f.split('tracking_data_')[1][:10] <= '2025-06-27']
    
    print(f'Analyzing {len(csv_files)} CSV files from 4/28 to 6/27\n')
    
    previous_df = None
    daily_enablements = []
    total_enablements = 0
    
    for csv_file in csv_files:
        date = csv_file.split('tracking_data_')[1][:10]
        df = pd.read_csv(csv_file, low_memory=False)
        
        # Count current statuses
        ready_count = df[df['status'].str.lower().str.contains('ready for enablement', na=False)].shape[0]
        enabled_count = df[df['status'].str.lower().str.contains('enabled', na=False) & 
                          ~df['status'].str.lower().str.contains('ready for enablement', na=False)].shape[0]
        total_count = len(df)
        
        # Compare with previous day to find NEW enablements
        new_enablements = 0
        if previous_df is not None:
            # Create lookup dictionaries by Site Name
            prev_statuses = {}
            curr_statuses = {}
            
            # Build previous day lookup
            for _, row in previous_df.iterrows():
                site_name = str(row.get('Site Name', '')).strip()
                if site_name:
                    prev_statuses[site_name] = str(row.get('status', '')).lower().strip()
            
            # Check current day for transitions
            for _, row in df.iterrows():
                site_name = str(row.get('Site Name', '')).strip()
                if site_name:
                    curr_status = str(row.get('status', '')).lower().strip()
                    curr_statuses[site_name] = curr_status
                    
                    prev_status = prev_statuses.get(site_name, '')
                    
                    # Check if this site went from "ready for enablement" to "enabled"
                    was_ready = 'ready for enablement' in prev_status
                    is_enabled = 'enabled' in curr_status and 'ready for enablement' not in curr_status
                    
                    # Also check if it wasn't already enabled
                    was_not_enabled = 'enabled' not in prev_status
                    
                    if was_ready and is_enabled and was_not_enabled:
                        new_enablements += 1
                        if new_enablements <= 3:  # Show first few examples
                            print(f"  Example: {site_name} changed from '{prev_status}' to '{curr_status}'")
        
        daily_enablements.append({
            'date': date,
            'total': total_count,
            'enabled': enabled_count,
            'ready': ready_count,
            'new_enablements': new_enablements
        })
        
        total_enablements += new_enablements
        
        if new_enablements > 0 or ready_count > 0:
            print(f'{date}: Total={total_count}, Enabled={enabled_count}, Ready={ready_count}, NEW enablements={new_enablements}')
        
        previous_df = df
    
    print(f'\nSummary:')
    print(f'Total NEW enablements (Ready->Enabled transitions): {total_enablements}')
    print(f'Average per day: {total_enablements / len(csv_files):.1f}')
    
    # Show last 7 days
    print('\nLast 7 days detail:')
    for day in daily_enablements[-7:]:
        print(f"  {day['date']}: {day['new_enablements']} new enablements, {day['ready']} ready")

if __name__ == "__main__":
    analyze_csv_enablements()