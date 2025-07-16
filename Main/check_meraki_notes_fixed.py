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
    
    # Check all columns in meraki_inventory
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'meraki_inventory'
        ORDER BY ordinal_position
        LIMIT 20
    """)
    
    print("Columns in meraki_inventory:")
    for col in cursor.fetchall():
        print(f"  - {col[0]}")
    
    print("\n" + "="*60 + "\n")
    
    # Check device notes
    cursor.execute("""
        SELECT network_name, device_name, device_notes
        FROM meraki_inventory
        WHERE network_name IN ('FLT 02', 'GAA 01')
        AND device_notes IS NOT NULL AND device_notes != ''
        ORDER BY network_name, device_name
    """)
    
    results = cursor.fetchall()
    
    print(f"Found {len(results)} devices with notes for FLT 02 and GAA 01:\n")
    
    for row in results:
        print(f"Network: {row[0]}")
        print(f"Device: {row[1]}")
        print(f"Device Notes (raw): {repr(row[2])}")
        
        # Parse the notes to see what patterns we have
        if row[2]:
            # Look for all speed-like patterns
            all_patterns = re.findall(r'(\d+(?:\.\d+)?\s*[MG](?:\s*x\s*\d+(?:\.\d+)?\s*[MG])?)', row[2], re.IGNORECASE)
            if all_patterns:
                print(f"All speed patterns found: {all_patterns}")
                
            # Look specifically for patterns that might be causing the issue
            # Pattern with space before M
            space_m_patterns = re.findall(r'(\d+(?:\.\d+)?\s+M)(?![xX])', row[2])
            if space_m_patterns:
                print(f"***ISSUE: Patterns with space before M (no x following): {space_m_patterns}")
                
            # Check if there's a proper x pattern
            x_patterns = re.findall(r'(\d+(?:\.\d+)?\s*M\s*x\s*\d+(?:\.\d+)?\s*M)', row[2], re.IGNORECASE)
            if x_patterns:
                print(f"Proper x patterns: {x_patterns}")
        print("\n" + "-"*60 + "\n")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()