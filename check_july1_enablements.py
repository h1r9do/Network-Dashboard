#!/usr/bin/env python3
"""Check what actually got enabled on July 1"""

import pandas as pd

print("Checking July 1 Enablements")
print("=" * 80)

# Read June 30 and July 1 CSVs
df_30 = pd.read_csv('/var/www/html/circuitinfo/tracking_data_2025-06-30.csv', low_memory=False)
df_01 = pd.read_csv('/var/www/html/circuitinfo/tracking_data_2025-07-01.csv', low_memory=False)

print(f"June 30 CSV: {len(df_30)} rows")
print(f"July 01 CSV: {len(df_01)} rows")

# Get all enabled circuits for each day
enabled_30 = set()
enabled_01 = set()

for _, row in df_30.iterrows():
    site_id = str(row['Site ID']).strip()
    status = str(row['status']).lower().strip()
    if 'enabled' in status and 'ready' not in status:
        enabled_30.add(site_id)

for _, row in df_01.iterrows():
    site_id = str(row['Site ID']).strip()
    status = str(row['status']).lower().strip()
    if 'enabled' in status and 'ready' not in status:
        enabled_01.add(site_id)

print(f"\nJune 30: {len(enabled_30)} enabled circuits")
print(f"July 01: {len(enabled_01)} enabled circuits")

# Find new enablements
new_enablements = enabled_01 - enabled_30
print(f"\nNew enablements on July 1: {len(new_enablements)}")

if new_enablements:
    print("\nCircuits that became enabled on July 1:")
    # Get details for each new enablement
    for site_id in sorted(new_enablements):
        circuit = df_01[df_01['Site ID'] == site_id].iloc[0]
        print(f"  {circuit['Site Name']:15} | {site_id:15} | {circuit['status']}")
        
# Also check the two new "Ready for Enablement" circuits added on July 1
print("\n\nNew Ready for Enablement circuits on July 1:")
print("-" * 60)

# Get ready circuits for each day
ready_30 = df_30[df_30['status'].str.lower() == 'ready for enablement']['Site ID'].tolist()
ready_01 = df_01[df_01['status'].str.lower() == 'ready for enablement']['Site ID'].tolist()

new_ready = set(ready_01) - set(ready_30)
print(f"New circuits in Ready status: {len(new_ready)}")
for site_id in new_ready:
    circuit = df_01[df_01['Site ID'] == site_id].iloc[0]
    print(f"  {circuit['Site Name']:15} | {site_id:15}")