#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/local/bin/Main')
from config import config
from sqlalchemy import create_engine, text

engine = create_engine(config['production'].SQLALCHEMY_DATABASE_URI)

with engine.connect() as conn:
    # Find sites with specific tags
    result = conn.execute(text("""
        SELECT DISTINCT organization_name, network_name, device_tags
        FROM meraki_inventory
        WHERE device_tags IS NOT NULL 
        AND device_tags <> ''
        AND device_tags <> '[]'
        AND (
            device_tags LIKE '%Discount Tire%' OR
            device_tags LIKE '%Full Service%' OR
            device_tags LIKE '%Warehouse%' OR
            device_tags LIKE '%Regional Office%' OR
            device_tags LIKE '%MDC%'
        )
        LIMIT 20
    """))
    
    print('Sites with location type tags:')
    for row in result:
        print(f'Org: {row.organization_name}, Network: {row.network_name}, Tags: {row.device_tags}')
    
    # Also check what tags exist
    print('\n\nAll unique tags found:')
    tag_result = conn.execute(text("""
        SELECT DISTINCT device_tags
        FROM meraki_inventory
        WHERE device_tags IS NOT NULL 
        AND device_tags <> ''
        AND device_tags <> '[]'
        AND device_tags NOT LIKE '%voice%'
        AND device_tags NOT LIKE '%lab%'
        AND device_tags NOT LIKE '%hub%'
        LIMIT 50
    """))
    
    unique_tags = set()
    for row in tag_result:
        if row.device_tags and row.device_tags != '[]':
            # Parse tags if they're in JSON format
            try:
                import json
                tag_list = json.loads(row.device_tags)
                for tag in tag_list:
                    unique_tags.add(tag)
            except:
                unique_tags.add(row.device_tags)
    
    for tag in sorted(unique_tags):
        print(f'  - {tag}')