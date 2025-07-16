#!/usr/bin/env python3
"""
Fix COD 22 speed format issue
Since the device notes are wrong in Meraki, we'll use the DSR speed
"""
import psycopg2
import re
from datetime import datetime

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
    
    print("Fixing COD 22 speed format...")
    
    # Check DSR circuit for correct speed
    cursor.execute("""
        SELECT provider_name, details_ordered_service_speed
        FROM circuits
        WHERE site_name = 'COD 22' 
        AND circuit_purpose = 'Primary'
        AND status = 'Enabled'
    """)
    
    dsr_row = cursor.fetchone()
    if dsr_row:
        correct_speed = dsr_row[1]
        print(f"\nDSR Primary circuit has correct speed: '{correct_speed}'")
        
        # Update enriched circuits
        cursor.execute("""
            UPDATE enriched_circuits
            SET wan1_speed = %s,
                last_updated = %s
            WHERE network_name = 'COD 22'
        """, (correct_speed, datetime.utcnow()))
        
        conn.commit()
        print(f"Updated COD 22 WAN1 speed to '{correct_speed}'")
        
        # Verify
        cursor.execute("""
            SELECT wan1_speed, wan1_provider
            FROM enriched_circuits
            WHERE network_name = 'COD 22'
        """)
        
        result = cursor.fetchone()
        print(f"\nVerification: WAN1 is now '{result[0]}' / {result[1]}")
    else:
        print("No DSR Primary circuit found for COD 22")
    
    # Also check if there are other sites with missing units
    print("\n" + "="*60)
    print("\nChecking for other sites with missing units (e.g., '300 x 30')...")
    
    cursor.execute("""
        SELECT network_name, wan1_speed, wan2_speed
        FROM enriched_circuits
        WHERE wan1_speed ~ '^\d+\s*x\s*\d+$' 
           OR wan2_speed ~ '^\d+\s*x\s*\d+$'
        ORDER BY network_name
    """)
    
    other_sites = cursor.fetchall()
    if other_sites:
        print(f"\nFound {len(other_sites)} sites with missing units:")
        for site in other_sites:
            issues = []
            if re.match(r'^\d+\s*x\s*\d+$', site[1] or ''):
                issues.append(f"WAN1: '{site[1]}'")
            if re.match(r'^\d+\s*x\s*\d+$', site[2] or ''):
                issues.append(f"WAN2: '{site[2]}'")
            print(f"  {site[0]}: {', '.join(issues)}")
        
        print(f"\nThese sites need their device notes fixed in Meraki!")
    else:
        print("\nNo other sites found with missing units.")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()