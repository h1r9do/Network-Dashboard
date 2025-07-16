#!/usr/bin/env python3
"""
Analyze failures in enriched_circuits matching
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
    
    print('=== Analyzing Enriched Circuits Matching Failures ===\n')
    
    # Get enriched circuits with provider data
    cursor.execute('''
        WITH enriched_data AS (
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
            WHERE (ec.wan1_provider IS NOT NULL OR ec.wan2_provider IS NOT NULL)
                AND ec.device_tags IS NOT NULL
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
            e.*,
            c.circuits,
            c.primary_providers,
            c.secondary_providers,
            c.circuit_count,
            CASE 
                WHEN c.circuit_count IS NULL THEN 'No circuits'
                ELSE 'Has circuits'
            END as status
        FROM enriched_data e
        LEFT JOIN circuit_data c ON e.network_name = c.site_name
        WHERE 'Discount-Tire' = ANY(e.device_tags)
            AND NOT EXISTS (
                SELECT 1 FROM unnest(e.device_tags) AS tag 
                WHERE LOWER(tag) LIKE '%hub%' 
                   OR LOWER(tag) LIKE '%lab%' 
                   OR LOWER(tag) LIKE '%voice%'
                   OR LOWER(tag) LIKE '%test%'
            )
        ORDER BY e.network_name
    ''')
    
    sites = cursor.fetchall()
    print(f'Found {len(sites)} Discount-Tire sites with provider data\n')
    
    # Analyze failures
    no_circuits = []
    provider_mismatches = []
    provider_counter = Counter()
    mismatch_patterns = defaultdict(list)
    
    for site in sites:
        if site['status'] == 'No circuits':
            no_circuits.append(site)
            # Count providers
            if site['wan1_provider'] and site['wan1_speed'] and site['wan1_speed'].lower() not in ['cell', 'satellite']:
                provider_counter[site['wan1_provider']] += 1
            if site['wan2_provider'] and site['wan2_speed'] and site['wan2_speed'].lower() not in ['cell', 'satellite']:
                provider_counter[site['wan2_provider']] += 1
        else:
            # Check for mismatches
            wan1_mismatch = False
            wan2_mismatch = False
            
            # Check WAN1
            if (site['wan1_provider'] and site['wan1_speed'] and 
                site['wan1_speed'].lower() not in ['cell', 'satellite'] and
                site['primary_providers']):
                
                primary_providers = [p for p in site['primary_providers'] if p]
                if primary_providers:
                    found_match = False
                    for pp in primary_providers:
                        score = max(
                            fuzz.ratio(site['wan1_provider'].lower(), pp.lower()),
                            fuzz.partial_ratio(site['wan1_provider'].lower(), pp.lower())
                        )
                        if score >= 80:
                            found_match = True
                            break
                    
                    if not found_match:
                        wan1_mismatch = True
                        mismatch_patterns[site['wan1_provider']].append({
                            'site': site['network_name'],
                            'wan': 'WAN1',
                            'circuits': primary_providers
                        })
            
            # Check WAN2
            if (site['wan2_provider'] and site['wan2_speed'] and 
                site['wan2_speed'].lower() not in ['cell', 'satellite'] and
                site['secondary_providers']):
                
                secondary_providers = [p for p in site['secondary_providers'] if p]
                if secondary_providers:
                    found_match = False
                    for sp in secondary_providers:
                        score = max(
                            fuzz.ratio(site['wan2_provider'].lower(), sp.lower()),
                            fuzz.partial_ratio(site['wan2_provider'].lower(), sp.lower())
                        )
                        if score >= 80:
                            found_match = True
                            break
                    
                    if not found_match:
                        wan2_mismatch = True
                        mismatch_patterns[site['wan2_provider']].append({
                            'site': site['network_name'],
                            'wan': 'WAN2',
                            'circuits': secondary_providers
                        })
            
            if wan1_mismatch or wan2_mismatch:
                provider_mismatches.append(site)
    
    print(f'Sites with no circuits: {len(no_circuits)}')
    print(f'Sites with provider mismatches: {len(provider_mismatches)}\n')
    
    # Show top providers without circuits
    print('=== Top Providers Without Circuits ===\n')
    print(f"{'Provider':<40} {'Count':<6} {'Fuzzy Match Opportunities'}")
    print('-' * 80)
    
    # Get all circuit providers for fuzzy matching
    cursor.execute('SELECT DISTINCT provider_name FROM circuits WHERE status = \'Enabled\'')
    all_circuit_providers = [row['provider_name'] for row in cursor.fetchall()]
    
    fuzzy_recommendations = []
    
    for provider, count in provider_counter.most_common(20):
        # Check fuzzy matches
        best_matches = []
        for cp in all_circuit_providers:
            score = max(
                fuzz.ratio(provider.lower(), cp.lower()),
                fuzz.partial_ratio(provider.lower(), cp.lower()),
                fuzz.token_sort_ratio(provider.lower(), cp.lower())
            )
            if score >= 70:
                best_matches.append((cp, score))
        
        best_matches.sort(key=lambda x: -x[1])
        match_str = ', '.join([f"{m[0]} ({m[1]}%)" for m in best_matches[:2]])
        
        print(f'{provider:<40} {count:<6} {match_str}')
        
        if best_matches and best_matches[0][1] >= 70:
            fuzzy_recommendations.append((provider, best_matches[0][0], best_matches[0][1], count))
    
    # Show mismatch patterns
    print('\n\n=== Provider Mismatch Patterns ===\n')
    
    mismatch_summary = []
    for provider, mismatches in sorted(mismatch_patterns.items(), key=lambda x: -len(x[1]))[:15]:
        print(f"\n'{provider}' ({len(mismatches)} mismatches):")
        
        # Count circuit patterns
        circuit_counter = Counter()
        for m in mismatches:
            for circuit in m['circuits']:
                if circuit:
                    circuit_counter[circuit] += 1
        
        for circuit, count in circuit_counter.most_common(3):
            print(f"  → Available circuit: '{circuit}' ({count} sites)")
            
            # Calculate fuzzy score
            score = max(
                fuzz.ratio(provider.lower(), circuit.lower()),
                fuzz.partial_ratio(provider.lower(), circuit.lower())
            )
            
            if score >= 70:
                mismatch_summary.append((provider, circuit, score, count))
    
    # Final recommendations
    print('\n\n=== RECOMMENDED ACTIONS ===\n')
    
    print('1. Provider Mappings (for sites without circuits):')
    for provider, circuit_provider, score, count in fuzzy_recommendations[:10]:
        if score >= 80:
            print(f"   Map '{provider}' → '{circuit_provider}' (score: {score}%, affects {count} sites)")
    
    print('\n2. Provider Mappings (for mismatches):')
    for provider, circuit, score, count in sorted(mismatch_summary, key=lambda x: (-x[3], -x[2]))[:10]:
        if score >= 70 and count >= 2:
            print(f"   Map '{provider}' → '{circuit}' (score: {score}%, affects {count} sites)")
    
    # Export detailed analysis
    print('\n\n=== Exporting Detailed Analysis ===')
    
    with open('/usr/local/bin/Main/enriched_failures_analysis.csv', 'w') as f:
        f.write('Site,Issue Type,WAN,Device Notes Provider,ARIN Provider,Speed,Available Circuits,Recommendation\n')
        
        # No circuit sites
        for site in no_circuits:
            if site['wan1_provider'] and site['wan1_speed'] and site['wan1_speed'].lower() not in ['cell', 'satellite']:
                f.write(f'"{site["network_name"]}","No circuits","WAN1","{site["wan1_provider"]}",')
                f.write(f'"{site["wan1_arin_org"] or ""}","{site["wan1_speed"]}","None","Create circuit"\n')
            
            if site['wan2_provider'] and site['wan2_speed'] and site['wan2_speed'].lower() not in ['cell', 'satellite']:
                f.write(f'"{site["network_name"]}","No circuits","WAN2","{site["wan2_provider"]}",')
                f.write(f'"{site["wan2_arin_org"] or ""}","{site["wan2_speed"]}","None","Create circuit"\n')
        
        # Mismatch sites
        for provider, mismatches in mismatch_patterns.items():
            for m in mismatches:
                circuits_str = ', '.join([c for c in m['circuits'] if c])
                f.write(f'"{m["site"]}","Provider mismatch","{m["wan"]}","{provider}",')
                f.write(f'"","","{circuits_str}","Fuzzy match or mapping needed"\n')
    
    print('✓ Exported to enriched_failures_analysis.csv')
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()