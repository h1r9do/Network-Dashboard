#!/usr/bin/env python3
"""
Test the actual parsing logic from nightly_enriched_db.py
"""
import re

# Exact function from the script
def parse_raw_notes(raw_notes):
    """Parse raw notes - exact logic from legacy meraki_mx.py"""
    if not raw_notes or not raw_notes.strip():
        return "", "", "", ""
    
    text = re.sub(r'\s+', ' ', raw_notes.strip())
    wan1_pattern = re.compile(r'(?:WAN1|WAN\s*1)\s*:?\s*', re.IGNORECASE)
    wan2_pattern = re.compile(r'(?:WAN2|WAN\s*2)\s*:?\s*', re.IGNORECASE)
    speed_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*([MG]B?)\s*x\s*(\d+(?:\.\d+)?)\s*([MG]B?)', re.IGNORECASE)
    
    def extract_provider_and_speed(segment):
        """Helper to extract provider name and speed from a text segment."""
        match = speed_pattern.search(segment)
        if match:
            up_speed = float(match.group(1))
            up_unit = match.group(2).upper()
            down_speed = float(match.group(3))
            down_unit = match.group(4).upper()
            
            if up_unit in ['G', 'GB']:
                up_speed *= 1000
                up_unit = 'M'
            elif up_unit in ['M', 'MB']:
                up_unit = 'M'
                
            if down_unit in ['G', 'GB']:
                down_speed *= 1000
                down_unit = 'M'
            elif down_unit in ['M', 'MB']:
                down_unit = 'M'
                
            speed_str = f"{up_speed:.1f}{up_unit} x {down_speed:.1f}{down_unit}"
            provider_name = segment[:match.start()].strip()
            provider_name = re.sub(r'[^\w\s.&|-]', ' ', provider_name).strip()
            provider_name = re.sub(r'\s+', ' ', provider_name).strip()
            return provider_name, speed_str
        else:
            # Check for cellular provider patterns ending with "Cell"
            if segment.strip().endswith(' Cell'):
                provider_name = segment.strip()[:-5].strip()  # Remove " Cell" from end
                return provider_name, "Cell"
            # Check for Starlink + Satellite pattern
            elif 'starlink' in segment.lower() and 'satellite' in segment.lower():
                return "Starlink", "Satellite"
            # Check for Verizon Business (likely cellular backup)
            elif 'verizon business' in segment.lower() and len(segment.strip()) < 20:
                return "Verizon Business", "Cell"
            # Check for VZ Gateway (Verizon cellular)
            elif 'vz gateway' in segment.lower() or 'vzg' in segment.lower():
                return "VZW Cell", "Cell"
            # Check for DIG/Digi cellular
            elif segment.strip().upper() in ['DIG', 'DIGI']:
                return "Digi", "Cell"
            # Check for Accelerated provider (cellular)
            elif 'accelerated' in segment.strip().lower():
                return "Accelerated", "Cell"
            # Check for Unknown secondary circuits (skip these)
            elif segment.strip().lower() in ['unknown']:
                return "", ""
            # Handle "Cell Cell" case specifically
            elif segment.strip().lower() == 'cell cell':
                return "VZW Cell", "Cell"
            else:
                provider_name = re.sub(r'[^\w\s.&|-]', ' ', segment).strip()
                provider_name = re.sub(r'\s+', ' ', provider_name).strip()
                return provider_name, ""
    
    wan1_text = ""
    wan2_text = ""
    parts = re.split(wan1_pattern, text, maxsplit=1)
    if len(parts) > 1:
        after_wan1 = parts[1]
        wan2_split = re.split(wan2_pattern, after_wan1, maxsplit=1)
        wan1_text = wan2_split[0].strip()
        if len(wan2_split) > 1:
            wan2_text = wan2_split[1].strip()
    else:
        parts = re.split(wan2_pattern, text, maxsplit=1)
        if len(parts) > 1:
            wan2_text = parts[1].strip()
        else:
            wan1_text = text.strip()
    
    wan1_provider, wan1_speed = extract_provider_and_speed(wan1_text)
    wan2_provider, wan2_speed = extract_provider_and_speed(wan2_text)
    
    return wan1_provider, wan1_speed, wan2_provider, wan2_speed

# Test cases
test_cases = [
    # COD 28 - has the issue
    'WAN 1\nComcast Workplace\n1000.0M x 35.0M\nWAN 2\nAT&T\n20.0M x 20.0M',
    # CAN 30 - has the issue  
    'WAN 1\nAT&T Broadband II\n1000.0M x 1000.0M\nWAN 2\nComcast\n300.0M x 35.0M',
    # Try some edge cases
    'WAN1\nComcast\n20.0 M x 5.0 M\nWAN2\nAT&T\n100.0M',
    # Single speed without x
    'WAN 1\nComcast\n300M\nWAN 2\nAT&T\n50M'
]

for i, notes in enumerate(test_cases):
    print(f"\nTest case {i+1}:")
    print(f"Notes: {repr(notes[:50])}...")
    w1p, w1s, w2p, w2s = parse_raw_notes(notes)
    print(f"WAN1: provider='{w1p}', speed='{w1s}'")
    print(f"WAN2: provider='{w2p}', speed='{w2s}'")
    
    # Check if empty speed
    if w1s == "":
        print("  WARNING: WAN1 speed is empty!")
    if w2s == "":
        print("  WARNING: WAN2 speed is empty!")

# Now test what happens when we have a speed without x
print("\n" + "="*60)
print("\nTesting single speed values (no x)...")

single_speeds = [
    "Comcast 300M",
    "AT&T 50.0M",
    "CenturyLink 20.0 M",
    "Spectrum 100 M"
]

for segment in single_speeds:
    print(f"\nSegment: '{segment}'")
    # The speed pattern requires 'x'
    speed_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*([MG]B?)\s*x\s*(\d+(?:\.\d+)?)\s*([MG]B?)', re.IGNORECASE)
    match = speed_pattern.search(segment)
    if match:
        print(f"  Matches: {match.group()}")
    else:
        print(f"  No match - would return empty speed!")
        # What does it extract as provider?
        provider_name = re.sub(r'[^\w\s.&|-]', ' ', segment).strip()
        provider_name = re.sub(r'\s+', ' ', provider_name).strip()
        print(f"  Provider would be: '{provider_name}'")