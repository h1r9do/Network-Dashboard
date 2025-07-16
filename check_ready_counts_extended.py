#!/usr/bin/env python3
import pandas as pd
import glob
from datetime import datetime

# Get all CSV files starting from June 22
csv_files = sorted(glob.glob('/var/www/html/circuitinfo/tracking_data_*.csv'))

print("Ready for Enablement Counts - June 22 to Present")
print("=" * 80)

# Filter for dates from June 22 onwards
start_date = datetime(2025, 6, 22)

for csv_file in csv_files:
    # Extract date from filename
    date_str = csv_file.split('tracking_data_')[-1].replace('.csv', '')
    
    try:
        file_date = datetime.strptime(date_str, '%Y-%m-%d')
        if file_date < start_date:
            continue
            
        df = pd.read_csv(csv_file, low_memory=False)
        
        # Count Ready for Enablement circuits
        ready_circuits = df[df['status'].str.lower() == 'ready for enablement']
        count = len(ready_circuits)
        
        print(f"\n{date_str}: {count} circuits")
        
        if count > 0 and count <= 15:  # Show details for smaller counts
            print("Circuits:")
            for _, row in ready_circuits.iterrows():
                site_name = row['Site Name'] if pd.notna(row['Site Name']) else 'N/A'
                site_id = row['Site ID'] if pd.notna(row['Site ID']) else 'N/A'
                purpose = row['Circuit Purpose'] if pd.notna(row['Circuit Purpose']) else 'N/A'
                print(f"  {site_name:15} | {site_id:15} | {purpose:10}")
    
    except Exception as e:
        print(f"\n{date_str}: ERROR - {e}")

print("\n" + "=" * 80)