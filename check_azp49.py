#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')
from config import Config
from sqlalchemy import create_engine, text
import json
import glob

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

with engine.connect() as conn:
    # Check AZP 49
    print('=== AZP 49 ===')
    
    # Check enriched circuits
    result = conn.execute(text('''
        SELECT wan1_provider, wan1_speed, wan2_provider, wan2_speed
        FROM enriched_circuits
        WHERE LOWER(network_name) = 'azp 49'
    '''))
    row = result.fetchone()
    if row:
        print(f'\nEnriched Circuits:')
        print(f'  WAN1: {row[0]} / {row[1]}')
        print(f'  WAN2: {row[2]} / {row[3]}')
    
    # Check meraki inventory
    result = conn.execute(text('''
        SELECT device_notes, wan1_provider_label, wan2_provider_label
        FROM meraki_inventory
        WHERE LOWER(network_name) = 'azp 49'
    '''))
    row = result.fetchone()
    if row:
        print(f'\nMeraki Inventory:')
        print(f'  Device Notes: {repr(row[0])}')
        print(f'  WAN1 Label: {row[1]}')
        print(f'  WAN2 Label: {row[2]}')
    
    # Check DSR circuits
    result = conn.execute(text('''
        SELECT circuit_purpose, provider_name, billing_monthly_cost, status
        FROM circuits
        WHERE LOWER(site_name) = 'azp 49'
        ORDER BY circuit_purpose
    '''))
    print(f'\nDSR Circuits:')
    for row in result:
        print(f'  {row[0]}: {row[1]} - ${row[2] if row[2] else "0.00"} ({row[3]})')

# Check master list
master_files = glob.glob('/var/www/html/circuitinfo/master_circuit_data_*.json')
if master_files:
    latest_master = max(master_files, key=lambda x: x)
    with open(latest_master, 'r') as f:
        master_data = json.load(f)
    
    print(f'\nMaster Circuit List:')
    for item in master_data:
        if item.get('Store', '').upper() == 'AZP 49':
            if item.get('Active A Circuit Carrier'):
                print(f'  Carrier A: {item["Active A Circuit Carrier"]} - ${item.get("MRC", "")}')
            if item.get('Active B Circuit Carrier'):
                print(f'  Carrier B: {item["Active B Circuit Carrier"]} - ${item.get("MRC3", "")}')
            break

# Check May live data
may_file = '/var/www/html/meraki-data/mx_inventory_live_20250502_033555.json'
try:
    with open(may_file, 'r') as f:
        may_data = json.load(f)
    
    print(f'\nMay 2nd Live Data:')
    for item in may_data:
        if isinstance(item, dict) and item.get('network_name') == 'AZP 49':
            print(f'  raw_notes: {repr(item.get("raw_notes", ""))}')
            break
except:
    print('\nCould not read May 2nd data')