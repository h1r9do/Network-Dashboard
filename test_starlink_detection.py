#!/usr/bin/env python3
"""
Test Starlink detection logic by checking for SpaceX ARIN providers
"""

import sys
sys.path.append('/usr/local/bin/Main')

from models import db, MerakiInventory
from sqlalchemy import create_engine
from config import get_config

print("=== TESTING STARLINK/SPACEX DETECTION ===\n")

try:
    # Get database config
    config = get_config()
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
    
    # Query for circuits with SpaceX ARIN providers
    with engine.connect() as conn:
        # Check WAN1 ARIN providers
        wan1_spacex = conn.execute("""
            SELECT network_name, wan1_arin_provider, wan1_provider_label, wan1_speed
            FROM meraki_inventory 
            WHERE wan1_arin_provider ILIKE '%spacex%' 
               OR wan1_arin_provider ILIKE '%starlink%'
            ORDER BY network_name
        """).fetchall()
        
        # Check WAN2 ARIN providers  
        wan2_spacex = conn.execute("""
            SELECT network_name, wan2_arin_provider, wan2_provider_label, wan2_speed
            FROM meraki_inventory 
            WHERE wan2_arin_provider ILIKE '%spacex%'
               OR wan2_arin_provider ILIKE '%starlink%' 
            ORDER BY network_name
        """).fetchall()
        
        # Check for circuits with "cell" in speed
        cellular_circuits = conn.execute("""
            SELECT network_name, wan1_speed, wan2_speed, wan1_arin_provider, wan2_arin_provider
            FROM meraki_inventory 
            WHERE wan1_speed ILIKE '%cell%' 
               OR wan2_speed ILIKE '%cell%'
            ORDER BY network_name
            LIMIT 20
        """).fetchall()
        
        print(f"🛰️ Found {len(wan1_spacex)} WAN1 circuits with SpaceX/Starlink ARIN provider:")
        for row in wan1_spacex:
            print(f"  - {row.network_name}: ARIN='{row.wan1_arin_provider}', Provider='{row.wan1_provider_label}', Speed='{row.wan1_speed}'")
            
        print(f"\n🛰️ Found {len(wan2_spacex)} WAN2 circuits with SpaceX/Starlink ARIN provider:")
        for row in wan2_spacex:
            print(f"  - {row.network_name}: ARIN='{row.wan2_arin_provider}', Provider='{row.wan2_provider_label}', Speed='{row.wan2_speed}'")
            
        print(f"\n📶 Found {len(cellular_circuits)} circuits with 'cell' in speed (first 20):")
        for row in cellular_circuits:
            print(f"  - {row.network_name}: WAN1 Speed='{row.wan1_speed}', WAN2 Speed='{row.wan2_speed}'")
            print(f"    WAN1 ARIN='{row.wan1_arin_provider}', WAN2 ARIN='{row.wan2_arin_provider}'")

except Exception as e:
    print(f"❌ Error: {e}")

print(f"\nTotal Starlink circuits that should show badges: {len(wan1_spacex) + len(wan2_spacex)}")
print("If these exist but badges aren't showing, there may be a logic issue.")