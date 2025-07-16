#!/usr/bin/env python3
"""
Comprehensive analysis of sites that have no matching circuits
"""

import sys
import os
sys.path.append('/usr/local/bin/Main')

import psycopg2
import psycopg2.extras
import re
from collections import defaultdict, Counter
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

def normalize_provider(provider):
    """Normalize provider name for comparison"""
    if not provider:
        return ""
    
    p = provider.lower().strip()
    
    # Remove common suffixes
    p = re.sub(r'\s*(communications|broadband|fiber|dedicated|business|workplace|inc\.|llc|corp).*$', '', p)
    p = re.sub(r'/boi$', '', p)  # Remove /BOI suffix
    p = re.sub(r'[^a-z0-9\s&-]', '', p)  # Remove special chars except & and -
    
    # Common replacements
    replacements = {
        'at&t': 'att',
        'at & t': 'att',
        'centurylink': 'lumen',
        'century link': 'lumen',
        'qwest': 'lumen',
        'embarq': 'lumen',
        'level 3': 'lumen',
        'level3': 'lumen',
        'charter': 'spectrum',
        'time warner': 'spectrum',
        'bright house': 'spectrum'
    }
    
    for old, new in replacements.items():
        if old in p:
            p = p.replace(old, new)
    
    return p.strip()

