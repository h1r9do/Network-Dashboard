#!/usr/bin/env python3
"""
Comprehensive analysis of ALL circuit matching failures
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
    
    print('=== Comprehensive Circuit Matching Failure Analysis ===\n')
    
    # Get ALL enriched circuits with provider data
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
        ),
        circuit_data AS (
            SELECT 
                site_name,
                array_agg(provider_name || ' (' || circuit_purpose || ')' ORDER BY circuit_purpose) as circuits,
                array_agg(DISTINCT provider_name) as all_providers,
                COUNT(*) as circuit_count
            FROM circuits
            WHERE status = 'Enabled'
            GROUP BY site_name
        )
        SELECT 
            e.*,
            c.circuits,
            c.all_providers,
            c.circuit_count,
            CASE 
                WHEN c.circuit_count IS NULL THEN 'No circuits'
                ELSE 'Has circuits'
            END as status
        FROM enriched_data e
        LEFT JOIN circuit_data c ON e.network_name = c.site_name
        ORDER BY status, e.network_name
    ''')
    
    all_sites = cursor.fetchall()
    print(f'Total sites with provider data: {len(all_sites)}\n')
    
    # Categorize sites
    no_circuits = []
    has_circuits = []
    provider_counter = Counter()
    provider_failure_details = defaultdict(list)
    
    for site in all_sites:
        if site['status'] == 'No circuits':
            no_circuits.append(site)
            # Count providers that have no circuits
            if site['wan1_provider'] and site['wan1_speed'] and site['wan1_speed'].lower() not in ['cell', 'satellite']:
                provider_counter[site['wan1_provider']] += 1
                provider_failure_details[site['wan1_provider']].append({
                    'site': site['network_name'],
                    'wan': 'WAN1',
                    'speed': site['wan1_speed'],
                    'arin': site['wan1_arin_org']
                })
            
            if site['wan2_provider'] and site['wan2_speed'] and site['wan2_speed'].lower() not in ['cell', 'satellite']:
                provider_counter[site['wan2_provider']] += 1
                provider_failure_details[site['wan2_provider']].append({
                    'site': site['network_name'],
                    'wan': 'WAN2', 
                    'speed': site['wan2_speed'],
                    'arin': site['wan2_arin_org']
                })
        else:
            has_circuits.append(site)
    
    print(f'Sites with NO circuits: {len(no_circuits)} ({len(no_circuits)/len(all_sites)*100:.1f}%)')
    print(f'Sites with circuits: {len(has_circuits)} ({len(has_circuits)/len(all_sites)*100:.1f}%)\n')
    
    # Get all circuit providers for fuzzy matching
    cursor.execute('SELECT DISTINCT provider_name FROM circuits WHERE status = \'Enabled\' ORDER BY provider_name')
    all_circuit_providers = [row['provider_name'] for row in cursor.fetchall()]
    
    # Analyze top providers without circuits
    print('=== Top 30 Providers Without ANY Circuits ===\n')
    print(f"{'#':<3} {'Provider':<40} {'Count':<6} {'Best Fuzzy Match'}")
    print('-' * 90)
    
    fuzzy_mapping_recommendations = []
    
    for idx, (provider, count) in enumerate(provider_counter.most_common(30), 1):
        # Find best fuzzy matches
        best_matches = []
        for cp in all_circuit_providers:
            # Try multiple fuzzy algorithms
            scores = [
                fuzz.ratio(provider.lower(), cp.lower()),
                fuzz.partial_ratio(provider.lower(), cp.lower()),
                fuzz.token_sort_ratio(provider.lower(), cp.lower()),
                fuzz.token_set_ratio(provider.lower(), cp.lower())
            ]
            max_score = max(scores)
            
            if max_score >= 60:
                best_matches.append((cp, max_score))
        
        best_matches.sort(key=lambda x: -x[1])
        
        if best_matches and best_matches[0][1] >= 70:
            match_str = f"{best_matches[0][0]} ({best_matches[0][1]}%)"
            fuzzy_mapping_recommendations.append({
                'device_provider': provider,
                'circuit_provider': best_matches[0][0],
                'score': best_matches[0][1],
                'count': count
            })
        else:
            match_str = "No good match" if not best_matches else f"{best_matches[0][0]} ({best_matches[0][1]}%)"
        
        print(f'{idx:<3} {provider:<40} {count:<6} {match_str}')
    
    # Show specific examples for top failures
    print('\n\n=== Examples of Top Provider Failures ===')
    
    for provider, count in provider_counter.most_common(5):
        print(f"\n'{provider}' ({count} failures):")
        examples = provider_failure_details[provider][:5]
        for ex in examples:
            arin_str = f" (ARIN: {ex['arin']})" if ex['arin'] else ""
            print(f"  - {ex['site']} {ex['wan']}: {ex['speed']}{arin_str}")
    
    # Analyze patterns in providers
    print('\n\n=== Provider Pattern Analysis ===')
    
    # Group by common patterns
    pattern_groups = defaultdict(list)
    
    for provider in provider_counter.keys():
        # Check for common patterns
        if 'frontier' in provider.lower():
            pattern_groups['Frontier variants'].append(provider)
        elif 'comcast' in provider.lower():
            pattern_groups['Comcast variants'].append(provider)
        elif 'at&t' in provider.lower() or 'att' in provider.lower():
            pattern_groups['AT&T variants'].append(provider)
        elif 'centurylink' in provider.lower() or 'lumen' in provider.lower():
            pattern_groups['CenturyLink/Lumen variants'].append(provider)
        elif 'spectrum' in provider.lower() or 'charter' in provider.lower():
            pattern_groups['Spectrum/Charter variants'].append(provider)
        elif 'cox' in provider.lower():
            pattern_groups['Cox variants'].append(provider)
    
    for pattern, providers in sorted(pattern_groups.items()):
        if len(providers) > 1:
            print(f"\n{pattern}:")
            total_count = sum(provider_counter[p] for p in providers)
            print(f"  Total failures: {total_count}")
            for p in sorted(providers)[:10]:
                print(f"  - '{p}' ({provider_counter[p]} sites)")
    
    # Final recommendations
    print('\n\n=== FUZZY MATCHING RECOMMENDATIONS ===\n')
    print('Based on the analysis, these provider mappings would resolve many failures:\n')
    
    # Sort by impact (count * score)
    fuzzy_mapping_recommendations.sort(key=lambda x: x['count'] * x['score'] / 100, reverse=True)
    
    for idx, rec in enumerate(fuzzy_mapping_recommendations[:20], 1):
        print(f"{idx}. Map '{rec['device_provider']}' → '{rec['circuit_provider']}'")
        print(f"   Score: {rec['score']}%, Affects: {rec['count']} sites")
    
    # Export detailed failure list
    print('\n\n=== Exporting Detailed Analysis ===')
    
    with open('/usr/local/bin/Main/all_circuit_failures_analysis.csv', 'w') as f:
        f.write('Site,WAN,Device Provider,ARIN Provider,Speed,Fuzzy Match,Score,Impact\n')
        
        for provider, details in provider_failure_details.items():
            # Find best fuzzy match
            best_match = None
            best_score = 0
            
            for cp in all_circuit_providers:
                score = max(
                    fuzz.ratio(provider.lower(), cp.lower()),
                    fuzz.partial_ratio(provider.lower(), cp.lower()),
                    fuzz.token_sort_ratio(provider.lower(), cp.lower())
                )
                if score > best_score:
                    best_score = score
                    best_match = cp
            
            for detail in details:
                f.write(f'"{detail["site"]}","{detail["wan"]}","{provider}",')
                f.write(f'"{detail["arin"] or ""}","{detail["speed"]}",')
                f.write(f'"{best_match or "None"}",{best_score},{len(details)}\n')
    
    print('✓ Exported to all_circuit_failures_analysis.csv')
    
    # Summary statistics
    print(f'\n=== Summary Statistics ===')
    print(f'Total sites analyzed: {len(all_sites)}')
    print(f'Sites without circuits: {len(no_circuits)}')
    print(f'Unique providers without circuits: {len(provider_counter)}')
    print(f'Total provider instances without circuits: {sum(provider_counter.values())}')
    print(f'Providers with 70%+ fuzzy matches: {len(fuzzy_mapping_recommendations)}')
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()