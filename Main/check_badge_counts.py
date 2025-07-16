#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/local/bin/Main')

from sqlalchemy import create_engine, text
import json

# Create database connection
engine = create_engine('postgresql://meraki:M3r@k1_2024!@localhost/meraki_database')

# Query to check wireless badges
query = text('''
    SELECT 
        wan1_provider,
        wan1_speed,
        wan2_provider,
        wan2_speed
    FROM enriched_circuits
''')

vzw_count = 0
att_count = 0
starlink_count = 0

with engine.connect() as conn:
    results = conn.execute(query).fetchall()
    
    for row in results:
        wan1_provider = (row[0] or '').upper()
        wan1_speed = (row[1] or '').upper()
        wan2_provider = (row[2] or '').upper()
        wan2_speed = (row[3] or '').upper()
        
        # Check WAN1
        if 'CELL' in wan1_speed:
            if 'VERIZON' in wan1_provider or 'VZW' in wan1_provider:
                vzw_count += 1
            elif 'AT&T' in wan1_provider or 'ATT' in wan1_provider:
                att_count += 1
        
        if 'SATELLITE' in wan1_speed or 'STARLINK' in wan1_provider:
            starlink_count += 1
            
        # Check WAN2
        if 'CELL' in wan2_speed:
            if 'VERIZON' in wan2_provider or 'VZW' in wan2_provider:
                vzw_count += 1
            elif 'AT&T' in wan2_provider or 'ATT' in wan2_provider:
                att_count += 1
                
        if 'SATELLITE' in wan2_speed or 'STARLINK' in wan2_provider:
            starlink_count += 1
    
    print(f'Total records: {len(results)}')
    print(f'VZW Count: {vzw_count}')
    print(f'AT&T Count: {att_count}')
    print(f'Starlink Count: {starlink_count}')
    
    # Show some examples
    print('\nStarlink examples:')
    for row in results[:10]:
        if row[1] and 'satellite' in row[1].lower():
            print(f'  WAN1: {row[0]} / {row[1]}')
        if row[3] and 'satellite' in row[3].lower():
            print(f'  WAN2: {row[2]} / {row[3]}')