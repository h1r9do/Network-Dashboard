#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/local/bin/Main')
from config import config
from sqlalchemy import create_engine, text

engine = create_engine(config['production'].SQLALCHEMY_DATABASE_URI)

# Location types to find
location_types = [
    'Discount-Tire',
    'Regional-Office', 
    'Warehouse',
    'Call-Center',
    'Full-Service'
]

with engine.connect() as conn:
    print("Finding one network for each location type from meraki_live_data:\n")
    
    for location_type in location_types:
        # Find a network with this tag
        result = conn.execute(text("""
            SELECT DISTINCT network_name, network_id, device_tags
            FROM meraki_live_data
            WHERE network_id IS NOT NULL 
            AND network_id <> ''
            AND device_tags LIKE :tag_pattern
            AND device_tags NOT LIKE '%hub%'
            AND device_tags NOT LIKE '%voice%'  
            AND device_tags NOT LIKE '%lab%'
            LIMIT 1
        """), {'tag_pattern': f'%{location_type}%'})
        
        row = result.fetchone()
        if row:
            print(f"{location_type}:")
            print(f"  Network: {row.network_name}")
            print(f"  Network ID: {row.network_id}")
            print(f"  Tags: {row.device_tags}")
            print()
        else:
            print(f"{location_type}: No network found")
            print()
            
    # Also check for MDC and other variations
    print("\nChecking additional location types:")
    
    # Check all unique tags
    result = conn.execute(text("""
        SELECT DISTINCT device_tags
        FROM meraki_live_data
        WHERE device_tags IS NOT NULL
        AND device_tags NOT LIKE '%hub%'
        AND device_tags NOT LIKE '%voice%'
        AND device_tags NOT LIKE '%lab%'
        AND (
            device_tags LIKE '%MDC%' OR
            device_tags LIKE '%Service%' OR
            device_tags LIKE '%Office%' OR
            device_tags LIKE '%Center%'
        )
        LIMIT 20
    """))
    
    print("\nOther relevant tags found:")
    for row in result:
        print(f"  {row.device_tags}")