#!/usr/bin/env python3
"""
Check Meraki inventory notes for FLT 02 and GAA 01
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
    
    # First check column names in meraki_inventory
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'meraki_inventory'
        AND column_name LIKE '%note%'
        ORDER BY ordinal_position
    """)
    
    print("Note-related columns in meraki_inventory:")
    note_columns = cursor.fetchall()
    for col in note_columns:
        print(f"  - {col[0]}")
    
    # Try device_notes column
    cursor.execute("""
        SELECT network_name, device_name, device_notes, model
        FROM meraki_inventory
        WHERE network_name IN ('FLT 02', 'GAA 01')
        AND device_notes IS NOT NULL AND device_notes != ''
        ORDER BY network_name, device_name
    """)
    
    results = cursor.fetchall()
    
    print(f"\nFound {len(results)} devices with notes for FLT 02 and GAA 01:\n")
    
    for row in results:
        print(f"Network: {row[0]}")
        print(f"Device: {row[1]} (Model: {row[3]})")
        print(f"Device Notes (full): {repr(row[2])}")
        
        # Parse the notes to see what patterns we have
        if row[2]:
            # Look for all speed-like patterns
            all_patterns = re.findall(r'(\d+(?:\.\d+)?\s*[MG](?:\s*x\s*\d+(?:\.\d+)?\s*[MG])?)', row[2], re.IGNORECASE)
            if all_patterns:
                print(f"All speed patterns found: {all_patterns}")
                
            # Look for patterns with " M" (space before M)
            space_patterns = re.findall(r'(\d+(?:\.\d+)?\s+M)', row[2])
            if space_patterns:
                print(f"Patterns with space before M: {space_patterns}")
        print("\n" + "-"*60 + "\n")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()