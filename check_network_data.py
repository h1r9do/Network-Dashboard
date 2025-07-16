#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/local/bin/Main')
from config import config
from sqlalchemy import create_engine, text

engine = create_engine(config['production'].SQLALCHEMY_DATABASE_URI)

with engine.connect() as conn:
    # Check device_inventory
    print('Sample device_inventory data:')
    result = conn.execute(text("""
        SELECT organization_name, device_serial, model, network_id
        FROM device_inventory
        WHERE network_id IS NOT NULL AND network_id <> ''
        LIMIT 5
    """))
    
    count = 0
    for row in result:
        count += 1
        print(f'  Org: {row.organization_name}')
        print(f'  Serial: {row.device_serial}')
        print(f'  Model: {row.model}')
        print(f'  Network ID: {row.network_id}')
        print()
    
    if count == 0:
        print('  No records found with network IDs')
        
    # Check enriched_networks
    print('\n\nChecking enriched_networks table schema:')
    result2 = conn.execute(text("""
        SELECT column_name, data_type
        FROM information_schema.columns 
        WHERE table_name = 'enriched_networks'
        ORDER BY ordinal_position
    """))
    
    for row in result2:
        print(f'  - {row.column_name}: {row.data_type}')
        
    # Check if we have network data anywhere
    print('\n\nChecking for network data in enriched_networks:')
    result3 = conn.execute(text("""
        SELECT *
        FROM enriched_networks
        LIMIT 2
    """))
    
    for row in result3:
        print(f'  Network: {row}')
        
    # Check meraki_live_data which might have the network IDs
    print('\n\nChecking meraki_live_data table:')
    result4 = conn.execute(text("""
        SELECT network_name, network_id, organization_id
        FROM meraki_live_data
        WHERE network_id IS NOT NULL AND network_id <> ''
        LIMIT 5
    """))
    
    count = 0
    for row in result4:
        count += 1
        print(f'  Network: {row.network_name}')
        print(f'  Network ID: {row.network_id}')
        print(f'  Org ID: {row.organization_id}')
        print()
        
    if count > 0:
        print(f'\nFound {count} networks with IDs in meraki_live_data table!')
    else:
        print('\nNo network IDs found in meraki_live_data either')