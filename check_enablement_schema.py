#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from config import Config
import psycopg2
import re

match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
user, password, host, port, database = match.groups()

conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
cursor = conn.cursor()

# Check schema for enablement tables
cursor.execute("""
    SELECT table_name, column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name IN ('daily_enablements', 'ready_queue_daily', 'enablement_summary')
    ORDER BY table_name, ordinal_position
""")

print('Database Schema for Enablement Tracking:')
print('=' * 80)
current_table = None
for row in cursor.fetchall():
    if row[0] != current_table:
        print(f'\n{row[0]}:')
        current_table = row[0]
    print(f'  - {row[1]:25} {row[2]}')

# Now check the latest CSV for ready for enablement status
print('\n\nChecking latest CSV for Ready for Enablement circuits:')
print('=' * 80)

import pandas as pd
import glob

csv_files = sorted(glob.glob('/var/www/html/circuitinfo/tracking_data_*.csv'))
if csv_files:
    latest_csv = csv_files[-1]
    print(f'Reading: {latest_csv}')
    
    df = pd.read_csv(latest_csv, low_memory=False)
    
    # Find all Ready for Enablement circuits
    ready_circuits = df[df['status'].str.lower() == 'ready for enablement']
    
    print(f'\nTotal circuits in Ready for Enablement status: {len(ready_circuits)}')
    print('\nCircuits:')
    for _, row in ready_circuits.iterrows():
        print(f"  {row['Site Name']:20} | {row['Site ID']:15} | {row['Circuit Purpose']:10} | {row['status']}")

cursor.close()
conn.close()