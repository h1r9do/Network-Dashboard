#!/usr/bin/env python3
import pandas as pd
import glob
from datetime import datetime, timedelta

# Get CSV files for the past week
csv_files = sorted(glob.glob('/var/www/html/circuitinfo/tracking_data_*.csv'))
today = datetime.now()
week_ago = today - timedelta(days=7)

print("Ready for Enablement Counts - Past Week")
print("=" * 80)

for csv_file in csv_files[-7:]:
    # Extract date from filename
    date_str = csv_file.split('tracking_data_')[-1].replace('.csv', '')
    
    try:
        df = pd.read_csv(csv_file, low_memory=False)
        
        # Count Ready for Enablement circuits
        ready_circuits = df[df['status'].str.lower() == 'ready for enablement']
        count = len(ready_circuits)
        
        print(f"\n{date_str}: {count} circuits")
        
        if count > 0:
            print("Circuits:")
            for _, row in ready_circuits.iterrows():
                print(f"  {row['Site Name']:15} | {row['Site ID']:15} | {row['Circuit Purpose']:10} | {row.get('assigned_to', 'N/A')}")
    
    except Exception as e:
        print(f"\n{date_str}: ERROR - {e}")

print("\n" + "=" * 80)