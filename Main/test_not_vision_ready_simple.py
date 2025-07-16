#!/usr/bin/env python3
"""
Simple test script to analyze the "Not Vision Ready" filter logic using direct database connection
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import re
import os

def get_db_connection():
    """Get database connection using environment variables with defaults"""
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=int(os.environ.get('DB_PORT', 5432)),
        database=os.environ.get('DB_NAME', 'dsrcircuits'),
        user=os.environ.get('DB_USER', 'dsruser'),
        password=os.environ.get('DB_PASSWORD', 'T3dC$gLp9')
    )

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
        clean_provider = re.sub(r'<[^>]+>', '', provider_str)
    
    # More specific cellular indicators - avoid broadband services
    cellular_indicators = ['VZW', 'Cell', 'Cellular', 'Wireless']
    
    # Special cases for AT&T and Verizon - only if it's specifically cellular
    if ('AT&T' in clean_provider and 'Cell' in clean_provider) or \
       ('Verizon' in clean_provider and 'Cell' in clean_provider) or \
       'VZW Cell' in clean_provider:
        return True
        
    return any(indicator in clean_provider for indicator in cellular_indicators)

def test_not_vision_ready_filter():
    """Test the Not Vision Ready filter logic"""
    
    try:
        # Create database connection
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Query all circuits with Discount-Tire tag from enriched_circuits
        query = """
            SELECT network_name as site_name, wan1_speed, wan2_speed, wan1_provider, wan2_provider, device_tags
            FROM enriched_circuits 
            WHERE 'Discount-Tire' = ANY(device_tags)
            ORDER BY network_name
        """
        
        cur.execute(query)
        circuits = cur.fetchall()
        
        print(f"Total Discount-Tire circuits: {len(circuits)}")
        
        # Show all sites first for analysis
        print(f"\n📋 All Discount-Tire circuits:")
        for i, circuit in enumerate(circuits):  # Show ALL circuits
            wan1_parsed = parse_speed(circuit['wan1_speed'])
            wan2_parsed = parse_speed(circuit['wan2_speed'])
            wan1_low = is_low_speed(wan1_parsed)
            wan2_low = is_low_speed(wan2_parsed)
            wan1_cell = is_cellular(circuit['wan1_speed']) or is_cellular_provider(circuit['wan1_provider'])
            wan2_cell = is_cellular(circuit['wan2_speed']) or is_cellular_provider(circuit['wan2_provider'])
            
            # Mark potential candidates
            candidate = ""
            if (wan1_cell and wan2_cell):
                candidate = " [CELL/CELL]"
            elif (wan1_low and wan2_cell) or (wan2_low and wan1_cell):
                candidate = " [LOW+CELL]"
            
            print(f"{i+1:2d}. {circuit['site_name']:8s} | WAN1: {circuit['wan1_speed']:20s} ({circuit['wan1_provider']:25s}) | WAN2: {circuit['wan2_speed']:20s} ({circuit['wan2_provider']:25s}){candidate}")
        print()
        
        not_vision_ready_sites = []
        
        for circuit in circuits:
            site_name = circuit['site_name']
            wan1_speed = circuit['wan1_speed'] or ''
            wan2_speed = circuit['wan2_speed'] or ''
            wan1_provider = circuit['wan1_provider'] or ''
            wan2_provider = circuit['wan2_provider'] or ''
            
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
            
            # Debug output for specific sites
            if site_name in ['MOS 07', 'ALB 03', 'FLO 13']:
                print(f"\n🔍 Debug {site_name}:")
                print(f"   WAN1 Speed: '{wan1_speed}' -> Cellular: {is_cellular(wan1_speed)}")
                print(f"   WAN1 Provider: '{wan1_provider}' -> Cellular: {is_cellular_provider(wan1_provider)}")
                print(f"   WAN1 Combined Cellular: {wan1_is_cellular}")
                print(f"   WAN1 Low Speed: {wan1_is_low_speed}")
                print(f"   WAN2 Speed: '{wan2_speed}' -> Cellular: {is_cellular(wan2_speed)}")
                print(f"   WAN2 Provider: '{wan2_provider}' -> Cellular: {is_cellular_provider(wan2_provider)}")
                print(f"   WAN2 Combined Cellular: {wan2_is_cellular}")
                print(f"   WAN2 Low Speed: {wan2_is_low_speed}")
            
            # Apply Not Vision Ready criteria:
            # 1. BOTH circuits are cellular (cell/cell), OR
            # 2. One circuit has low speed (under 100M x 10M) AND the other is cellular
            qualifies = ((wan1_is_cellular and wan2_is_cellular) or 
                        (wan1_is_low_speed and wan2_is_cellular) or 
                        (wan2_is_low_speed and wan1_is_cellular))
            
            if qualifies:
                reason = get_qualification_reason(wan1_is_cellular, wan2_is_cellular, 
                                                wan1_is_low_speed, wan2_is_low_speed)
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
                    'reason': reason
                })
        
        print(f"\n📡 Not Vision Ready sites found: {len(not_vision_ready_sites)}")
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
                cur.execute("""
                    SELECT network_name as site_name, wan1_speed, wan2_speed, wan1_provider, wan2_provider 
                    FROM enriched_circuits 
                    WHERE network_name = %s AND 'Discount-Tire' = ANY(device_tags)
                """, (site_name,))
                site_exists = cur.fetchone()
                
                if site_exists:
                    print(f"\n✗ {site_name}: EXISTS but doesn't qualify")
                    print(f"   WAN1: {site_exists['wan1_speed']} ({site_exists['wan1_provider']})")
                    print(f"   WAN2: {site_exists['wan2_speed']} ({site_exists['wan2_provider']})")
                else:
                    print(f"\n? {site_name}: NOT FOUND in Discount-Tire circuits")
        
        # Show summary by qualification reason
        print(f"\n📊 Summary by qualification reason:")
        reason_counts = {}
        for site in not_vision_ready_sites:
            reason = site['reason']
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        for reason, count in sorted(reason_counts.items()):
            print(f"   {reason}: {count} sites")
        
        cur.close()
        conn.close()
        
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