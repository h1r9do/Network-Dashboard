#!/usr/bin/env python3
"""Test the corrected Not Vision Ready filter logic"""

def parse_speed(speed_str):
    """Parse speed string like '100.0M x 10.0M'"""
    if not speed_str or speed_str in ['N/A', 'null', 'Cell', 'Satellite', 'TBD', 'Unknown']:
        return None
    
    import re
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

def test_not_vision_ready_logic():
    """Test the filter logic with various scenarios"""
    
    print("Testing Not Vision Ready Filter Logic")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        # Case 1: Both cellular - should match
        {
            'name': 'Both Cell speeds',
            'wan1_speed': 'Cell',
            'wan1_provider': 'AT&T',
            'wan2_speed': 'Cell', 
            'wan2_provider': 'Verizon',
            'expected': True,
            'reason': 'Both cellular'
        },
        # Case 2: Both cellular providers - should match
        {
            'name': 'Both cellular providers',
            'wan1_speed': '100.0M x 10.0M',
            'wan1_provider': 'AT&T Broadband',
            'wan2_speed': '50.0M x 5.0M',
            'wan2_provider': 'Verizon Business',
            'expected': True,
            'reason': 'Both cellular providers'
        },
        # Case 3: Low speed + cellular - should match
        {
            'name': 'Low speed + cellular',
            'wan1_speed': '50.0M x 5.0M',  # Low speed (< 100M AND < 10M)
            'wan1_provider': 'Comcast',
            'wan2_speed': 'Cell',
            'wan2_provider': 'AT&T',
            'expected': True,
            'reason': 'Low speed + cellular'
        },
        # Case 4: Good speed + cellular - should NOT match  
        {
            'name': 'Good speed + cellular',
            'wan1_speed': '100.0M x 10.0M',  # NOT low speed (100M >= limit, 10M >= limit)
            'wan1_provider': 'Comcast',
            'wan2_speed': 'Cell',
            'wan2_provider': 'AT&T',
            'expected': False,
            'reason': 'Speed meets requirements'
        },
        # Case 5: Low download, good upload + cellular - should match
        {
            'name': 'Low download, good upload + cellular',
            'wan1_speed': '50.0M x 15.0M',  # Low download (< 100M) even with good upload
            'wan1_provider': 'Comcast',
            'wan2_speed': 'Cell',
            'wan2_provider': 'AT&T',
            'expected': True,
            'reason': 'Low download speed + cellular'
        },
        # Case 6: Good download, low upload + cellular - should match
        {
            'name': 'Good download, low upload + cellular',
            'wan1_speed': '150.0M x 5.0M',  # Good download but low upload
            'wan1_provider': 'Comcast',
            'wan2_speed': 'Cell',
            'wan2_provider': 'AT&T',
            'expected': True,
            'reason': 'Low upload speed + cellular'
        },
        # Case 7: Both satellite - should NOT match (excluded)
        {
            'name': 'Both satellite',
            'wan1_speed': 'Satellite',
            'wan1_provider': 'Starlink',
            'wan2_speed': 'Satellite',
            'wan2_provider': 'Starlink',
            'expected': False,
            'reason': 'Satellite excluded'
        },
        # Case 8: Both good speeds, no cellular - should NOT match
        {
            'name': 'Both good speeds, no cellular',
            'wan1_speed': '100.0M x 10.0M',
            'wan1_provider': 'Comcast',
            'wan2_speed': '200.0M x 20.0M',
            'wan2_provider': 'Charter',
            'expected': False,
            'reason': 'Both speeds good, no cellular'
        }
    ]
    
    # Run tests
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print(f"  WAN1: {test['wan1_provider']} - {test['wan1_speed']}")
        print(f"  WAN2: {test['wan2_provider']} - {test['wan2_speed']}")
        
        # Parse speeds
        wan1_parsed = parse_speed(test['wan1_speed'])
        wan2_parsed = parse_speed(test['wan2_speed'])
        
        # Check cellular status
        wan1_cellular = is_cellular_speed(test['wan1_speed']) or is_cellular_provider(test['wan1_provider'])
        wan2_cellular = is_cellular_speed(test['wan2_speed']) or is_cellular_provider(test['wan2_provider'])
        
        # Check low speed status
        wan1_low = is_low_speed(wan1_parsed)
        wan2_low = is_low_speed(wan2_parsed)
        
        # Exclude satellites
        if test['wan1_speed'] == 'Satellite' or test['wan2_speed'] == 'Satellite':
            result = False
        else:
            # Apply filter logic
            both_cellular = wan1_cellular and wan2_cellular
            low_speed_with_cellular = (wan1_low and wan2_cellular) or (wan2_low and wan1_cellular)
            result = both_cellular or low_speed_with_cellular
            
            # Debug output for failed cases
            if result != test['expected']:
                print(f"      DEBUG: both_cellular={both_cellular}, low_speed_with_cellular={low_speed_with_cellular}")
                print(f"      DEBUG: (wan1_low and wan2_cellular)={(wan1_low and wan2_cellular)}")
                print(f"      DEBUG: (wan2_low and wan1_cellular)={(wan2_low and wan1_cellular)}")
                print(f"      DEBUG: result={result}")
        
        # Check result
        if result == test['expected']:
            print(f"  ✅ PASS - {test['reason']}")
            passed += 1
        else:
            print(f"  ❌ FAIL - Expected {test['expected']}, got {result}")
            print(f"      WAN1 cellular: {wan1_cellular}, low: {wan1_low}")
            print(f"      WAN2 cellular: {wan2_cellular}, low: {wan2_low}")
            print(f"      Both cellular: {wan1_cellular and wan2_cellular}")
            print(f"      Low+cellular: {(wan1_low and wan2_cellular) or (wan2_low and wan1_cellular)}")
            failed += 1
    
    print(f"\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The filter logic is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the logic.")

if __name__ == "__main__":
    test_not_vision_ready_logic()