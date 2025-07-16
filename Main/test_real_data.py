#!/usr/bin/env python3
"""Test the Not Vision Ready filter with real database data"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
import sys
import os
sys.path.append('/usr/local/bin/Main')
try:
    from models import db
    from config import config
except ImportError as e:
    print(f"Import error: {e}")
    print("Running simple test without database connection...")
    
from sqlalchemy import text

def test_with_real_data():
    """Test the filter with actual database data to verify it's working"""
    
    # Create Flask app and database connection
    app = Flask(__name__)
    app_config = config['production']
    app.config['SQLALCHEMY_DATABASE_URI'] = app_config.SQLALCHEMY_DATABASE_URI
    db = SQLAlchemy(app)
    
    with app.app_context():
        engine = db.engine
        
        print("Testing Not Vision Ready Filter with Real Data")
        print("=" * 80)
        
        # Get a sample of sites with various speed configurations
        query = text("""
        SELECT 
            ec.network_name,
            ec.wan1_provider,
            ec.wan1_speed,
            ec.wan2_provider,
            ec.wan2_speed
        FROM enriched_circuits ec
        JOIN meraki_inventory mi ON ec.network_name = mi.network_name
        WHERE 
            'Discount-Tire' = ANY(mi.device_tags)
            AND NOT EXISTS (
                SELECT 1 FROM unnest(mi.device_tags) AS tag 
                WHERE LOWER(tag) LIKE '%hub%' 
                   OR LOWER(tag) LIKE '%lab%' 
                   OR LOWER(tag) LIKE '%voice%'
                   OR LOWER(tag) LIKE '%test%'
            )
            AND NOT (
                (mi.wan1_ip IS NULL OR mi.wan1_ip = '' OR mi.wan1_ip = 'None') AND
                (mi.wan2_ip IS NULL OR mi.wan2_ip = '' OR mi.wan2_ip = 'None')
            )
            AND (
                -- Include some examples of different scenarios
                (ec.wan1_speed = 'Cell' OR ec.wan2_speed = 'Cell') OR
                (ec.wan1_speed ~ '^[0-9.]+M\s*[xX]\s*[0-9.]+M$' AND ec.wan2_speed ~ '^[0-9.]+M\s*[xX]\s*[0-9.]+M$') OR
                (ec.wan1_provider ILIKE '%AT&T%' OR ec.wan1_provider ILIKE '%Verizon%' OR 
                 ec.wan2_provider ILIKE '%AT&T%' OR ec.wan2_provider ILIKE '%Verizon%')
            )
        ORDER BY 
            CASE WHEN ec.wan1_speed = 'Cell' OR ec.wan2_speed = 'Cell' THEN 1 ELSE 2 END,
            ec.network_name
        LIMIT 15
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query)
            rows = result.fetchall()
            
            if not rows:
                print("No test data found.")
                return
            
            print(f"\nFound {len(rows)} test sites:")
            print("-" * 100)
            print(f"{'Site':<12} {'WAN1 Provider':<20} {'WAN1 Speed':<15} {'WAN2 Provider':<20} {'WAN2 Speed':<15} {'Should Match'}")
            print("-" * 100)
            
            for row in rows:
                # Apply the filter logic to each row
                should_match = analyze_site(row.wan1_speed, row.wan1_provider, row.wan2_speed, row.wan2_provider)
                match_indicator = "✅ YES" if should_match else "❌ NO"
                
                print(f"{row.network_name:<12} {(row.wan1_provider or 'N/A')[:19]:<20} {(row.wan1_speed or 'N/A'):<15} "
                      f"{(row.wan2_provider or 'N/A')[:19]:<20} {(row.wan2_speed or 'N/A'):<15} {match_indicator}")

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

def analyze_site(wan1_speed, wan1_provider, wan2_speed, wan2_provider):
    """Apply the Not Vision Ready filter logic to a site"""
    
    # Exclude satellites
    if wan1_speed == 'Satellite' or wan2_speed == 'Satellite':
        return False
    
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
    
    return both_cellular or low_speed_with_cellular

if __name__ == "__main__":
    test_with_real_data()