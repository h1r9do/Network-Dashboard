#!/usr/bin/env python3
import psycopg2
import psycopg2.extras
import json
from config import Config
import re

# Parse database connection
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
if match:
    user, password, host, port, database = match.groups()
    
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )
    
    cursor = conn.cursor()
    
    # First check the column type
    cursor.execute("""
        SELECT column_name, data_type, udt_name
        FROM information_schema.columns
        WHERE table_name = 'meraki_inventory' 
        AND column_name = 'device_tags'
    """)
    
    col_info = cursor.fetchone()
    print(f"Column info: {col_info}")
    
    # Check sample device_tags
    cursor.execute("""
        SELECT network_name, device_tags 
        FROM meraki_inventory 
        WHERE device_tags IS NOT NULL 
        AND array_length(device_tags, 1) > 0
        LIMIT 10
    """)
    
    print("Sample device_tags from meraki_inventory:")
    for row in cursor.fetchall():
        network_name, tags = row
        print(f"\nNetwork: {network_name}")
        print(f"Raw tags: {tags}")
        print(f"Type: {type(tags)}")
        
        # Try to parse as JSON
        try:
            parsed = json.loads(tags)
            print(f"Parsed tags: {parsed}")
        except:
            print("Failed to parse as JSON")
    
    # Check for Discount-Tire variations
    print("\n\nChecking for Discount-Tire variations:")
    variations = ['Discount-Tire', 'discount-tire', 'Discount Tire', 'DiscountTire']
    
    for var in variations:
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM meraki_inventory 
            WHERE device_tags LIKE %s
        """, (f'%{var}%',))
        
        count = cursor.fetchone()[0]
        print(f"  '{var}': {count} devices")
    
    conn.close()