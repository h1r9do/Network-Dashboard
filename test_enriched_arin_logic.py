#!/usr/bin/env python3
"""Test how the enriched script gets and uses ARIN data"""

import psycopg2

# Database connection
conn = psycopg2.connect(
    host='localhost',
    database='dsrcircuits',
    user='dsruser',
    password='dsrpass123'
)
cur = conn.cursor()

print("=== Testing Enriched Script ARIN Logic ===\n")

# Test CAN 24 - the problematic site
site = 'CAN 24'
print(f"1. Getting data for {site} from meraki_inventory:")

cur.execute("""
    SELECT 
        network_name,
        device_serial,
        wan1_ip,
        wan1_arin_provider,
        wan2_ip,
        wan2_arin_provider,
        device_notes
    FROM meraki_inventory
    WHERE network_name = %s
    AND device_model LIKE 'MX%%'
""", (site,))

result = cur.fetchone()
if result:
    network_name, device_serial, wan1_ip, wan1_arin, wan2_ip, wan2_arin, device_notes = result
    print(f"  Network: {network_name}")
    print(f"  Device: {device_serial}")
    print(f"  WAN1 IP: {wan1_ip}")
    print(f"  WAN1 ARIN: {wan1_arin}")
    print(f"  WAN2 IP: {wan2_ip}")
    print(f"  WAN2 ARIN: {wan2_arin}")
    print(f"  Device Notes: {device_notes}")
    
    print(f"\n2. The enriched script would use:")
    print(f"  - WAN1 ARIN provider: {wan1_arin} (from meraki_inventory table)")
    print(f"  - WAN2 ARIN provider: {wan2_arin} (from meraki_inventory table)")
    print(f"\n  It does NOT make fresh ARIN API calls!")
    
    # Check what's in enriched_circuits
    print(f"\n3. Current enriched_circuits data:")
    cur.execute("""
        SELECT wan1_provider, wan2_provider, last_updated
        FROM enriched_circuits
        WHERE network_name = %s
    """, (site,))
    
    enriched = cur.fetchone()
    if enriched:
        print(f"  WAN1 Provider: {enriched[0]}")
        print(f"  WAN2 Provider: {enriched[1]}")
        print(f"  Last Updated: {enriched[2]}")

# Also test CAL 24 for comparison
print(f"\n4. Comparing with CAL 24:")
cur.execute("""
    SELECT 
        network_name,
        wan1_ip,
        wan1_arin_provider,
        wan2_ip,
        wan2_arin_provider
    FROM meraki_inventory
    WHERE network_name = 'CAL 24'
    AND device_model LIKE 'MX%%'
""")

cal_result = cur.fetchone()
if cal_result:
    print(f"  Network: {cal_result[0]}")
    print(f"  WAN1: {cal_result[1]} - {cal_result[2]}")
    print(f"  WAN2: {cal_result[3]} - {cal_result[4]}")

conn.close()

print("\n5. KEY INSIGHT:")
print("   The enriched script relies on meraki_inventory.wan1_arin_provider")
print("   and wan2_arin_provider columns that are populated by nightly_meraki_db.py")
print("   using the sophisticated parse_arin_response() function.")
print("\n   The ARIN refresh in the edit modal should read from these columns")
print("   instead of making fresh ARIN calls with simplified parsing!")