#!/usr/bin/env python3
"""
Trace where the speed issue is coming from
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
    
    # Check one of the problem sites in detail
    print("Checking COD 28 (has '1200.0M x 35.0M' for WAN1 but '20.0 M' for WAN2)...")
    
    # Check Meraki inventory
    cursor.execute("""
        SELECT network_name, device_notes, wan1_ip, wan2_ip, 
               wan1_arin_provider, wan2_arin_provider
        FROM meraki_inventory
        WHERE network_name = 'COD 28'
    """)
    
    meraki_row = cursor.fetchone()
    if meraki_row:
        print(f"\nMeraki Inventory:")
        print(f"  Device Notes: {repr(meraki_row[1])}")
        print(f"  WAN1 IP: {meraki_row[2]}, ARIN: {meraki_row[4]}")
        print(f"  WAN2 IP: {meraki_row[3]}, ARIN: {meraki_row[5]}")
    
    # Check enriched circuits
    cursor.execute("""
        SELECT network_name, wan1_speed, wan1_provider, wan2_speed, wan2_provider,
               wan1_confirmed, wan2_confirmed, last_updated
        FROM enriched_circuits
        WHERE network_name = 'COD 28'
    """)
    
    enriched_row = cursor.fetchone()
    if enriched_row:
        print(f"\nEnriched Circuits:")
        print(f"  WAN1: '{enriched_row[1]}' / {enriched_row[2]} (confirmed: {enriched_row[5]})")
        print(f"  WAN2: '{enriched_row[3]}' / {enriched_row[4]} (confirmed: {enriched_row[6]})")
        print(f"  Last Updated: {enriched_row[7]}")
    
    # Check DSR circuits
    cursor.execute("""
        SELECT site_name, circuit_purpose, provider_name, details_ordered_service_speed
        FROM circuits
        WHERE site_name = 'COD 28'
        AND status = 'Enabled'
    """)
    
    print(f"\nDSR Circuits:")
    dsr_rows = cursor.fetchall()
    for row in dsr_rows:
        print(f"  {row[1]}: {row[2]} - '{row[3]}'")
    
    # Now check a few more sites with the issue
    print("\n" + "="*60)
    print("\nChecking more sites with space before M...")
    
    cursor.execute("""
        SELECT ec.network_name, ec.wan1_speed, ec.wan2_speed,
               mi.device_notes
        FROM enriched_circuits ec
        JOIN meraki_inventory mi ON ec.network_name = mi.network_name
        WHERE ec.wan1_speed LIKE '%% M' OR ec.wan2_speed LIKE '%% M'
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"\n{row[0]}:")
        print(f"  Enriched: WAN1='{row[1]}', WAN2='{row[2]}'")
        if row[3]:
            # Parse the device notes to see what they should be
            notes_lines = row[3].split('\n')
            print(f"  Device Notes lines: {[line for line in notes_lines if line.strip()]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()