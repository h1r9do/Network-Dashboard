#!/usr/bin/env python3
"""
Check parsing error for FLT 02 and GAA 01 - simplified version
"""
import psycopg2
import re

# Read config to get database connection
with open('/usr/local/bin/Main/config.py', 'r') as f:
    config_content = f.read()
    
# Extract database URI
uri_match = re.search(r"SQLALCHEMY_DATABASE_URI = ['\"]postgresql://([^:]+):([^@]+)@([^/]+)/([^'\"]+)['\"]", config_content)
if uri_match:
    user, password, host, database = uri_match.groups()
else:
    print("Could not find database URI in config")
    exit(1)

# Connect to database
try:
    conn = psycopg2.connect(
        host=host.split(':')[0],  # Remove port if present
        port=5432,
        database=database,
        user=user,
        password=password
    )
    cursor = conn.cursor()
    
    # First check what columns we have
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'enriched_circuits'
        ORDER BY ordinal_position
    """)
    
    print("Available columns in enriched_circuits:")
    for col in cursor.fetchall():
        print(f"  - {col[0]}")
    
    print("\n" + "="*60 + "\n")
    
    # Now check the data for FLT 02 and GAA 01
    cursor.execute("""
        SELECT network_name, wan1_speed, wan2_speed, wan1_provider, wan2_provider, 
               wan1_notes, wan2_notes, last_updated 
        FROM enriched_circuits 
        WHERE network_name IN ('FLT 02', 'GAA 01')
        ORDER BY network_name
    """)
    
    results = cursor.fetchall()
    
    if not results:
        print("No data found for FLT 02 or GAA 01")
    else:
        for row in results:
            print(f"Site: {row[0]}")
            print(f"  WAN1 Speed: '{row[1]}'")
            print(f"  WAN1 Provider: '{row[3]}'") 
            print(f"  WAN1 Notes: '{row[5] if row[5] else 'None'}'")
            print(f"  WAN2 Speed: '{row[2]}'")
            print(f"  WAN2 Provider: '{row[4]}'")
            print(f"  WAN2 Notes: '{row[6] if row[6] else 'None'}'")
            print(f"  Last Updated: {row[7]}")
            print("\n" + "-"*60 + "\n")
    
    # Check Meraki inventory
    print("Checking Meraki inventory for these sites...\n")
    
    cursor.execute("""
        SELECT network_name, device_name, notes, model
        FROM meraki_inventory
        WHERE network_name IN ('FLT 02', 'GAA 01')
        ORDER BY network_name, device_name
    """)
    
    results = cursor.fetchall()
    
    for row in results:
        print(f"Network: {row[0]}, Device: {row[1]}, Model: {row[3]}")
        if row[2]:
            print(f"  Notes: {repr(row[2])}")
        print()
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()