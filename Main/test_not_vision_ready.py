#!/usr/bin/env python3
"""
Test script to analyze the "Not Vision Ready" filter logic
"""

from models import db, Circuit, session_factory
import re

def parse_speed(speed_str):
    """Parse speed string to get download/upload speeds"""
    if not speed_str or speed_str == 'Cell' or speed_str == 'Satellite':
        return None
    
    # Handle patterns like "100M x 100M", "50M x 10M", etc.
    match = re.search(r'(\d+(?:\.\d+)?)M?\s*x\s*(\d+(?:\.\d+)?)M?', speed_str)
    if match:
        download = float(match.group(1))
        upload = float(match.group(2))
        return {'download': download, 'upload': upload}
    
    return None

def is_low_speed(speed):
    """Check if speed is under 100M x 10M"""
    if not speed:
        return False
    return speed['download'] < 100.0 or speed['upload'] < 10.0

def is_cellular(speed_str):
    """Check if connection is cellular based on speed"""
    return speed_str == 'Cell'

def is_cellular_provider(provider_str):
    """Check if provider is cellular"""
    if not provider_str:
        return False
    
    # Clean HTML if present
    clean_provider = provider_str
    if '<' in provider_str:
        import re
        clean_provider = re.sub(r'<[^>]+>', '', provider_str)
    
    cellular_indicators = ['AT&T', 'Verizon', 'VZW', 'Cell', 'Cellular', 'Wireless']
    return any(indicator in clean_provider for indicator in cellular_indicators)

def test_not_vision_ready_filter():
    """Test the Not Vision Ready filter logic"""
    
    try:
        # Create database session
        session = session_factory()
        
        # Query all circuits with Discount-Tire tag
        circuits = session.query(Circuit).filter(
            Circuit.tags.ilike('%Discount-Tire%')
        ).all()
        
        print(f"Total Discount-Tire circuits: {len(circuits)}")
        
        not_vision_ready_sites = []
        
        for circuit in circuits:
            site_name = circuit.site_name
            
            # Get both WAN speeds and providers
            wan1_speed = circuit.wan1_speed or ''
            wan2_speed = circuit.wan2_speed or ''
            wan1_provider = circuit.wan1_provider or ''
            wan2_provider = circuit.wan2_provider or ''
            
            # Skip satellite
            if wan1_speed == 'Satellite' or wan2_speed == 'Satellite':
                continue
            
            # Parse speeds
            wan1_parsed = parse_speed(wan1_speed)
            wan2_parsed = parse_speed(wan2_speed)
            
            # Check cellular status
            wan1_is_low_speed = is_low_speed(wan1_parsed)
            wan2_is_low_speed = is_low_speed(wan2_parsed)
            wan1_is_cellular = is_cellular(wan1_speed) or is_cellular_provider(wan1_provider)
            wan2_is_cellular = is_cellular(wan2_speed) or is_cellular_provider(wan2_provider)
            
            # Apply Not Vision Ready criteria:
            # 1. BOTH circuits are cellular (cell/cell), OR
            # 2. One circuit has low speed (under 100M x 10M) AND the other is cellular
            qualifies = ((wan1_is_cellular and wan2_is_cellular) or 
                        (wan1_is_low_speed and wan2_is_cellular) or 
                        (wan2_is_low_speed and wan1_is_cellular))
            
            if qualifies:
                not_vision_ready_sites.append({
                    'site_name': site_name,
                    'wan1_speed': wan1_speed,
                    'wan2_speed': wan2_speed,
                    'wan1_provider': wan1_provider,
                    'wan2_provider': wan2_provider,
                    'wan1_cellular': wan1_is_cellular,
                    'wan2_cellular': wan2_is_cellular,
                    'wan1_low_speed': wan1_is_low_speed,
                    'wan2_low_speed': wan2_is_low_speed,
                    'reason': get_qualification_reason(wan1_is_cellular, wan2_is_cellular, 
                                                     wan1_is_low_speed, wan2_is_low_speed)
                })
        
        print(f"\nNot Vision Ready sites found: {len(not_vision_ready_sites)}")
        print("\nSample sites and their qualification reasons:")
        
        # Show first 10 sites with details
        for i, site in enumerate(not_vision_ready_sites[:10]):
            print(f"\n{i+1}. {site['site_name']}")
            print(f"   WAN1: {site['wan1_speed']} ({site['wan1_provider']})")
            print(f"   WAN2: {site['wan2_speed']} ({site['wan2_provider']})")
            print(f"   Reason: {site['reason']}")
        
        # Look for specific sites mentioned
        specific_sites = ['CAL 07', 'AZP 56', 'WAS 23', 'CAN 12', 'AZP 49']
        print(f"\nLooking for specific sites: {specific_sites}")
        
        found_sites = {}
        for site in not_vision_ready_sites:
            if site['site_name'] in specific_sites:
                found_sites[site['site_name']] = site
        
        for site_name in specific_sites:
            if site_name in found_sites:
                site = found_sites[site_name]
                print(f"\n✓ {site_name}: FOUND")
                print(f"   WAN1: {site['wan1_speed']} ({site['wan1_provider']})")
                print(f"   WAN2: {site['wan2_speed']} ({site['wan2_provider']})")
                print(f"   Reason: {site['reason']}")
            else:
                # Check if site exists at all
                site_exists = session.query(Circuit).filter(
                    Circuit.site_name == site_name,
                    Circuit.tags.ilike('%Discount-Tire%')
                ).first()
                if site_exists:
                    print(f"\n✗ {site_name}: EXISTS but doesn't qualify")
                    print(f"   WAN1: {site_exists.wan1_speed} ({site_exists.wan1_provider})")
                    print(f"   WAN2: {site_exists.wan2_speed} ({site_exists.wan2_provider})")
                else:
                    print(f"\n? {site_name}: NOT FOUND in Discount-Tire circuits")
        
        session.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def get_qualification_reason(wan1_cellular, wan2_cellular, wan1_low_speed, wan2_low_speed):
    """Get human readable reason for qualification"""
    if wan1_cellular and wan2_cellular:
        return "Both circuits are cellular (cell/cell)"
    elif wan1_low_speed and wan2_cellular:
        return "WAN1 low speed + WAN2 cellular"
    elif wan2_low_speed and wan1_cellular:
        return "WAN2 low speed + WAN1 cellular"
    else:
        return "Unknown qualification"

if __name__ == "__main__":
    test_not_vision_ready_filter()