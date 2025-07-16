#!/usr/bin/env python3
"""
Analyze provider mismatches between device notes and DSR circuits
"""

import sys
import os
sys.path.append('/usr/local/bin/Main')

import psycopg2
import psycopg2.extras
import re
from collections import defaultdict
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
    """Analyze provider mismatches"""
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=== Analyzing Provider Mismatches ===\n")
    
    # Get sites with both enriched data and circuits
    cursor.execute("""
        WITH site_providers AS (
            SELECT DISTINCT
                ec.network_name,
                ec.wan1_provider as wan1_notes,
                ec.wan1_speed,
                ec.wan1_arin_org,
                ec.wan2_provider as wan2_notes, 
                ec.wan2_speed,
                ec.wan2_arin_org,
                ec.device_tags
            FROM enriched_circuits ec
            WHERE ec.device_tags @> ARRAY['Discount-Tire']
                AND NOT EXISTS (
                    SELECT 1 FROM unnest(ec.device_tags) AS tag 
                    WHERE LOWER(tag) LIKE '%hub%' 
                       OR LOWER(tag) LIKE '%lab%' 
                       OR LOWER(tag) LIKE '%voice%'
                       OR LOWER(tag) LIKE '%test%'
                )
        ),
        circuit_providers AS (
            SELECT 
                c.site_name,
                array_agg(DISTINCT c.provider_name || ' (' || c.circuit_purpose || ')') as circuit_list,
                array_agg(DISTINCT CASE WHEN c.circuit_purpose = 'Primary' THEN c.provider_name END) as primary_providers,
                array_agg(DISTINCT CASE WHEN c.circuit_purpose = 'Secondary' THEN c.provider_name END) as secondary_providers
            FROM circuits c
            WHERE c.status = 'Enabled'
            GROUP BY c.site_name
        )
        SELECT 
            sp.*,
            cp.circuit_list,
            cp.primary_providers,
            cp.secondary_providers
        FROM site_providers sp
        LEFT JOIN circuit_providers cp ON sp.network_name = cp.site_name
        WHERE cp.circuit_list IS NOT NULL  -- Has circuits
        ORDER BY sp.network_name
    """)
    
    sites = cursor.fetchall()
    
    print(f"Found {len(sites)} Discount-Tire sites with circuits\n")
    
    # Analyze mismatches
    provider_mismatches = defaultdict(lambda: defaultdict(int))
    fuzzy_scores = []
    
    for site in sites:
        # Check WAN1/Primary mismatches
        if site['wan1_notes'] and site['primary_providers']:
            wan1_notes = site['wan1_notes']
            primary_providers = [p for p in site['primary_providers'] if p]
            
            if primary_providers:
                primary_provider = primary_providers[0]
                
                # Calculate fuzzy score
                score = max(
                    fuzz.ratio(wan1_notes.lower(), primary_provider.lower()),
                    fuzz.partial_ratio(wan1_notes.lower(), primary_provider.lower()),
                    fuzz.token_sort_ratio(wan1_notes.lower(), primary_provider.lower())
                )
                
                if score < 90:  # Not an exact/near-exact match
                    provider_mismatches[wan1_notes][primary_provider] += 1
                    fuzzy_scores.append({
                        'site': site['network_name'],
                        'wan': 'WAN1',
                        'notes': wan1_notes,
                        'circuit': primary_provider,
                        'score': score,
                        'arin': site['wan1_arin_org']
                    })
        
        # Check WAN2/Secondary mismatches
        if site['wan2_notes'] and site['secondary_providers'] and site['wan2_speed'] and site['wan2_speed'].lower() not in ['cell', 'satellite']:
            wan2_notes = site['wan2_notes']
            secondary_providers = [p for p in site['secondary_providers'] if p]
            
            if secondary_providers:
                secondary_provider = secondary_providers[0]
                
                # Calculate fuzzy score
                score = max(
                    fuzz.ratio(wan2_notes.lower(), secondary_provider.lower()),
                    fuzz.partial_ratio(wan2_notes.lower(), secondary_provider.lower()),
                    fuzz.token_sort_ratio(wan2_notes.lower(), secondary_provider.lower())
                )
                
                if score < 90:  # Not an exact/near-exact match
                    provider_mismatches[wan2_notes][secondary_provider] += 1
                    fuzzy_scores.append({
                        'site': site['network_name'],
                        'wan': 'WAN2',
                        'notes': wan2_notes,
                        'circuit': secondary_provider,
                        'score': score,
                        'arin': site['wan2_arin_org']
                    })
    
    # Show top mismatches
    print("=== Top Provider Mismatches (Device Notes → Circuit Provider) ===\n")
    
    mismatch_summary = []
    for notes_provider, circuit_matches in provider_mismatches.items():
        for circuit_provider, count in circuit_matches.items():
            mismatch_summary.append({
                'notes': notes_provider,
                'circuit': circuit_provider,
                'count': count
            })
    
    mismatch_summary.sort(key=lambda x: -x['count'])
    
    print(f"{'Device Notes':<30} {'Circuit Provider':<30} {'Count':<6} {'Suggested Mapping'}")
    print("-" * 100)
    
    for m in mismatch_summary[:20]:
        # Suggest mapping
        if m['count'] >= 3:
            suggestion = "YES - Consistent pattern"
        elif m['count'] == 2:
            suggestion = "MAYBE - Small pattern"
        else:
            suggestion = "NO - Single occurrence"
        
        print(f"{m['notes']:<30} {m['circuit']:<30} {m['count']:<6} {suggestion}")
    
    # Analyze fuzzy score distribution
    print("\n\n=== Fuzzy Score Analysis ===\n")
    
    score_ranges = {
        '80-89%': [s for s in fuzzy_scores if 80 <= s['score'] < 90],
        '70-79%': [s for s in fuzzy_scores if 70 <= s['score'] < 80],
        '60-69%': [s for s in fuzzy_scores if 60 <= s['score'] < 70],
        '50-59%': [s for s in fuzzy_scores if 50 <= s['score'] < 60],
        '<50%': [s for s in fuzzy_scores if s['score'] < 50]
    }
    
    for range_name, scores in score_ranges.items():
        print(f"{range_name}: {len(scores)} mismatches")
    
    # Show examples from each range
    print("\n=== Examples by Score Range ===")
    
    for range_name, scores in score_ranges.items():
        if scores:
            print(f"\n{range_name} Examples:")
            for s in scores[:5]:
                print(f"  {s['site']} {s['wan']}: '{s['notes']}' vs '{s['circuit']}' (score: {s['score']}%)")
                if s['arin']:
                    print(f"    ARIN: {s['arin']}")
    
    # Specific provider analysis
    print("\n\n=== Specific Provider Pattern Analysis ===\n")
    
    # Look for Frontier patterns
    frontier_patterns = [s for s in fuzzy_scores if 'frontier' in s['notes'].lower() or 'frontier' in s['circuit'].lower()]
    if frontier_patterns:
        print("Frontier Patterns:")
        for fp in frontier_patterns[:10]:
            print(f"  {fp['site']}: '{fp['notes']}' vs '{fp['circuit']}' (score: {fp['score']}%)")
    
    # Look for AT&T patterns
    att_patterns = [s for s in fuzzy_scores if 'at&t' in s['notes'].lower() or 'at&t' in s['circuit'].lower()]
    if att_patterns:
        print("\nAT&T Patterns:")
        for ap in att_patterns[:10]:
            print(f"  {ap['site']}: '{ap['notes']}' vs '{ap['circuit']}' (score: {ap['score']}%)")
    
    # Export detailed mismatches
    print("\n\n=== Exporting Detailed Mismatches ===")
    
    with open('/usr/local/bin/Main/provider_mismatches_analysis.csv', 'w') as f:
        f.write("Site,WAN,Device Notes,Circuit Provider,Fuzzy Score,ARIN Provider,Mapping Recommended\n")
        
        for s in sorted(fuzzy_scores, key=lambda x: (x['notes'], -x['score'])):
            # Find if this is a common pattern
            pattern_count = provider_mismatches[s['notes']][s['circuit']]
            mapping_rec = 'Yes' if pattern_count >= 3 else 'Maybe' if pattern_count >= 2 else 'No'
            
            f.write(f'"{s["site"]}","{s["wan"]}","{s["notes"]}","{s["circuit"]}",{s["score"]},"{s["arin"] or ""}","{mapping_rec}"\n')
    
    print("✓ Exported to provider_mismatches_analysis.csv")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()