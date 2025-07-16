#!/usr/bin/env python3
"""
Test speed parsing for FLT 02 and GAA 01
"""
import re

# Device notes from the database
flt02_notes = 'WAN 1\nComcast\n300.0M x 35.0M\nWAN 2\nMetroNet\n300.0M x 300.0M'
gaa01_notes = 'WAN 1\nComcast\n300.0M x 35.0M\nWAN 2\nAT&T Broadband II\n300.0M x 300.0M'

def parse_raw_notes(raw_notes):
    """Parse raw device notes to extract provider and speed info."""
    if not raw_notes:
        return "", "", "", ""
    
    # Clean up the text
    text = raw_notes.replace('\r\n', '\n').replace('\r', '\n')
    
    # Split by WAN sections
    wan1_pattern = re.compile(r'(?:WAN\s*1|WAN1)(?:\s*:)?', re.IGNORECASE)
    wan2_pattern = re.compile(r'(?:WAN\s*2|WAN2)(?:\s*:)?', re.IGNORECASE)
    
    # Speed pattern to match formats like "300.0M x 35.0M"
    speed_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*([MG]B?)\s*x\s*(\d+(?:\.\d+)?)\s*([MG]B?)', re.IGNORECASE)
    
    # Split the text by WAN sections
    parts = re.split(wan1_pattern, text, maxsplit=1)
    wan1_text = ""
    wan2_text = ""
    
    if len(parts) > 1:
        # Found WAN 1
        after_wan1 = parts[1]
        wan2_split = re.split(wan2_pattern, after_wan1, maxsplit=1)
        wan1_text = wan2_split[0].strip()
        if len(wan2_split) > 1:
            wan2_text = wan2_split[1].strip()
    else:
        # Try WAN 2 pattern
        parts = re.split(wan2_pattern, text, maxsplit=1)
        if len(parts) > 1:
            wan2_text = parts[1].strip()
    
    print(f"WAN1 text: {repr(wan1_text)}")
    print(f"WAN2 text: {repr(wan2_text)}")
    
    # Extract provider and speed from each section
    def extract_provider_and_speed(section):
        if not section:
            return "", ""
            
        lines = section.strip().split('\n')
        provider = ""
        speed = ""
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Check if this line contains a speed pattern
            speed_match = speed_pattern.search(line)
            if speed_match:
                speed = line
                # Previous non-empty line should be the provider
                for j in range(i-1, -1, -1):
                    if lines[j].strip():
                        provider = lines[j].strip()
                        break
                break
            
        print(f"  Extracted: provider='{provider}', speed='{speed}'")
        return provider, speed
    
    wan1_provider, wan1_speed = extract_provider_and_speed(wan1_text)
    wan2_provider, wan2_speed = extract_provider_and_speed(wan2_text)
    
    return wan1_provider, wan1_speed, wan2_provider, wan2_speed

print("Testing FLT 02:")
print(f"Notes: {repr(flt02_notes)}")
w1p, w1s, w2p, w2s = parse_raw_notes(flt02_notes)
print(f"Result: WAN1='{w1p}' / '{w1s}', WAN2='{w2p}' / '{w2s}'")
print()

print("Testing GAA 01:")
print(f"Notes: {repr(gaa01_notes)}")
w1p, w1s, w2p, w2s = parse_raw_notes(gaa01_notes)
print(f"Result: WAN1='{w1p}' / '{w1s}', WAN2='{w2p}' / '{w2s}'")

# Now test the actual parsing function from the nightly script
print("\n" + "="*60)
print("Testing with actual function logic:")

def extract_provider_and_speed_actual(segment):
    """Actual extraction logic from nightly_enriched_db.py"""
    speed_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*([MG]B?)\s*x\s*(\d+(?:\.\d+)?)\s*([MG]B?)', re.IGNORECASE)
    
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
        # No speed pattern found
        provider_name = re.sub(r'[^\w\s.&|-]', ' ', segment).strip()
        provider_name = re.sub(r'\s+', ' ', provider_name).strip()
        return provider_name, ""

# Test with the actual segments
wan1_segment = "Comcast\n300.0M x 35.0M"
print(f"\nTesting WAN1 segment: {repr(wan1_segment)}")
provider, speed = extract_provider_and_speed_actual(wan1_segment)
print(f"Result: provider='{provider}', speed='{speed}'")