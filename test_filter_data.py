#!/usr/bin/env python3
"""
Test what data is being passed to the template
"""

import sys
sys.path.append('/usr/local/bin/Main')

from models import db, EnrichedCircuit, MerakiInventory
from sqlalchemy import create_engine, func
from config import Config

print("=== TESTING FILTER DATA ===\n")

try:
    # Connect to database
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    # Get a sample of enriched circuits like the test route does
    with engine.connect() as conn:
        # Get sample enriched data
        result = conn.execute("""
            SELECT ec.network_name, ec.wan1_provider, ec.wan2_provider, 
                   ec.wan1_speed, ec.wan2_speed
            FROM enriched_circuits ec
            JOIN meraki_inventory mi ON ec.network_name = mi.network_name
            WHERE ec.network_name NOT ILIKE '%hub%'
              AND ec.network_name NOT ILIKE '%lab%'
              AND ec.network_name NOT ILIKE '%voice%'
              AND ec.network_name NOT ILIKE '%test%'
              AND NOT (
                  (mi.wan1_ip IS NULL OR mi.wan1_ip = '' OR mi.wan1_ip = 'None') AND
                  (mi.wan2_ip IS NULL OR mi.wan2_ip = '' OR mi.wan2_ip = 'None')
              )
            ORDER BY ec.network_name
            LIMIT 20
        """)
        
        rows = result.fetchall()
        
        print(f"Sample data from enriched_circuits (first 20):")
        print("-" * 80)
        for row in rows:
            print(f"Site: {row.network_name}")
            print(f"  WAN1: Provider='{row.wan1_provider}', Speed='{row.wan1_speed}'")
            print(f"  WAN2: Provider='{row.wan2_provider}', Speed='{row.wan2_speed}'")
            print()
            
        # Get unique providers
        wan1_providers = conn.execute("""
            SELECT DISTINCT wan1_provider 
            FROM enriched_circuits 
            WHERE wan1_provider IS NOT NULL 
              AND wan1_provider != '' 
              AND wan1_provider != 'N/A'
            ORDER BY wan1_provider
            LIMIT 10
        """).fetchall()
        
        wan2_providers = conn.execute("""
            SELECT DISTINCT wan2_provider 
            FROM enriched_circuits 
            WHERE wan2_provider IS NOT NULL 
              AND wan2_provider != '' 
              AND wan2_provider != 'N/A'
            ORDER BY wan2_provider
            LIMIT 10
        """).fetchall()
        
        print("\nUnique WAN1 Providers (first 10):")
        for p in wan1_providers:
            print(f"  - '{p[0]}'")
            
        print("\nUnique WAN2 Providers (first 10):")
        for p in wan2_providers:
            print(f"  - '{p[0]}'")
            
        # Check for Starlink specifically
        starlink_count = conn.execute("""
            SELECT COUNT(*) 
            FROM enriched_circuits 
            WHERE wan1_provider ILIKE '%starlink%' 
               OR wan2_provider ILIKE '%starlink%'
        """).scalar()
        
        print(f"\nTotal circuits with 'Starlink' in provider: {starlink_count}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()