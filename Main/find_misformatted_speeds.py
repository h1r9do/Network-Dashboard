#!/usr/bin/env python3
"""
Find all sites with misformatted speeds in enriched_circuits
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
    
    print("Finding all sites with misformatted speeds...\n")
    
    # Query for various misformatted speed patterns
    cursor.execute("""
        SELECT network_name, wan1_speed, wan1_provider, wan2_speed, wan2_provider, last_updated
        FROM enriched_circuits
        WHERE 
            -- Single speed with space before unit (e.g., "300.0 M")
            (wan1_speed ~ '^\d+\.?\d*\s+[MG]$' OR wan2_speed ~ '^\d+\.?\d*\s+[MG]$')
            -- Missing unit in x format (e.g., "300 x 30")
            OR (wan1_speed ~ '^\d+\.?\d*\s*x\s*\d+\.?\d*$' OR wan2_speed ~ '^\d+\.?\d*\s*x\s*\d+\.?\d*$')
            -- Space before x (e.g., "300.0M x30.0M")
            OR (wan1_speed ~ '^\d+\.?\d*[MG]\s*x\d+\.?\d*[MG]$' OR wan2_speed ~ '^\d+\.?\d*[MG]\s*x\d+\.?\d*[MG]$')
            -- Other single speeds without x format
            OR (wan1_speed ~ '^\d+\.?\d*[MG]$' AND wan1_speed NOT IN ('Cell', 'Satellite'))
            OR (wan2_speed ~ '^\d+\.?\d*[MG]$' AND wan2_speed NOT IN ('Cell', 'Satellite'))
        ORDER BY last_updated DESC, network_name
    """)
    
    results = cursor.fetchall()
    
    print(f"Found {len(results)} sites with misformatted speeds:\n")
    
    # Group by issue type
    space_before_unit = []
    missing_units = []
    single_speed = []
    other_issues = []
    
    for row in results:
        network, wan1_speed, wan1_prov, wan2_speed, wan2_prov, updated = row
        issues = []
        
        # Check WAN1
        if wan1_speed:
            if re.match(r'^\d+\.?\d*\s+[MG]$', wan1_speed):
                issues.append(f"WAN1 has space before unit: '{wan1_speed}'")
                space_before_unit.append(row)
            elif re.match(r'^\d+\.?\d*\s*x\s*\d+\.?\d*$', wan1_speed):
                issues.append(f"WAN1 missing units: '{wan1_speed}'")
                missing_units.append(row)
            elif re.match(r'^\d+\.?\d*[MG]$', wan1_speed) and wan1_speed not in ('Cell', 'Satellite'):
                issues.append(f"WAN1 single speed (no x format): '{wan1_speed}'")
                single_speed.append(row)
        
        # Check WAN2
        if wan2_speed:
            if re.match(r'^\d+\.?\d*\s+[MG]$', wan2_speed):
                issues.append(f"WAN2 has space before unit: '{wan2_speed}'")
                if row not in space_before_unit:
                    space_before_unit.append(row)
            elif re.match(r'^\d+\.?\d*\s*x\s*\d+\.?\d*$', wan2_speed):
                issues.append(f"WAN2 missing units: '{wan2_speed}'")
                if row not in missing_units:
                    missing_units.append(row)
            elif re.match(r'^\d+\.?\d*[MG]$', wan2_speed) and wan2_speed not in ('Cell', 'Satellite'):
                issues.append(f"WAN2 single speed (no x format): '{wan2_speed}'")
                if row not in single_speed:
                    single_speed.append(row)
        
        if not issues:
            other_issues.append(row)
    
    # Display results by category
    if space_before_unit:
        print(f"\n=== SPACE BEFORE UNIT ({len(space_before_unit)} sites) ===")
        print("(e.g., '300.0 M' instead of '300.0M')")
        for row in space_before_unit[:10]:  # Show first 10
            print(f"{row[0]:15} WAN1: '{row[1]:20}' WAN2: '{row[3]:20}' Updated: {row[5]}")
        if len(space_before_unit) > 10:
            print(f"... and {len(space_before_unit) - 10} more")
    
    if missing_units:
        print(f"\n=== MISSING UNITS ({len(missing_units)} sites) ===")
        print("(e.g., '300 x 30' instead of '300.0M x 30.0M')")
        for row in missing_units[:10]:
            print(f"{row[0]:15} WAN1: '{row[1]:20}' WAN2: '{row[3]:20}' Updated: {row[5]}")
        if len(missing_units) > 10:
            print(f"... and {len(missing_units) - 10} more")
    
    if single_speed:
        print(f"\n=== SINGLE SPEED FORMAT ({len(single_speed)} sites) ===")
        print("(e.g., '100M' instead of '100.0M x 10.0M')")
        for row in single_speed[:10]:
            print(f"{row[0]:15} WAN1: '{row[1]:20}' WAN2: '{row[3]:20}' Updated: {row[5]}")
        if len(single_speed) > 10:
            print(f"... and {len(single_speed) - 10} more")
    
    # Check specific examples
    print("\n" + "="*60)
    print("\nDetailed check for FLT 02 and GAA 01:")
    
    cursor.execute("""
        SELECT network_name, wan1_speed, wan1_provider, wan2_speed, wan2_provider, 
               wan1_confirmed, wan2_confirmed, last_updated
        FROM enriched_circuits
        WHERE network_name IN ('FLT 02', 'GAA 01')
        ORDER BY network_name
    """)
    
    for row in cursor.fetchall():
        print(f"\n{row[0]}:")
        print(f"  WAN1: '{row[1]}' / {row[2]} (confirmed: {row[5]})")
        print(f"  WAN2: '{row[3]}' / {row[4]} (confirmed: {row[6]})")
        print(f"  Last updated: {row[7]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()