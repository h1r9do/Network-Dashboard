#!/usr/bin/env python3
"""
Debug provider matching for ALM 01
"""

import sys
sys.path.insert(0, '.')
from config import Config
from sqlalchemy import create_engine, text

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

def main():
    with engine.connect() as conn:
        # Get ALM 01 data
        site_name = "ALM 01"
        
        # Get enriched circuit data
        result = conn.execute(text('''
            SELECT wan1_provider, wan2_provider
            FROM enriched_circuits
            WHERE LOWER(network_name) = LOWER(:site)
        '''), {'site': site_name})
        
        enriched = result.fetchone()
        if enriched:
            print(f"Enriched WAN1: '{enriched[0]}'")
            print(f"Enriched WAN2: '{enriched[1]}'")
        
        # Get DSR circuits
        result = conn.execute(text('''
            SELECT circuit_purpose, provider_name, billing_monthly_cost
            FROM circuits
            WHERE LOWER(site_name) = LOWER(:site)
            AND status = 'Enabled'
            ORDER BY circuit_purpose
        '''), {'site': site_name})
        
        print("\nDSR Circuits:")
        for row in result:
            purpose, provider, cost = row
            print(f"  {purpose}: '{provider}' - ${cost}")
            
            if enriched and enriched[0]:  # WAN1 provider exists
                # Test matching logic
                dsr_provider = (provider or '').upper().strip()
                wan1_provider = (enriched[0] or '').upper().strip()
                
                print(f"    DSR normalized: '{dsr_provider}'")
                print(f"    WAN1 normalized: '{wan1_provider}'")
                
                # Test the exact conditions from dsrcircuits.py
                match1 = dsr_provider in wan1_provider
                match2 = wan1_provider in dsr_provider
                match3 = ('SPECTRUM' in dsr_provider and ('CHARTER' in wan1_provider or 'SPECTRUM' in wan1_provider))
                match4 = ('CHARTER' in dsr_provider and ('SPECTRUM' in wan1_provider or 'CHARTER' in wan1_provider))
                
                print(f"    Match tests:")
                print(f"      DSR in WAN1: {match1}")
                print(f"      WAN1 in DSR: {match2}")
                print(f"      Spectrum->Charter: {match3}")
                print(f"      Charter->Spectrum: {match4}")
                print(f"      Overall match: {match1 or match2 or match3 or match4}")
                
                if match1 or match2 or match3 or match4:
                    print(f"    ✅ SHOULD MATCH - Cost: ${cost}")
                else:
                    print(f"    ❌ NO MATCH")

if __name__ == "__main__":
    main()