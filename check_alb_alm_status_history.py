#!/usr/bin/env python3
"""Check the status history of ALB and ALM circuits"""

import pandas as pd

print("Checking ALB and ALM circuit status history")
print("=" * 80)

# Check July 1 and July 2 CSVs
csv_files = {
    '2025-06-30': '/var/www/html/circuitinfo/tracking_data_2025-06-30.csv',
    '2025-07-01': '/var/www/html/circuitinfo/tracking_data_2025-07-01.csv',
    '2025-07-02': '/var/www/html/circuitinfo/tracking_data_2025-07-02.csv'
}

# Read CSVs and filter for ALB/ALM sites
for date, file in csv_files.items():
    print(f"\n{date} Status:")
    print("-" * 60)
    
    try:
        df = pd.read_csv(file, low_memory=False)
        
        # Filter for ALB and ALM sites
        alb_alm = df[df['Site Name'].str.startswith(('ALB', 'ALM'), na=False)]
        
        if len(alb_alm) > 0:
            # Sort by Site Name for easier comparison
            alb_alm = alb_alm.sort_values('Site Name')
            
            print(f"{'Site Name':10} | {'Site ID':15} | {'Status':30} | {'Circuit Purpose':15}")
            print("-" * 80)
            
            for _, row in alb_alm.iterrows():
                site_name = str(row['Site Name'])[:10]
                site_id = str(row['Site ID'])[:15]
                status = str(row['status'])[:30]
                purpose = str(row.get('Circuit Purpose', 'N/A'))[:15]
                print(f"{site_name:10} | {site_id:15} | {status:30} | {purpose:15}")
        else:
            print("No ALB/ALM sites found")
            
    except Exception as e:
        print(f"Error reading {date}: {e}")

# Now let's check specific transitions
print("\n\nStatus Transitions:")
print("=" * 80)

try:
    # Read all three days
    df_30 = pd.read_csv(csv_files['2025-06-30'], low_memory=False)
    df_01 = pd.read_csv(csv_files['2025-07-01'], low_memory=False)
    df_02 = pd.read_csv(csv_files['2025-07-02'], low_memory=False)
    
    # Get ALB/ALM sites from July 2 that are enabled
    alb_alm_enabled = df_02[(df_02['Site Name'].str.startswith(('ALB', 'ALM'), na=False)) & 
                            (df_02['status'].str.lower() == 'enabled')]
    
    print(f"\nALB/ALM sites that became Enabled on July 2: {len(alb_alm_enabled)}")
    
    for _, row in alb_alm_enabled.iterrows():
        site_id = row['Site ID']
        site_name = row['Site Name']
        
        # Find same site in previous days
        prev_01 = df_01[df_01['Site ID'] == site_id]
        prev_30 = df_30[df_30['Site ID'] == site_id]
        
        print(f"\n{site_name} ({site_id}):")
        
        if len(prev_30) > 0:
            print(f"  June 30: {prev_30.iloc[0]['status']}")
        else:
            print(f"  June 30: Not found")
            
        if len(prev_01) > 0:
            print(f"  July 01: {prev_01.iloc[0]['status']}")
        else:
            print(f"  July 01: Not found")
            
        print(f"  July 02: {row['status']}")
        
except Exception as e:
    print(f"Error analyzing transitions: {e}")