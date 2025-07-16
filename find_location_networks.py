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
    print("Finding one network for each location type:\n")
    
    for location_type in location_types:
        # Find a network with this tag
        result = conn.execute(text("""
            SELECT DISTINCT mi.network_id, mi.network_name, mi.organization_name, mi.device_tags
            FROM meraki_inventory mi
            WHERE :tag = ANY(mi.device_tags)
            AND NOT ('hub' = ANY(mi.device_tags))
            AND NOT ('voice' = ANY(mi.device_tags))  
            AND NOT ('lab' = ANY(mi.device_tags))
            LIMIT 1
        """), {'tag': location_type})
        
        row = result.fetchone()
        if row:
            print(f"{location_type}:")
            print(f"  Network: {row.network_name}")
            print(f"  Network ID: {row.network_id}")
            print(f"  Org: {row.organization_name}")
            print(f"  Tags: {row.device_tags}")
            print()
        else:
            print(f"{location_type}: No network found")
            print()