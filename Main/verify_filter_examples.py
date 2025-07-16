#!/usr/bin/env python3
"""Verify the Not Vision Ready filter logic with example scenarios"""

import re

def parse_speed(speed_str):
    """Parse speed string like '100.0M x 10.0M'"""
    if not speed_str or speed_str in ['N/A', 'null', 'Cell', 'Satellite', 'TBD', 'Unknown']:
        return None
    
    match = re.match(r'^([\d.]+)M\s*[xX]\s*([\d.]+)M$', speed_str)
    if match:
        return {
            'download': float(match.group(1)),
            'upload': float(match.group(2))
        }
    return None

def is_low_speed(speed):
    """Check if speed is considered 'low' (under 100M download OR under 10M upload)"""
    if not speed:
        return False
    return speed['download'] < 100.0 or speed['upload'] < 10.0

def is_cellular_speed(speed_str):
    """Check if speed field indicates cellular"""
    return speed_str == 'Cell'

def is_cellular_provider(provider_str):
    """Check if provider indicates cellular service"""
    if not provider_str:
        return False
    
    provider = provider_str.upper()
    return any(keyword in provider for keyword in ['AT&T', 'VERIZON', 'VZW', 'CELL', 'CELLULAR', 'WIRELESS'])

def analyze_site(wan1_speed, wan1_provider, wan2_speed, wan2_provider):
    """Apply the Not Vision Ready filter logic to a site"""
    
    # Exclude satellites
    if wan1_speed == 'Satellite' or wan2_speed == 'Satellite':
        return False, "Satellite excluded"
    
    # Parse speeds
    wan1_parsed = parse_speed(wan1_speed)
    wan2_parsed = parse_speed(wan2_speed)
    
    # Check cellular status
    wan1_cellular = is_cellular_speed(wan1_speed) or is_cellular_provider(wan1_provider)
    wan2_cellular = is_cellular_speed(wan2_speed) or is_cellular_provider(wan2_provider)
    
    # Check low speed status
    wan1_low = is_low_speed(wan1_parsed)
    wan2_low = is_low_speed(wan2_parsed)
    
    # Apply filter logic
    both_cellular = wan1_cellular and wan2_cellular
    low_speed_with_cellular = (wan1_low and wan2_cellular) or (wan2_low and wan1_cellular)
    
    if both_cellular:
        return True, "Both circuits are cellular"
    elif low_speed_with_cellular:
        if wan1_low and wan2_cellular:
            return True, f"WAN1 low speed ({wan1_speed}) + WAN2 cellular"
        elif wan2_low and wan1_cellular:
            return True, f"WAN2 low speed ({wan2_speed}) + WAN1 cellular"
    
    return False, "Meets Vision Ready requirements"

def main():
    """Test with realistic examples"""
    
    print("Not Vision Ready Filter - Example Analysis")
    print("=" * 80)
    
    examples = [
        # Example 1: Both cellular
        {
            'site': 'CAL 07',
            'wan1_provider': 'AT&T Broadband II',
            'wan1_speed': '300.0M x 30.0M',
            'wan2_provider': 'VZW',
            'wan2_speed': 'Cell'
        },
        # Example 2: Low speed + cellular  
        {
            'site': 'AZP 44',
            'wan1_provider': 'CenturyLink',
            'wan1_speed': '100.0M x 10.0M',  # This should NOT match (meets requirements)
            'wan2_provider': 'AT&T',
            'wan2_speed': 'Cell'
        },
        # Example 3: Actually low speed + cellular
        {
            'site': 'AZP 56',
            'wan1_provider': 'Comcast',
            'wan1_speed': '10.0M x 10.0M',  # Low download
            'wan2_provider': 'AT&T',
            'wan2_speed': 'Cell'
        },
        # Example 4: Good download, low upload + cellular
        {
            'site': 'COD 06', 
            'wan1_provider': 'Lumen',
            'wan1_speed': '100.0M x 5.0M',  # Low upload
            'wan2_provider': 'AT&T',
            'wan2_speed': 'Cell'
        },
        # Example 5: Both good speeds
        {
            'site': 'Good Site',
            'wan1_provider': 'Comcast',
            'wan1_speed': '200.0M x 20.0M',
            'wan2_provider': 'Charter',
            'wan2_speed': '100.0M x 10.0M'
        },
        # Example 6: Edge case - exactly at limits
        {
            'site': 'Edge Case',
            'wan1_provider': 'Comcast',
            'wan1_speed': '100.0M x 10.0M',  # Exactly at limits
            'wan2_provider': 'Charter', 
            'wan2_speed': '100.0M x 10.0M'
        }
    ]
    
    for example in examples:
        result, reason = analyze_site(
            example['wan1_speed'], example['wan1_provider'],
            example['wan2_speed'], example['wan2_provider']
        )
        
        status = "✅ MATCHES" if result else "❌ No match"
        
        print(f"\n{example['site']}:")
        print(f"  WAN1: {example['wan1_provider']} - {example['wan1_speed']}")
        print(f"  WAN2: {example['wan2_provider']} - {example['wan2_speed']}")
        print(f"  Result: {status} - {reason}")

if __name__ == "__main__":
    main()