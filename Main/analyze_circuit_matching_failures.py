#!/usr/bin/env python3
"""
Analyze circuit matching failures
"""

import sys
import os
sys.path.append('/usr/local/bin/Main')

import psycopg2
import psycopg2.extras
import re
from collections import Counter
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
    
    print('=== Analyzing Circuit Matching Failures ===\n')
    
    # First, let's see what data we have in meraki_mx_uplink_data
    cursor.execute('''
        WITH uplink_sites AS (
            SELECT DISTINCT
                mu.network_name,
                mu.wan1_provider,
                mu.wan1_speed,
                mu.wan2_provider,
                mu.wan2_speed,
                mu.device_notes
            FROM meraki_mx_uplink_data mu
            WHERE mu.wan1_provider IS NOT NULL OR mu.wan2_provider IS NOT NULL
        ),
        circuit_data AS (
            SELECT 
                site_name,
                string_agg(provider_name || ' (' || circuit_purpose || ')', ', ' ORDER BY circuit_purpose) as circuits,
                COUNT(*) as circuit_count
            FROM circuits
            WHERE status = 'Enabled'
            GROUP BY site_name
        )
        SELECT 
            u.*,
            c.circuits,
            c.circuit_count,
            CASE 
                WHEN c.circuit_count IS NULL THEN 'No circuits'
                WHEN c.circuit_count > 0 THEN 'Has circuits'
            END as status
        FROM uplink_sites u
        LEFT JOIN circuit_data c ON u.network_name = c.site_name
        ORDER BY status DESC, u.network_name
    ''')
    
    all_sites = cursor.fetchall()
    print(f'Total sites with uplink data: {len(all_sites)}\n')
    
    # Categorize failures
    no_circuits = []
    potential_mismatches = []
    provider_counter = Counter()
    
    for site in all_sites:
        if site['status'] == 'No circuits':
            no_circuits.append(site)
            # Count providers
            if site['wan1_provider']:
                provider_counter[site['wan1_provider']] += 1
            if site['wan2_provider']:
                provider_counter[site['wan2_provider']] += 1
        elif site['circuits']:
            # Check for potential mismatches
            circuits_lower = site['circuits'].lower()
            
            wan1_needs_match = (site['wan1_provider'] and 
                               site['wan1_speed'] and 
                               site['wan1_speed'].lower() not in ['cell', 'satellite'])
            wan2_needs_match = (site['wan2_provider'] and 
                               site['wan2_speed'] and 
                               site['wan2_speed'].lower() not in ['cell', 'satellite'])
            
            if wan1_needs_match or wan2_needs_match:
                # Simple check if provider appears in circuits
                wan1_found = site['wan1_provider'] and any(
                    p in site['wan1_provider'].lower() for p in circuits_lower.split(', ')
                )
                wan2_found = site['wan2_provider'] and any(
                    p in site['wan2_provider'].lower() for p in circuits_lower.split(', ')
                )
                
                if (wan1_needs_match and not wan1_found) or (wan2_needs_match and not wan2_found):
                    potential_mismatches.append(site)
    
    print(f'Sites with no circuits: {len(no_circuits)}')
    print(f'Sites with potential provider mismatches: {len(potential_mismatches)}\n')
    
    # Show top providers without circuits
    print('=== Top Providers Without Circuits ===\n')
    print(f"{'Provider':<40} {'Count'}")
    print('-' * 50)
    
    for provider, count in provider_counter.most_common(20):
        print(f'{provider:<40} {count}')
    
    # Check some specific examples
    print('\n\n=== Sample Sites Without Circuits ===\n')
    
    for site in no_circuits[:10]:
        print(f"{site['network_name']}:")
        print(f"  WAN1: {site['wan1_provider']} ({site['wan1_speed']})" if site['wan1_provider'] else '  WAN1: None')
        print(f"  WAN2: {site['wan2_provider']} ({site['wan2_speed']})" if site['wan2_provider'] else '  WAN2: None')
    
    # Look for fuzzy match opportunities
    print('\n\n=== Checking Fuzzy Match Potential ===\n')
    
    # Get all unique circuit providers
    cursor.execute('''
        SELECT DISTINCT provider_name 
        FROM circuits 
        WHERE status = 'Enabled'
        ORDER BY provider_name
    ''')
    all_circuit_providers = [row['provider_name'] for row in cursor.fetchall()]
    
    # Check top unmatched providers against circuit providers
    fuzzy_opportunities = []
    
    for provider, count in provider_counter.most_common(10):
        print(f"\nChecking '{provider}' ({count} sites):")
        best_matches = []
        
        for circuit_provider in all_circuit_providers:
            score = max(
                fuzz.ratio(provider.lower(), circuit_provider.lower()),
                fuzz.partial_ratio(provider.lower(), circuit_provider.lower()),
                fuzz.token_sort_ratio(provider.lower(), circuit_provider.lower())
            )
            
            if score >= 60:
                best_matches.append((circuit_provider, score))
        
        if best_matches:
            best_matches.sort(key=lambda x: -x[1])
            for cp, score in best_matches[:3]:
                print(f"  → '{cp}' (score: {score}%)")
                if score >= 70:
                    fuzzy_opportunities.append((provider, cp, score, count))
        else:
            print("  → No good matches found")
    
    if fuzzy_opportunities:
        print('\n\n=== Recommended Fuzzy Mappings ===\n')
        for provider, circuit_provider, score, count in fuzzy_opportunities:
            print(f"Map '{provider}' → '{circuit_provider}' (score: {score}%, affects {count} sites)")
    
    # Export detailed analysis
    print('\n\n=== Exporting Detailed Analysis ===')
    
    with open('/usr/local/bin/Main/circuit_matching_failures.csv', 'w') as f:
        f.write('Site,WAN1 Provider,WAN1 Speed,WAN2 Provider,WAN2 Speed,Status,Available Circuits\n')
        
        # No circuit sites
        for site in no_circuits:
            f.write(f'"{site["network_name"]}","{site["wan1_provider"] or ""}","{site["wan1_speed"] or ""}",')
            f.write(f'"{site["wan2_provider"] or ""}","{site["wan2_speed"] or ""}","No circuits",""\n')
        
        # Mismatch sites
        for site in potential_mismatches:
            f.write(f'"{site["network_name"]}","{site["wan1_provider"] or ""}","{site["wan1_speed"] or ""}",')
            f.write(f'"{site["wan2_provider"] or ""}","{site["wan2_speed"] or ""}","Provider mismatch","{site["circuits"]}"\n')
    
    print('✓ Exported to circuit_matching_failures.csv')
    
    # Summary
    print(f'\n=== Summary ===')
    print(f'Total sites analyzed: {len(all_sites)}')
    print(f'Sites without circuits: {len(no_circuits)} ({len(no_circuits)/len(all_sites)*100:.1f}%)')
    print(f'Sites with mismatches: {len(potential_mismatches)} ({len(potential_mismatches)/len(all_sites)*100:.1f}%)')
    print(f'Unique providers without circuits: {len(provider_counter)}')
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()