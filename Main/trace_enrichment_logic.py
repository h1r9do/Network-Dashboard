#!/usr/bin/env python3
"""
Trace enrichment logic for FLT 02
"""

# Simulate the enrichment process for FLT 02
network_name = "FLT 02"
device_notes = 'WAN 1\nComcast\n300.0M x 35.0M\nWAN 2\nMetroNet\n300.0M x 300.0M'

# DSR circuits from database
dsr_circuits = [
    {'provider': 'MetroNet', 'speed': '300.0M x 300.0M', 'purpose': 'Secondary', 'ip': None, 'cost': None}
]

# Parse device notes (this works correctly as we tested)
wan1_notes = "Comcast"
wan1_speed = "300.0M x 35.0M"
wan2_notes = "MetroNet" 
wan2_speed = "300.0M x 300.0M"

print(f"Processing {network_name}:")
print(f"  Device notes parsed correctly:")
print(f"    WAN1: {wan1_notes} / {wan1_speed}")
print(f"    WAN2: {wan2_notes} / {wan2_speed}")
print()

# The matching logic from the script
# WAN1 should match to Primary, WAN2 to Secondary
wan1_dsr = None  # No Primary circuit in DSR data
wan2_dsr = dsr_circuits[0]  # Matches MetroNet Secondary

print("DSR matching results:")
print(f"  WAN1 DSR match: {wan1_dsr}")
print(f"  WAN2 DSR match: {wan2_dsr}")
print()

# Line 693-694 in the script:
# wan1_speed_to_use = wan1_dsr['speed'] if wan1_dsr and wan1_dsr.get('speed') else wan1_speed
# wan1_speed_final = reformat_speed(wan1_speed_to_use, wan1_provider)

wan1_speed_to_use = wan1_dsr['speed'] if wan1_dsr and wan1_dsr.get('speed') else wan1_speed
wan2_speed_to_use = wan2_dsr['speed'] if wan2_dsr and wan2_dsr.get('speed') else wan2_speed

print("Speed selection:")
print(f"  WAN1 speed to use: '{wan1_speed_to_use}' (from {'DSR' if wan1_dsr else 'Meraki notes'})")
print(f"  WAN2 speed to use: '{wan2_speed_to_use}' (from {'DSR' if wan2_dsr else 'Meraki notes'})")

# The issue is that wan1_speed should be "300.0M x 35.0M" but it's showing as "300.0 M"
# This suggests the parsing is not working correctly OR there's another source overriding it

print("\n" + "="*60)
print("The issue must be in the parsing logic. Let me check the actual parsing...")

import re

def parse_raw_notes_debug(raw_notes):
    """Debug version of parse_raw_notes"""
    if not raw_notes:
        return "", "", "", ""
    
    # Normalize line endings
    text = raw_notes.replace('\r\n', '\n').replace('\r', '\n')
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text.strip())
    print(f"\nNormalized text: {repr(text)}")
    
    wan1_pattern = re.compile(r'(?:WAN1|WAN\s*1)\s*:?\s*', re.IGNORECASE)
    wan2_pattern = re.compile(r'(?:WAN2|WAN\s*2)\s*:?\s*', re.IGNORECASE)
    
    # Split by WAN patterns
    parts = re.split(wan1_pattern, text, maxsplit=1)
    print(f"After WAN1 split: {parts}")
    
    wan1_text = ""
    wan2_text = ""
    
    if len(parts) > 1:
        after_wan1 = parts[1]
        wan2_split = re.split(wan2_pattern, after_wan1, maxsplit=1)
        wan1_text = wan2_split[0].strip()
        if len(wan2_split) > 1:
            wan2_text = wan2_split[1].strip()
    
    print(f"WAN1 text after split: {repr(wan1_text)}")
    print(f"WAN2 text after split: {repr(wan2_text)}")
    
    return wan1_text, wan2_text

# The issue is in line 130 of nightly_enriched_db.py:
# text = re.sub(r'\s+', ' ', raw_notes.strip())
# This replaces ALL whitespace (including newlines) with single spaces!

print("\nThe problem is the whitespace normalization!")
wan1_text, wan2_text = parse_raw_notes_debug(device_notes)

# This would turn "Comcast\n300.0M x 35.0M" into "Comcast 300.0M x 35.0M"
# And then the speed pattern matching might fail or extract incorrectly