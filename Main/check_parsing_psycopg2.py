#!/usr/bin/env python3
"""
Check parsing error for FLT 02 and GAA 01 using psycopg2
"""
import psycopg2
import re

# Read config to get database connection
with open('/usr/local/bin/Main/config.py', 'r') as f:
    config_content = f.read()
    
# Extract database URI - look for the pattern
import re
uri_match = re.search(r"SQLALCHEMY_DATABASE_URI = ['\"]postgresql://([^:]+):([^@]+)@([^/]+)/([^'\"]+)['\"]", config_content)
if uri_match:
    user, password, host, database = uri_match.groups()
    print(f"Found database connection: {user}@{host}/{database}")
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
    
    print("\nChecking sites FLT 02 and GAA 01...\n")
    
    cursor.execute("""
        SELECT network_name, wan1_speed, wan2_speed, wan1_provider, wan2_provider, 
               device_notes, last_updated 
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
            print(f"  WAN2 Speed: '{row[2]}'")
            print(f"  WAN2 Provider: '{row[4]}'")
            print(f"  Last Updated: {row[6]}")
            
            # Show device notes
            if row[5]:
                print(f"\n  Device Notes (first 500 chars):")
                print(f"  {repr(row[5][:500])}")
                
                # Look for speed patterns
                speed_patterns = re.findall(r'(\d+\.?\d*\s*[MG])', row[5], re.IGNORECASE)
                if speed_patterns:
                    print(f"\n  Speed patterns found in notes: {speed_patterns}")
                
                # Look for x patterns (e.g., "300.0M x 35.0M")
                x_patterns = re.findall(r'(\d+\.?\d*\s*[MG]\s*x\s*\d+\.?\d*\s*[MG])', row[5], re.IGNORECASE)
                if x_patterns:
                    print(f"  'x' patterns found in notes: {x_patterns}")
            
            print("\n" + "-"*60 + "\n")
    
    # Also check what the raw Meraki inventory has
    print("\nChecking Meraki inventory for these sites...\n")
    
    cursor.execute("""
        SELECT network_name, device_name, device_notes, model
        FROM meraki_inventory
        WHERE network_name IN ('FLT 02', 'GAA 01')
        ORDER BY network_name, device_name
    """)
    
    results = cursor.fetchall()
    
    for row in results:
        print(f"Network: {row[0]}, Device: {row[1]}, Model: {row[3]}")
        if row[2]:
            print(f"  Notes (first 300 chars): {repr(row[2][:300])}")
        print()
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()