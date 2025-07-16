#!/usr/bin/env python3
"""
Final trace to find where "20.0 M" is coming from
"""
import psycopg2
import re

# Read config
with open('/usr/local/bin/Main/config.py', 'r') as f:
    config_content = f.read()
    
uri_match = re.search(r"SQLALCHEMY_DATABASE_URI = ['\"]postgresql://([^:]+):([^@]+)@([^/]+)/([^'\"]+)['\"]", config_content)
if uri_match:
    user, password, host, database = uri_match.groups()

def reformat_speed(speed_str, provider):
    """Reformat speed string - from nightly_enriched_db.py"""
    if not speed_str or str(speed_str).lower() == 'nan':
        return ""
    
    # Special cases for cellular/satellite
    provider_lower = str(provider).lower()
    if provider_lower == 'cell' or any(term in provider_lower for term in ['vzw cell', 'verizon cell', 'digi', 'inseego']):
        return "Cell"
    if 'starlink' in provider_lower:
        return "Satellite"
    
    return str(speed_str).strip()

try:
    conn = psycopg2.connect(
        host=host.split(':')[0],
        port=5432,
        database=database,
        user=user,
        password=password
    )
    cursor = conn.cursor()
    
    # Check COD 28 specifically
    site = 'COD 28'
    
    print(f"Tracing speed issue for {site}...")
    print("="*60)
    
    # 1. Check what DSR circuits exist
    cursor.execute("""
        SELECT circuit_purpose, provider_name, details_ordered_service_speed
        FROM circuits
        WHERE site_name = %s AND status = 'Enabled'
    """, (site,))
    
    dsr_circuits = cursor.fetchall()
    print("\n1. DSR Circuits:")
    for row in dsr_circuits:
        print(f"   {row[0]}: {row[1]} - '{row[2]}'")
    
    # 2. Check device notes parsing
    print("\n2. Device Notes Parsing:")
    device_notes = 'WAN 1\nComcast Workplace\n1000.0M x 35.0M\nWAN 2\nAT&T\n20.0M x 20.0M'
    print(f"   Raw notes: {repr(device_notes[:50])}...")
    
    # Simulate parsing
    from test_actual_parsing import parse_raw_notes
    wan1_notes, wan1_speed, wan2_notes, wan2_speed = parse_raw_notes(device_notes)
    print(f"   Parsed WAN1: '{wan1_notes}' / '{wan1_speed}'")
    print(f"   Parsed WAN2: '{wan2_notes}' / '{wan2_speed}'")
    
    # 3. Check DSR matching logic
    print("\n3. DSR Matching Logic:")
    print("   WAN1 should match Primary (Comcast Workplace)")
    print("   WAN2 should match Secondary (but there is none!)")
    
    # 4. Speed selection
    print("\n4. Speed Selection:")
    # WAN1 has DSR match
    wan1_dsr = {'speed': '1200.0M x 35.0M', 'provider': 'Comcast Workplace'} if dsr_circuits else None
    wan1_speed_to_use = wan1_dsr['speed'] if wan1_dsr and wan1_dsr.get('speed') else wan1_speed
    print(f"   WAN1: DSR speed '{wan1_dsr['speed']}' used instead of Meraki '{wan1_speed}'")
    
    # WAN2 has no DSR match
    wan2_dsr = None
    wan2_speed_to_use = wan2_dsr['speed'] if wan2_dsr and wan2_dsr.get('speed') else wan2_speed
    print(f"   WAN2: No DSR match, should use Meraki speed '{wan2_speed}'")
    
    # 5. Speed reformatting
    print("\n5. Speed Reformatting:")
    wan1_speed_final = reformat_speed(wan1_speed_to_use, 'Comcast Workplace')
    wan2_speed_final = reformat_speed(wan2_speed_to_use, 'AT&T')
    print(f"   WAN1 final: '{wan1_speed_final}'")
    print(f"   WAN2 final: '{wan2_speed_final}'")
    
    # 6. Check if there's manual override data
    print("\n6. Checking for manual overrides or other sources...")
    
    # Check if there are any manual circuit entries
    cursor.execute("""
        SELECT COUNT(*) FROM circuits 
        WHERE site_name = %s 
        AND details_ordered_service_speed LIKE '%% %%'
        AND details_ordered_service_speed NOT LIKE '%%x%%'
    """, (site,))
    
    manual_count = cursor.fetchone()[0]
    if manual_count > 0:
        print(f"   Found {manual_count} circuits with space-separated speeds!")
    
    # The issue might be in the database already
    print("\n7. Current Database State:")
    cursor.execute("""
        SELECT wan1_speed, wan2_speed, last_updated
        FROM enriched_circuits
        WHERE network_name = %s
    """, (site,))
    
    current = cursor.fetchone()
    if current:
        print(f"   WAN1: '{current[0]}'")
        print(f"   WAN2: '{current[1]}'")
        print(f"   Last updated: {current[2]}")
        
        # THE SMOKING GUN: The speed is already wrong in the database!
        if current[1] == '20.0 M':
            print("\n   >>> The '20.0 M' is already in the database!")
            print("   >>> This means it was set by a previous run or manual entry")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()