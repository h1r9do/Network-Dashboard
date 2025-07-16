#!/usr/bin/env python3
"""
Simulate the speed parsing to find where "20.0 M" comes from
"""
import re

# From COD 28 device notes
device_notes = 'WAN 1\nComcast Workplace\n1000.0M x 35.0M\nWAN 2\nAT&T\n20.0M x 20.0M'

print("Testing speed parsing with COD 28 device notes:")
print(f"Device notes: {repr(device_notes)}")
print("\n" + "="*60 + "\n")

# The problematic normalization from line 129
text_normalized = re.sub(r'\s+', ' ', device_notes.strip())
print(f"After normalization: {repr(text_normalized)}")

# The WAN split
wan1_pattern = re.compile(r'(?:WAN1|WAN\s*1)\s*:?\s*', re.IGNORECASE)
wan2_pattern = re.compile(r'(?:WAN2|WAN\s*2)\s*:?\s*', re.IGNORECASE)

parts = re.split(wan1_pattern, text_normalized, maxsplit=1)
print(f"\nAfter WAN1 split: {parts}")

if len(parts) > 1:
    after_wan1 = parts[1]
    wan2_split = re.split(wan2_pattern, after_wan1, maxsplit=1)
    wan1_text = wan2_split[0].strip()
    wan2_text = wan2_split[1].strip() if len(wan2_split) > 1 else ""
    
    print(f"\nWAN1 text: '{wan1_text}'")
    print(f"WAN2 text: '{wan2_text}'")

# The speed pattern from the original
speed_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*([MG]B?)\s*x\s*(\d+(?:\.\d+)?)\s*([MG]B?)', re.IGNORECASE)

# Check WAN2 text
match = speed_pattern.search(wan2_text)
if match:
    print(f"\nSpeed pattern matched in WAN2: {match.group()}")
    print(f"Groups: {match.groups()}")
    
    # Extract based on original logic
    up_speed = float(match.group(1))
    up_unit = match.group(2).upper()
    down_speed = float(match.group(3))
    down_unit = match.group(4).upper()
    
    speed_str = f"{up_speed:.1f}{up_unit} x {down_speed:.1f}{down_unit}"
    print(f"Formatted speed: '{speed_str}'")
    
    # Provider would be everything before the match
    provider_name = wan2_text[:match.start()].strip()
    print(f"Provider: '{provider_name}'")
else:
    print("\nNo speed pattern match!")
    
# Now let's trace what happens when speed is just extracted as first number
print("\n" + "="*60)
print("\nAlternative parsing that might cause the issue:")

# What if the regex is failing and it's extracting just the first number?
simple_number = re.search(r'(\d+(?:\.\d+)?)\s*M', wan2_text)
if simple_number:
    print(f"Simple number match: '{simple_number.group()}'")
    print(f"This would give: '{simple_number.group(1)} M'")
    
# Check if there's a pattern where the speed is being extracted differently
print("\n" + "="*60)
print("\nChecking if extract_provider_and_speed might have a bug...")

# The segment for WAN2 would be "AT&T 20.0M x 20.0M"
segment = wan2_text
print(f"Segment to parse: '{segment}'")

# What if the provider extraction is taking too much?
# Original code does: provider_name = segment[:match.start()].strip()
# But what if there's additional processing?

# Check edge case: what if speed pattern doesn't match properly?
# The regex might fail if there's something subtle
test_patterns = [
    r'(\d+(?:\.\d+)?)\s*([MG]B?)\s*x\s*(\d+(?:\.\d+)?)\s*([MG]B?)',  # Original
    r'(\d+\.?\d*)\s*([MG])\s*x\s*(\d+\.?\d*)\s*([MG])',  # Simpler
    r'(\d+(?:\.\d+)?)\s*M\s*x\s*(\d+(?:\.\d+)?)\s*M',  # Just M
]

for i, pattern in enumerate(test_patterns):
    regex = re.compile(pattern, re.IGNORECASE)
    if regex.search(segment):
        print(f"Pattern {i+1} matches: {regex.search(segment).group()}")
    else:
        print(f"Pattern {i+1} does NOT match")