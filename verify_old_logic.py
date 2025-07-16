#!/usr/bin/env python3
"""
Verify what the old logic was actually counting
"""

import pandas as pd
import glob
from collections import defaultdict

def main():
    # Get all CSV files since 4/28
    csv_files = sorted(glob.glob('/var/www/html/circuitinfo/tracking_data_*.csv'))
    csv_files = [f for f in csv_files if '2025-04-28' <= f.split('tracking_data_')[1][:10] <= '2025-06-27']
    
    print(f'Analyzing {len(csv_files)} CSV files using OLD LOGIC\n')
    
    # Enabled status keywords from the backup
    enabled_statuses = [
        'enabled', 'service activated', 'enabled using existing broadband'
    ]
    
    daily_enablements = {}
    
    for i in range(1, len(csv_files)):
        prev_file = csv_files[i-1]
        curr_file = csv_files[i]
        
        prev_date = prev_file.split('tracking_data_')[1][:10]
        curr_date = curr_file.split('tracking_data_')[1][:10]
        
        df_prev = pd.read_csv(prev_file, low_memory=False)
        df_curr = pd.read_csv(curr_file, low_memory=False)
        
        # Create fingerprints like the old logic
        prev_circuits = {}
        curr_circuits = {}
        
        # Build previous circuits
        for _, row in df_prev.iterrows():
            site_name = str(row.get('Site Name', '')).strip()
            site_id = str(row.get('Site ID', '')).strip()
            purpose = str(row.get('Circuit Purpose', '')).strip()
            fingerprint = f"{site_name}|{site_id}|{purpose}"
            prev_circuits[fingerprint] = str(row.get('status', '')).lower().strip()
        
        # Check current circuits
        enablements_today = 0
        
        for _, row in df_curr.iterrows():
            site_name = str(row.get('Site Name', '')).strip()
            site_id = str(row.get('Site ID', '')).strip()
            purpose = str(row.get('Circuit Purpose', '')).strip()
            fingerprint = f"{site_name}|{site_id}|{purpose}"
            curr_status = str(row.get('status', '')).lower().strip()
            
            # Check if current status is enabled
            is_enabled = any(enabled_status in curr_status for enabled_status in enabled_statuses)
            
            if is_enabled:
                # Check previous status
                if fingerprint in prev_circuits:
                    prev_status = prev_circuits[fingerprint]
                    # Only count if it wasn't enabled before
                    was_enabled = any(enabled_status in prev_status for enabled_status in enabled_statuses)
                    if not was_enabled:
                        enablements_today += 1
                        if enablements_today <= 3:  # Show examples
                            print(f"  {site_name}: '{prev_status}' -> '{curr_status}'")
                else:
                    # New circuit that's enabled
                    enablements_today += 1
                    if enablements_today <= 3:
                        print(f"  NEW {site_name}: -> '{curr_status}'")
        
        daily_enablements[curr_date] = enablements_today
        print(f"{curr_date}: {enablements_today} enablements")
    
    total = sum(daily_enablements.values())
    avg = total / len(daily_enablements) if daily_enablements else 0
    
    print(f"\nSummary:")
    print(f"Total enablements: {total}")
    print(f"Days analyzed: {len(daily_enablements)}")
    print(f"Average per day: {avg:.1f}")

if __name__ == "__main__":
    main()