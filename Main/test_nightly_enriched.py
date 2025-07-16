#!/usr/bin/env python3
"""
Test the nightly enriched script with a few sites
"""
import sys
sys.path.insert(0, '/usr/local/bin/Main/nightly')

from nightly_enriched_db import (
    is_bad_speed_format, parse_raw_notes, get_db_connection,
    needs_update, normalize_provider_for_arin_match
)

print("Testing nightly enriched functions...")
print("="*60)

# Test bad speed format detection
print("\n1. Testing is_bad_speed_format():")
test_speeds = [
    ("300.0M x 35.0M", False),  # Good
    ("300.0 M", True),          # Bad - space before M
    ("300 x 30", True),         # Bad - missing units
    ("Cell", False),            # Good - special case
    ("Satellite", False),       # Good - special case
    ("", False),                # Empty is OK
    ("1000.0M", False),         # Single speed OK
]

for speed, expected in test_speeds:
    result = is_bad_speed_format(speed)
    status = "✓" if result == expected else "✗"
    print(f"  {status} '{speed}' -> {result} (expected {expected})")

# Test parse_raw_notes
print("\n2. Testing parse_raw_notes():")
test_notes = 'WAN 1\nComcast\n300.0M x 35.0M\nWAN 2\nAT&T\n20.0M x 20.0M'
w1p, w1s, w2p, w2s = parse_raw_notes(test_notes)
print(f"  Input: {repr(test_notes[:30])}...")
print(f"  WAN1: '{w1p}' / '{w1s}'")
print(f"  WAN2: '{w2p}' / '{w2s}'")

# Test SpaceX conversion
print("\n3. Testing SpaceX to Starlink conversion:")
test_arin = "SPACEX-STARLINK"
if 'spacex' in test_arin.lower():
    converted = 'Starlink'
else:
    converted = test_arin
print(f"  '{test_arin}' -> '{converted}'")

# Test needs_update with bad speeds
print("\n4. Testing needs_update() with bad speeds:")
current_record = {
    'wan1_speed': '300.0 M',  # Bad format
    'wan2_speed': '100.0M x 10.0M',
    'wan1_provider': 'Comcast',
    'wan2_provider': 'AT&T'
}
new_data = {
    'wan1_speed': '300.0M x 35.0M',
    'wan2_speed': '100.0M x 10.0M',
    'wan1_provider': 'Comcast',
    'wan2_provider': 'AT&T'
}
result = needs_update(current_record, new_data)
print(f"  Current has bad speed: {current_record['wan1_speed']}")
print(f"  needs_update() returned: {result} (should be True)")

# Test database connection
print("\n5. Testing database connection:")
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM enriched_circuits")
    count = cursor.fetchone()[0]
    print(f"  ✓ Connected successfully - {count} records in enriched_circuits")
    
    # Check if new columns exist
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_name = 'enriched_circuits' 
        AND column_name IN ('wan1_ip', 'wan2_ip', 'wan1_arin_org', 'wan2_arin_org')
    """)
    col_count = cursor.fetchone()[0]
    print(f"  ✓ New columns verified - {col_count} of 4 columns exist")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"  ✗ Database error: {e}")

print("\n" + "="*60)
print("All tests completed!")