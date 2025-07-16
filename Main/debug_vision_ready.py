#!/usr/bin/env python3
"""
Debug script to check why 'Not Vision Ready' filter isn't catching cell/cell sites
"""

import sys
import os
sys.path.append('/usr/local/bin')

from flask import Flask
from config import Config
from models import db, EnrichedCircuit, MerakiInventory

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def debug_site_data(site_name):
    """Debug data for a specific site"""
    print(f"\n=== DEBUGGING {site_name} ===")
    
    with app.app_context():
        # Query enriched circuits
        enriched = db.session.query(EnrichedCircuit, MerakiInventory).join(
            MerakiInventory,
            EnrichedCircuit.network_name == MerakiInventory.network_name
        ).filter(
            EnrichedCircuit.network_name.ilike(f'%{site_name}%')
        ).first()
        
        if enriched:
            circuit, device = enriched
            print(f"Network Name: {circuit.network_name}")
            print(f"Device Tags: {device.device_tags}")
            print(f"WAN1 Provider: '{device.wan1_provider}'")
            print(f"WAN1 Speed: '{device.wan1_speed}'")
            print(f"WAN2 Provider: '{device.wan2_provider}'")
            print(f"WAN2 Speed: '{device.wan2_speed}'")
            print(f"Notes: {device.notes}")
            
            # Check if it has Discount-Tire tag
            has_discount_tire_tag = False
            if device.device_tags:
                tags = device.device_tags if isinstance(device.device_tags, list) else []
                has_discount_tire_tag = 'Discount-Tire' in tags
            print(f"Has Discount-Tire tag: {has_discount_tire_tag}")
            
            # Simulate the JavaScript filter logic
            print("\n--- FILTER LOGIC SIMULATION ---")
            
            # Parse speeds
            def parse_speed(speed_str):
                if not speed_str or speed_str in ['N/A', 'null', 'Cell', 'Satellite', 'TBD', 'Unknown']:
                    return None
                
                import re
                match = re.match(r'^([\d.]+)M\s*[xX]\s*([\d.]+)M$', speed_str.strip())
                if match:
                    return {
                        'download': float(match.group(1)),
                        'upload': float(match.group(2))
                    }
                return None
            
            def is_low_speed(speed):
                if not speed:
                    return False
                return speed['download'] < 100.0 or speed['upload'] < 10.0
            
            def is_cellular(speed_str):
                return speed_str and speed_str.strip() == 'Cell'
            
            def is_cellular_provider(provider_str):
                if not provider_str:
                    return False
                provider = provider_str.upper()
                return any(indicator in provider for indicator in ['AT&T', 'VERIZON', 'VZW', 'CELL', 'CELLULAR', 'WIRELESS'])
            
            wan1_parsed_speed = parse_speed(device.wan1_speed)
            wan2_parsed_speed = parse_speed(device.wan2_speed)
            
            print(f"WAN1 Parsed Speed: {wan1_parsed_speed}")
            print(f"WAN2 Parsed Speed: {wan2_parsed_speed}")
            
            wan1_is_low_speed = is_low_speed(wan1_parsed_speed)
            wan2_is_low_speed = is_low_speed(wan2_parsed_speed)
            wan1_is_cellular = is_cellular(device.wan1_speed) or is_cellular_provider(device.wan1_provider)
            wan2_is_cellular = is_cellular(device.wan2_speed) or is_cellular_provider(device.wan2_provider)
            
            print(f"WAN1 is low speed: {wan1_is_low_speed}")
            print(f"WAN2 is low speed: {wan2_is_low_speed}")
            print(f"WAN1 is cellular: {wan1_is_cellular}")
            print(f"WAN2 is cellular: {wan2_is_cellular}")
            
            both_cellular = wan1_is_cellular and wan2_is_cellular
            low_speed_with_cellular = (wan1_is_low_speed and wan2_is_cellular) or (wan2_is_low_speed and wan1_is_cellular)
            
            print(f"Both cellular: {both_cellular}")
            print(f"Low speed with cellular: {low_speed_with_cellular}")
            
            should_match_filter = both_cellular or low_speed_with_cellular
            print(f"SHOULD MATCH 'Not Vision Ready' FILTER: {should_match_filter}")
            
        else:
            print(f"No data found for {site_name}")

if __name__ == "__main__":
    # Debug specific sites
    sites_to_debug = ["CAS 02", "NVL 16"]
    
    for site in sites_to_debug:
        debug_site_data(site)