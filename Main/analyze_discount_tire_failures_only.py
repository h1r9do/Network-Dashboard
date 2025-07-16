#!/usr/bin/env python3
"""
Analyze ONLY Discount-Tire site circuit matching failures
"""

import sys
import os
sys.path.append('/usr/local/bin/Main')

import psycopg2
import psycopg2.extras
import re
from collections import Counter, defaultdict
from thefuzz import fuzz

def get_db_connection():
    """Get database connection"""
    with open('/usr/local/bin/Main/config.py', 'r') as f:
        config_content = f.read()
    
    uri_match = re.search(r"SQLALCHEMY_DATABASE_URI = ['\"](.+?)['\"]", config_content)
    if not uri_match:
        raise ValueError("Could not find database URI in config")
    
    db_uri = uri_match.group(1)
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', db_uri)
    if not match:
        raise ValueError("Invalid database URI format")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )

def main():
    """Main analysis"""
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print('=== Discount-Tire Sites ONLY - Circuit Matching Analysis ===\n')
    
    # Get ONLY Discount-Tire sites
    cursor.execute('''
        WITH discount_tire_sites AS (
            SELECT 
                ec.network_name,
                ec.wan1_provider,
                ec.wan1_speed,
                ec.wan1_arin_org,
                ec.wan2_provider,
                ec.wan2_speed,
                ec.wan2_arin_org,
                ec.device_tags
            FROM enriched_circuits ec
            WHERE 'Discount-Tire' = ANY(ec.device_tags)
                AND NOT EXISTS (
                    SELECT 1 FROM unnest(ec.device_tags) AS tag 
                    WHERE LOWER(tag) LIKE '%hub%' 
                       OR LOWER(tag) LIKE '%lab%' 
                       OR LOWER(tag) LIKE '%voice%'
                       OR LOWER(tag) LIKE '%test%'
                )
                AND (ec.wan1_provider IS NOT NULL OR ec.wan2_provider IS NOT NULL)
        ),
        circuit_data AS (
            SELECT 
                site_name,
                array_agg(provider_name || ' (' || circuit_purpose || ')' ORDER BY circuit_purpose) as circuits,
                array_agg(CASE WHEN circuit_purpose = 'Primary' THEN provider_name END) as primary_providers,
                array_agg(CASE WHEN circuit_purpose = 'Secondary' THEN provider_name END) as secondary_providers,
                COUNT(*) as circuit_count
            FROM circuits
            WHERE status = 'Enabled'
            GROUP BY site_name
        )
        SELECT 
            dts.*,
            cd.circuits,
            cd.primary_providers,
            cd.secondary_providers,
            cd.circuit_count,
            CASE 
                WHEN cd.circuit_count IS NULL THEN 'No circuits'
                ELSE 'Has circuits'
            END as status
        FROM discount_tire_sites dts
        LEFT JOIN circuit_data cd ON dts.network_name = cd.site_name
        ORDER BY dts.network_name
    ''')
    
    dt_sites = cursor.fetchall()
    print(f'Total Discount-Tire sites with provider data: {len(dt_sites)}\n')
    
    # Analyze failures
    no_circuits = []
    wan1_failures = []
    wan2_failures = []
    provider_counter = Counter()
    
    for site in dt_sites:
        if site['status'] == 'No circuits':
            no_circuits.append(site)
            # Count providers
            if site['wan1_provider'] and site['wan1_speed'] and site['wan1_speed'].lower() not in ['cell', 'satellite']:
                provider_counter[site['wan1_provider']] += 1
            if site['wan2_provider'] and site['wan2_speed'] and site['wan2_speed'].lower() not in ['cell', 'satellite']:
                provider_counter[site['wan2_provider']] += 1
        else:
            # Check for matching failures even with circuits
            # WAN1 check
            if (site['wan1_provider'] and site['wan1_speed'] and 
                site['wan1_speed'].lower() not in ['cell', 'satellite']):
                
                wan1_matched = False
                if site['primary_providers']:
                    for pp in site['primary_providers']:
                        if pp:
                            score = max(
                                fuzz.ratio(site['wan1_provider'].lower(), pp.lower()),
                                fuzz.partial_ratio(site['wan1_provider'].lower(), pp.lower())
                            )
                            if score >= 70:
                                wan1_matched = True
                                break
                
                if not wan1_matched:
                    wan1_failures.append({
                        'site': site['network_name'],
                        'provider': site['wan1_provider'],
                        'speed': site['wan1_speed'],
                        'arin': site['wan1_arin_org'],
                        'available_circuits': site['circuits']
                    })
                    provider_counter[site['wan1_provider']] += 1
            
            # WAN2 check
            if (site['wan2_provider'] and site['wan2_speed'] and 
                site['wan2_speed'].lower() not in ['cell', 'satellite']):
                
                wan2_matched = False
                if site['secondary_providers']:
                    for sp in site['secondary_providers']:
                        if sp:
                            score = max(
                                fuzz.ratio(site['wan2_provider'].lower(), sp.lower()),
                                fuzz.partial_ratio(site['wan2_provider'].lower(), sp.lower())
                            )
                            if score >= 70:
                                wan2_matched = True
                                break
                
                if not wan2_matched:
                    wan2_failures.append({
                        'site': site['network_name'],
                        'provider': site['wan2_provider'],
                        'speed': site['wan2_speed'],
                        'arin': site['wan2_arin_org'],
                        'available_circuits': site['circuits']
                    })
                    provider_counter[site['wan2_provider']] += 1
    
    print(f'=== Discount-Tire Failure Summary ===')
    print(f'Sites with NO circuits: {len(no_circuits)}')
    print(f'Sites with WAN1 matching failures: {len(wan1_failures)}')
    print(f'Sites with WAN2 matching failures: {len(wan2_failures)}')
    print(f'Total provider instances failing: {sum(provider_counter.values())}\n')
    
    if no_circuits:
        print('=== Discount-Tire Sites with NO Circuits ===\n')
        for site in no_circuits:
            print(f"{site['network_name']}:")
            if site['wan1_provider']:
                print(f"  WAN1: {site['wan1_provider']} ({site['wan1_speed']})")
            if site['wan2_provider']:
                print(f"  WAN2: {site['wan2_provider']} ({site['wan2_speed']})")
        print()
    
    # Get all circuit providers for fuzzy matching
    cursor.execute('SELECT DISTINCT provider_name FROM circuits WHERE status = \'Enabled\'')
    all_circuit_providers = [row['provider_name'] for row in cursor.fetchall()]
    
    if provider_counter:
        print('=== Provider Failure Analysis (Discount-Tire Only) ===\n')
        print(f"{'Provider':<40} {'Failures':<8} {'Best Fuzzy Match'}")
        print('-' * 80)
        
        fuzzy_recommendations = []
        
        for provider, count in provider_counter.most_common():
            # Find best fuzzy match
            best_matches = []
            for cp in all_circuit_providers:
                score = max(
                    fuzz.ratio(provider.lower(), cp.lower()),
                    fuzz.partial_ratio(provider.lower(), cp.lower()),
                    fuzz.token_sort_ratio(provider.lower(), cp.lower())
                )
                if score >= 60:
                    best_matches.append((cp, score))
            
            best_matches.sort(key=lambda x: -x[1])
            
            if best_matches:
                match_str = f"{best_matches[0][0]} ({best_matches[0][1]}%)"
                if best_matches[0][1] >= 70:
                    fuzzy_recommendations.append({
                        'provider': provider,
                        'match': best_matches[0][0],
                        'score': best_matches[0][1],
                        'count': count
                    })
            else:
                match_str = "No good match"
            
            print(f"{provider:<40} {count:<8} {match_str}")
    
    # Show specific examples
    if wan1_failures or wan2_failures:
        print('\n\n=== Specific Failure Examples ===')
        
        if wan1_failures:
            print('\nWAN1 Failures:')
            for fail in wan1_failures[:5]:
                print(f"\n{fail['site']}:")
                print(f"  Device notes: {fail['provider']} ({fail['speed']})")
                print(f"  ARIN: {fail['arin'] or 'None'}")
                print(f"  Available circuits: {fail['available_circuits']}")
        
        if wan2_failures:
            print('\nWAN2 Failures:')
            for fail in wan2_failures[:5]:
                print(f"\n{fail['site']}:")
                print(f"  Device notes: {fail['provider']} ({fail['speed']})")
                print(f"  ARIN: {fail['arin'] or 'None'}")
                print(f"  Available circuits: {fail['available_circuits']}")
    
    if fuzzy_recommendations:
        print('\n\n=== Fuzzy Matching Recommendations ===')
        print('\nThese mappings would resolve Discount-Tire failures:\n')
        
        for rec in sorted(fuzzy_recommendations, key=lambda x: -x['count']):
            print(f"Map '{rec['provider']}' → '{rec['match']}'")
            print(f"  Score: {rec['score']}%, Affects: {rec['count']} instances")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()