#!/usr/bin/env python3
"""
Check FLT 02 and GAA 01 data
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
        host=host.split(':')[0],
        port=5432,
        database=database,
        user=user,
        password=password
    )
    cursor = conn.cursor()
    
    # Check enriched_circuits data
    print("Checking enriched_circuits for FLT 02 and GAA 01...\n")
    
    cursor.execute("""
        SELECT network_name, wan1_speed, wan2_speed, wan1_provider, wan2_provider,
               wan1_ip, wan2_ip, device_tags, last_updated 
        FROM enriched_circuits 
        WHERE network_name IN ('FLT 02', 'GAA 01')
        ORDER BY network_name
    """)
    
    results = cursor.fetchall()
    
    for row in results:
        print(f"Site: {row[0]}")
        print(f"  WAN1 Speed: '{row[1]}'")
        print(f"  WAN1 Provider: '{row[3]}'")
        print(f"  WAN1 IP: {row[5]}")
        print(f"  WAN2 Speed: '{row[2]}'")
        print(f"  WAN2 Provider: '{row[4]}'")
        print(f"  WAN2 IP: {row[6]}")
        print(f"  Device Tags: {row[7]}")
        print(f"  Last Updated: {row[8]}")
        print("\n" + "-"*60 + "\n")
    
    # Check Meraki inventory with notes
    print("Checking Meraki inventory for device notes...\n")
    
    cursor.execute("""
        SELECT network_name, device_name, notes, model, tags
        FROM meraki_inventory
        WHERE network_name IN ('FLT 02', 'GAA 01')
        AND notes IS NOT NULL AND notes != ''
        ORDER BY network_name, device_name
    """)
    
    results = cursor.fetchall()
    
    for row in results:
        print(f"Network: {row[0]}")
        print(f"Device: {row[1]} ({row[3]})")
        print(f"Tags: {row[4]}")
        print(f"Notes (raw): {repr(row[2])}")
        
        # Parse the notes to see what patterns we have
        if row[2]:
            # Look for speed patterns
            speed_patterns = re.findall(r'(\d+\.?\d*\s*[MG](?:\s*x\s*\d+\.?\d*\s*[MG])?)', row[2], re.IGNORECASE)
            if speed_patterns:
                print(f"Speed patterns found: {speed_patterns}")
        print()
    
    # Check circuits table to see the source data
    print("\n" + "="*60)
    print("Checking circuits table (source data)...\n")
    
    cursor.execute("""
        SELECT store_id, wan1_speed, wan2_speed, wan1_provider, wan2_provider
        FROM circuits
        WHERE store_id IN ('FLT 02', 'GAA 01')
        ORDER BY store_id
    """)
    
    results = cursor.fetchall()
    
    for row in results:
        print(f"Store ID: {row[0]}")
        print(f"  WAN1 Speed (from CSV): '{row[1]}'")
        print(f"  WAN1 Provider (from CSV): '{row[2]}'")
        print(f"  WAN2 Speed (from CSV): '{row[3]}'")
        print(f"  WAN2 Provider (from CSV): '{row[4]}'")
        print()
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()