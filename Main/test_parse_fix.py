#!/usr/bin/env python3
"""
Test the parsing fix before applying
"""
import re

# Test data
test_notes = [
    'WAN 1\nComcast\n300.0M x 35.0M\nWAN 2\nMetroNet\n300.0M x 300.0M',
    'WAN 1\nComcast\n300.0M x 35.0M\nWAN 2\nAT&T Broadband II\n300.0M x 300.0M'
]

def parse_raw_notes_original(raw_notes):
    """Original parsing logic that has the bug"""
    if not raw_notes or not raw_notes.strip():
        return "", "", "", ""
    
    # This is the problematic line - converts newlines to spaces
    text = re.sub(r'\s+', ' ', raw_notes.strip())
    print(f"After whitespace normalization: {repr(text)}")
    
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
    
    print(f"WAN1 segment: {repr(wan1_text)}")
    print(f"WAN2 segment: {repr(wan2_text)}")
    
    wan1_provider, wan1_speed = extract_provider_and_speed(wan1_text)
    wan2_provider, wan2_speed = extract_provider_and_speed(wan2_text)
    
    return wan1_provider, wan1_speed, wan2_provider, wan2_speed

def parse_raw_notes_fixed(raw_notes):
    """Fixed parsing logic that handles newlines properly"""
    if not raw_notes or not raw_notes.strip():
        return "", "", "", ""
    
    # DON'T normalize newlines away - we need them for parsing!
    wan1_pattern = re.compile(r'(?:WAN1|WAN\s*1)\s*:?\s*', re.IGNORECASE)
    wan2_pattern = re.compile(r'(?:WAN2|WAN\s*2)\s*:?\s*', re.IGNORECASE)
    
    # Split by WAN patterns
    parts = re.split(wan1_pattern, raw_notes, maxsplit=1)
    wan1_text = ""
    wan2_text = ""
    
    if len(parts) > 1:
        after_wan1 = parts[1]
        wan2_split = re.split(wan2_pattern, after_wan1, maxsplit=1)
        wan1_text = wan2_split[0].strip()
        if len(wan2_split) > 1:
            wan2_text = wan2_split[1].strip()
    else:
        parts = re.split(wan2_pattern, raw_notes, maxsplit=1)
        if len(parts) > 1:
            wan2_text = parts[1].strip()
        else:
            wan1_text = raw_notes.strip()
    
    print(f"WAN1 text (with newlines): {repr(wan1_text)}")
    print(f"WAN2 text (with newlines): {repr(wan2_text)}")
    
    # Extract provider and speed from multiline text
    def extract_provider_and_speed_fixed(text):
        """Extract provider and speed from multiline text"""
        if not text:
            return "", ""
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        provider = ""
        speed = ""
        
        # Look for speed pattern in lines
        speed_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*([MG]B?)\s*x\s*(\d+(?:\.\d+)?)\s*([MG]B?)', re.IGNORECASE)
        
        for i, line in enumerate(lines):
            match = speed_pattern.search(line)
            if match:
                # Format the speed properly
                down_speed = float(match.group(1))
                down_unit = match.group(2).upper().rstrip('B')
                up_speed = float(match.group(3))
                up_unit = match.group(4).upper().rstrip('B')
                
                if down_unit == 'G':
                    down_speed *= 1000
                    down_unit = 'M'
                if up_unit == 'G':
                    up_speed *= 1000
                    up_unit = 'M'
                    
                speed = f"{down_speed:.1f}{down_unit} x {up_speed:.1f}{up_unit}"
                
                # Provider is usually the line before the speed
                if i > 0:
                    provider = lines[i-1]
                break
        
        # Handle special cases (Cell, Satellite, etc.)
        if not speed and lines:
            provider = lines[0]
            if 'cell' in provider.lower() or provider.strip().endswith(' Cell'):
                return provider.replace(' Cell', '').strip(), "Cell"
            elif 'satellite' in provider.lower() or 'starlink' in provider.lower():
                return "Starlink", "Satellite"
        
        return provider, speed
    
    wan1_provider, wan1_speed = extract_provider_and_speed_fixed(wan1_text)
    wan2_provider, wan2_speed = extract_provider_and_speed_fixed(wan2_text)
    
    return wan1_provider, wan1_speed, wan2_provider, wan2_speed

# Test both versions
for notes in test_notes:
    print("\n" + "="*60)
    print(f"Testing with: {repr(notes[:50])}...")
    
    print("\nORIGINAL PARSING:")
    w1p, w1s, w2p, w2s = parse_raw_notes_original(notes)
    print(f"Result: WAN1='{w1p}' / '{w1s}', WAN2='{w2p}' / '{w2s}'")
    
    print("\nFIXED PARSING:")
    w1p, w1s, w2p, w2s = parse_raw_notes_fixed(notes)
    print(f"Result: WAN1='{w1p}' / '{w1s}', WAN2='{w2p}' / '{w2s}'")