def main():
    """Main analysis"""
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=== Comprehensive Analysis of Unmatched Sites ===\n")
    
    # Get all circuits available
    cursor.execute("""
        SELECT site_name, provider_name, circuit_purpose
        FROM circuits
        WHERE status = 'Enabled'
        ORDER BY site_name, circuit_purpose
    """)
    
    all_circuits = {}
    for row in cursor.fetchall():
        site = row['site_name']
        if site not in all_circuits:
            all_circuits[site] = []
        all_circuits[site].append(row)
    
    # Get enriched sites that would fail to match
    cursor.execute("""
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
        WHERE ec.device_tags @> ARRAY['Discount-Tire']
            AND NOT EXISTS (
                SELECT 1 FROM unnest(ec.device_tags) AS tag 
                WHERE LOWER(tag) LIKE '%hub%' 
                   OR LOWER(tag) LIKE '%lab%' 
                   OR LOWER(tag) LIKE '%voice%'
                   OR LOWER(tag) LIKE '%test%'
            )
            AND (ec.wan1_provider IS NOT NULL OR ec.wan2_provider IS NOT NULL)
        ORDER BY ec.network_name
    """)
    
    enriched_sites = cursor.fetchall()
    
    print(f"Analyzing {len(enriched_sites)} Discount-Tire sites\n")
    
    # Track various failure patterns
    no_circuit_sites = []
    provider_mismatch_sites = []
    fuzzy_match_opportunities = []
    provider_frequency = Counter()
    mismatch_patterns = defaultdict(lambda: defaultdict(int))
    
    for site in enriched_sites:
        site_name = site['network_name']
        site_circuits = all_circuits.get(site_name, [])
        
        # Categorize the issue
        if not site_circuits:
            # No circuits at all
            no_circuit_sites.append(site)
            
            # Count provider frequencies
            if site['wan1_provider'] and site['wan1_speed'] and site['wan1_speed'].lower() not in ['cell', 'satellite']:
                provider_frequency[site['wan1_provider']] += 1
            if site['wan2_provider'] and site['wan2_speed'] and site['wan2_speed'].lower() not in ['cell', 'satellite']:
                provider_frequency[site['wan2_provider']] += 1
        else:
            # Has circuits but might not match
            wan1_match = False
            wan2_match = False
            
            # Check WAN1
            if site['wan1_provider'] and site['wan1_speed'] and site['wan1_speed'].lower() not in ['cell', 'satellite']:
                for circuit in site_circuits:
                    if circuit['circuit_purpose'] == 'Primary':
                        score = max(
                            fuzz.ratio(site['wan1_provider'].lower(), circuit['provider_name'].lower()),
                            fuzz.partial_ratio(site['wan1_provider'].lower(), circuit['provider_name'].lower()),
                            fuzz.token_sort_ratio(site['wan1_provider'].lower(), circuit['provider_name'].lower())
                        )
                        
                        if score >= 70:
                            wan1_match = True
                            break
                        else:
                            # Check normalized matching
                            norm1 = normalize_provider(site['wan1_provider'])
                            norm2 = normalize_provider(circuit['provider_name'])
                            if norm1 == norm2:
                                wan1_match = True
                                break
                
                if not wan1_match:
                    mismatch_patterns[site['wan1_provider']]['No Primary match'] += 1
                    fuzzy_match_opportunities.append({
                        'site': site_name,
                        'wan': 'WAN1',
                        'provider': site['wan1_provider'],
                        'available_circuits': [f"{c['provider_name']} ({c['circuit_purpose']})" for c in site_circuits]
                    })
            
            # Check WAN2
            if site['wan2_provider'] and site['wan2_speed'] and site['wan2_speed'].lower() not in ['cell', 'satellite']:
                for circuit in site_circuits:
                    if circuit['circuit_purpose'] == 'Secondary':
                        score = max(
                            fuzz.ratio(site['wan2_provider'].lower(), circuit['provider_name'].lower()),
                            fuzz.partial_ratio(site['wan2_provider'].lower(), circuit['provider_name'].lower()),
                            fuzz.token_sort_ratio(site['wan2_provider'].lower(), circuit['provider_name'].lower())
                        )
                        
                        if score >= 70:
                            wan2_match = True
                            break
                        else:
                            # Check normalized matching
                            norm1 = normalize_provider(site['wan2_provider'])
                            norm2 = normalize_provider(circuit['provider_name'])
                            if norm1 == norm2:
                                wan2_match = True
                                break
                
                if not wan2_match:
                    mismatch_patterns[site['wan2_provider']]['No Secondary match'] += 1
                    fuzzy_match_opportunities.append({
                        'site': site_name,
                        'wan': 'WAN2',
                        'provider': site['wan2_provider'],
                        'available_circuits': [f"{c['provider_name']} ({c['circuit_purpose']})" for c in site_circuits]
                    })
    
    # Report findings
    print(f"=== Site Categories ===")
    print(f"Sites with no circuits at all: {len(no_circuit_sites)}")
    print(f"Sites with potential fuzzy matches: {len(fuzzy_match_opportunities)}")
    
    # Top providers with no circuits
    print(f"\n=== Top Providers Without Circuits (Frequency) ===\n")
    
    for provider, count in provider_frequency.most_common(20):
        print(f"{provider:<40} {count:>3} times")
        
        # Check if fuzzy/mapping would help
        matches_in_db = set()
        for site_name, circuits in all_circuits.items():
            for circuit in circuits:
                score = max(
                    fuzz.ratio(provider.lower(), circuit['provider_name'].lower()),
                    fuzz.partial_ratio(provider.lower(), circuit['provider_name'].lower())
                )
                if score >= 70:
                    matches_in_db.add(circuit['provider_name'])
        
        if matches_in_db:
            print(f"  → Could fuzzy match to: {', '.join(sorted(matches_in_db)[:3])}")
    
    # Analyze fuzzy match opportunities
    print(f"\n\n=== Fuzzy Match Opportunities ===\n")
    
    fuzzy_summary = defaultdict(list)
    for opp in fuzzy_match_opportunities[:20]:
        provider = opp['provider']
        fuzzy_summary[provider].append(opp)
    
    for provider, opps in sorted(fuzzy_summary.items(), key=lambda x: -len(x[1]))[:10]:
        print(f"\n'{provider}' ({len(opps)} sites):")
        
        # Find best matches across all circuits
        best_matches = Counter()
        for opp in opps:
            for circuit_str in opp['available_circuits']:
                circuit_provider = circuit_str.split(' (')[0]
                score = max(
                    fuzz.ratio(provider.lower(), circuit_provider.lower()),
                    fuzz.partial_ratio(provider.lower(), circuit_provider.lower())
                )
                if score >= 60:
                    best_matches[f"{circuit_provider} ({score}%)"] += 1
        
        if best_matches:
            print(f"  Best fuzzy matches:")
            for match, count in best_matches.most_common(3):
                print(f"    → {match} ({count} times)")
    
    # Provider mapping recommendations
    print(f"\n\n=== Provider Mapping Recommendations ===\n")
    
    # Analyze patterns for mappings
    mapping_candidates = defaultdict(lambda: defaultdict(int))
    
    for site in no_circuit_sites:
        # Look for sites with similar names that do have circuits
        site_prefix = re.match(r'^([A-Z]+)', site['network_name'])
        if site_prefix:
            prefix = site_prefix.group(1)
            
            # Find other sites with same prefix that have circuits
            for other_site, circuits in all_circuits.items():
                if other_site.startswith(prefix) and other_site != site['network_name']:
                    for circuit in circuits:
                        if site['wan1_provider'] and circuit['circuit_purpose'] == 'Primary':
                            mapping_candidates[site['wan1_provider']][circuit['provider_name']] += 1
                        if site['wan2_provider'] and circuit['circuit_purpose'] == 'Secondary':
                            mapping_candidates[site['wan2_provider']][circuit['provider_name']] += 1
    
    print("Based on same-region analysis:")
    for device_provider, circuit_counts in sorted(mapping_candidates.items(), 
                                                  key=lambda x: sum(x[1].values()), 
                                                  reverse=True)[:15]:
        total = sum(circuit_counts.values())
        if total >= 2:
            print(f"\n'{device_provider}':")
            for circuit_provider, count in sorted(circuit_counts.items(), key=lambda x: -x[1])[:3]:
                if count >= 2:
                    print(f"  → Map to '{circuit_provider}' ({count} similar sites)")
    
    # Export detailed analysis
    print("\n\n=== Exporting Detailed Analysis ===")
    
    with open('/usr/local/bin/Main/unmatched_sites_comprehensive.csv', 'w') as f:
        f.write("Site,Provider Type,Device Notes Provider,ARIN Provider,Speed,Issue,Recommendation\n")
        
        # Sites with no circuits
        for site in no_circuit_sites:
            if site['wan1_provider'] and site['wan1_speed'] and site['wan1_speed'].lower() not in ['cell', 'satellite']:
                f.write(f'"{site["network_name"]}","WAN1","{site["wan1_provider"]}","{site["wan1_arin_org"] or ""}","{site["wan1_speed"]}","No circuits","Create circuit or verify site status"\n')
            if site['wan2_provider'] and site['wan2_speed'] and site['wan2_speed'].lower() not in ['cell', 'satellite']:
                f.write(f'"{site["network_name"]}","WAN2","{site["wan2_provider"]}","{site["wan2_arin_org"] or ""}","{site["wan2_speed"]}","No circuits","Create circuit or verify site status"\n')
        
        # Fuzzy match opportunities
        for opp in fuzzy_match_opportunities:
            circuits_str = '; '.join(opp['available_circuits'])
            f.write(f'"{opp["site"]}","{opp["wan"]}","{opp["provider"]}","","","Has circuits but no match","Fuzzy match or mapping needed: {circuits_str}"\n')
    
    print("✓ Exported to unmatched_sites_comprehensive.csv")
    
    # Summary statistics
    print(f"\n=== Summary Statistics ===")
    print(f"Total Discount-Tire sites analyzed: {len(enriched_sites)}")
    print(f"Sites with no circuits: {len(no_circuit_sites)}")
    print(f"Sites needing fuzzy/mapping: {len(fuzzy_match_opportunities)}")
    print(f"Unique providers without circuits: {len(provider_frequency)}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()