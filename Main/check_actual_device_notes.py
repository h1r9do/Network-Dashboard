#!/usr/bin/env python3
"""
Check actual device notes for problem sites
"""
import psycopg2
import re

# Read config
with open('/usr/local/bin/Main/config.py', 'r') as f:
    config_content = f.read()
    
uri_match = re.search(r"SQLALCHEMY_DATABASE_URI = ['\"]postgresql://([^:]+):([^@]+)@([^/]+)/([^'\"]+)['\"]", config_content)
if uri_match:
    user, password, host, database = uri_match.groups()

try:
    conn = psycopg2.connect(
        host=host.split(':')[0],
        port=5432,
        database=database,
        user=user,
        password=password
    )
    cursor = conn.cursor()
    
    # Check specific problem sites
    problem_sites = ['COD 28', 'CAN 30', 'COD 36', 'FLT 02', 'GAA 01']
    
    for site in problem_sites:
        print(f"\nChecking {site}:")
        print("="*60)
        
        # Get device notes from meraki_inventory
        cursor.execute("""
            SELECT device_notes
            FROM meraki_inventory
            WHERE network_name = %s
        """, (site,))
        
        row = cursor.fetchone()
        if row and row[0]:
            notes = row[0]
            print(f"Device notes (length={len(notes)}):")
            print(f"Raw: {repr(notes)}")
            print(f"\nLines:")
            for i, line in enumerate(notes.split('\n')):
                print(f"  {i}: '{line}'")
                
            # Check for any odd characters
            if '\r' in notes:
                print("  WARNING: Contains \\r characters!")
            if '  ' in notes:
                print("  WARNING: Contains double spaces!")
            if notes != notes.strip():
                print("  WARNING: Has leading/trailing whitespace!")
                
            # Test parsing with the actual notes
            from test_actual_parsing import parse_raw_notes
            w1p, w1s, w2p, w2s = parse_raw_notes(notes)
            print(f"\nParsing result:")
            print(f"  WAN1: '{w1p}' / '{w1s}'")
            print(f"  WAN2: '{w2p}' / '{w2s}'")
        else:
            print("  No device notes found!")
    
    # Now check what the enriched_circuits table has for device_notes
    print("\n" + "="*80)
    print("\nChecking if enriched_circuits stores device_notes...")
    
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'enriched_circuits'
        AND column_name LIKE '%note%'
    """)
    
    note_columns = cursor.fetchall()
    if note_columns:
        print(f"Found note columns: {[col[0] for col in note_columns]}")
    else:
        print("No device_notes column in enriched_circuits!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()