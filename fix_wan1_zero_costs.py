#!/usr/bin/env python3
"""
Fix WAN1 zero costs by properly matching providers
"""

import sys
sys.path.insert(0, '.')
from config import Config
from sqlalchemy import create_engine, text
from datetime import datetime

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

# Provider name mappings for matching
PROVIDER_MAPPINGS = {
    'CHARTER COMMUNICATIONS': ['SPECTRUM', 'CHARTER'],
    'SPECTRUM': ['CHARTER COMMUNICATIONS', 'CHARTER'],
    'COX COMMUNICATIONS': ['COX BUSINESS', 'COX BUSINESS/BOI', 'COX'],
    'COX BUSINESS': ['COX COMMUNICATIONS', 'COX'],
    'COMCAST': ['COMCAST WORKPLACE', 'COMCAST BUSINESS'],
    'COMCAST WORKPLACE': ['COMCAST'],
    'AT&T': ['AT&T BROADBAND', 'ATT', 'AT&T ENTERPRISES'],
    'CENTURYLINK': ['CENTURY LINK', 'CENTURYLINK/QWEST', 'QWEST', 'LUMEN'],
    'VERIZON': ['VERIZON BUSINESS', 'VERIZON FIOS'],
    'FRONTIER': ['FRONTIER COMMUNICATIONS', 'FRONTIER FIOS'],
    'OPTIMUM': ['ALTICE', 'ALTICE WEST'],
    'WINDSTREAM': ['WINDSTREAM COMMUNICATIONS'],
}

def normalize_provider(provider):
    """Normalize provider name for comparison"""
    if not provider:
        return ''
    return provider.upper().strip().replace('-', ' ').replace('  ', ' ')

def providers_match(prov1, prov2):
    """Check if two providers match"""
    norm1 = normalize_provider(prov1)
    norm2 = normalize_provider(prov2)
    
    # Exact match
    if norm1 == norm2:
        return True
    
    # Substring match
    if norm1 in norm2 or norm2 in norm1:
        return True
    
    # Check mappings
    for key, values in PROVIDER_MAPPINGS.items():
        if norm1 == key:
            for val in values:
                if val in norm2:
                    return True
        if norm2 == key:
            for val in values:
                if val in norm1:
                    return True
    
    return False

def main():
    with engine.connect() as conn:
        # Get sites with WAN1 $0 cost
        result = conn.execute(text('''
            SELECT DISTINCT ec.network_name, ec.wan1_provider
            FROM enriched_circuits ec
            WHERE ec.wan1_provider NOT LIKE '%Cell%'
            AND ec.wan1_provider NOT LIKE '%Starlink%'
            AND ec.wan1_provider != ''
            AND ec.wan1_provider IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM circuits c
                WHERE LOWER(c.site_name) = LOWER(ec.network_name)
                AND c.status = 'Enabled'
                AND c.billing_monthly_cost > 0
                AND UPPER(c.provider_name) LIKE '%' || UPPER(SUBSTR(ec.wan1_provider, 1, 5)) || '%'
            )
            ORDER BY ec.network_name
            LIMIT 10
        '''))
        
        sites = result.fetchall()
        print(f"Processing {len(sites)} sites with WAN1 $0.00 cost...\n")
        
        fixed_count = 0
        
        for site_name, wan1_provider in sites:
            # Find matching circuit with proper provider matching
            circuit_result = conn.execute(text('''
                SELECT id, provider_name, billing_monthly_cost
                FROM circuits
                WHERE LOWER(site_name) = LOWER(:site)
                AND status = 'Enabled'
                AND billing_monthly_cost > 0
            '''), {'site': site_name})
            
            matched = False
            for circuit_id, dsr_provider, cost in circuit_result:
                if providers_match(wan1_provider, dsr_provider):
                    print(f"{site_name}: Matched '{wan1_provider}' to '{dsr_provider}' - ${cost}")
                    matched = True
                    fixed_count += 1
                    break
            
            if not matched:
                # Check if there's any enabled circuit with cost
                any_cost = conn.execute(text('''
                    SELECT provider_name, billing_monthly_cost
                    FROM circuits
                    WHERE LOWER(site_name) = LOWER(:site)
                    AND status = 'Enabled'
                    AND billing_monthly_cost > 0
                    LIMIT 1
                '''), {'site': site_name}).fetchone()
                
                if any_cost:
                    print(f"{site_name}: No match for '{wan1_provider}', but found {any_cost[0]} with ${any_cost[1]}")
                else:
                    print(f"{site_name}: No circuits with cost found")
        
        print(f"\nFound cost matches for {fixed_count} out of {len(sites)} sites")
        print("\nNote: The issue is provider name matching in dsrcircuits.py")
        print("Need to update the matching logic to handle these variations")

if __name__ == "__main__":
    main()