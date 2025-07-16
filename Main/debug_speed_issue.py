#!/usr/bin/env python3
"""
Debug speed parsing issue for FLT 02 and GAA 01
"""
import psycopg2
import re
from datetime import datetime, timezone

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

# Function from nightly_enriched_db.py
def reformat_speed(speed_str, provider):
    """Reformat speed string - handle special cases"""
    if not speed_str or str(speed_str).lower() == 'nan':
        return ""
    
    # Special cases for cellular/satellite
    provider_lower = str(provider).lower()
    if provider_lower == 'cell' or any(term in provider_lower for term in ['vzw cell', 'verizon cell', 'digi', 'inseego']):
        return "Cell"
    if 'starlink' in provider_lower:
        return "Satellite"
    
    return str(speed_str).strip()

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
    
    # Get DSR circuits data for these sites
    cursor.execute("""
        SELECT site_name, provider_name, details_ordered_service_speed, circuit_purpose
        FROM circuits
        WHERE site_name IN ('FLT 02', 'GAA 01')
        AND status = 'Enabled'
        ORDER BY site_name, circuit_purpose
    """)
    
    print("DSR Circuits data:")
    dsr_data = cursor.fetchall()
    for row in dsr_data:
        print(f"  {row[0]} - {row[3]}: Provider='{row[1]}', Speed='{row[2]}'")
    
    print("\n" + "="*60 + "\n")
    
    # Check if there's a match in the nightly process
    # The issue might be that DSR data is overriding the Meraki notes
    
    # Simulate the speed processing
    test_speeds = [
        ("300.0M x 35.0M", "Comcast"),
        ("300.0M x 300.0M", "MetroNet"),
        ("300.0M x 300.0M", "AT&T Broadband II"),
        ("300.0 M", "Comcast"),  # This is what's showing up
    ]
    
    print("Testing reformat_speed function:")
    for speed, provider in test_speeds:
        result = reformat_speed(speed, provider)
        print(f"  reformat_speed('{speed}', '{provider}') = '{result}'")
    
    print("\n" + "="*60 + "\n")
    
    # Let's check if DSR speeds might be the issue
    print("Checking if DSR speeds contain the problematic format:")
    for row in dsr_data:
        speed = row[2]
        if speed and ' M' in speed and ' x ' not in speed:
            print(f"  FOUND ISSUE: {row[0]} - {row[3]} has speed '{speed}'")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()