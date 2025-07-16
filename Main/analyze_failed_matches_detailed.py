#!/usr/bin/env python3
"""
Analyze failed circuit matches in detail to identify patterns
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

def analyze_failures():
    """Analyze all failed matches in detail"""
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get all enriched circuits with their device tags
    cursor.execute("""
        SELECT 
            ec.network_name,
            ec.wan1_provider,
            ec.wan1_speed,
            ec.wan1_arin_org,
            ec.wan2_provider,
            ec.wan2_speed,
            ec.wan2_arin_org,
            ec.device_tags,
            -- Check if any circuits exist
            (SELECT COUNT(*) FROM circuits WHERE site_name = ec.network_name AND status = 'Enabled') as circuit_count
        FROM enriched_circuits ec
        WHERE ec.network_name LIKE '%'
        ORDER BY ec.network_name
    """)
    
    all_sites = cursor.fetchall()
    
    # Get all DSR circuits
    cursor.execute("""
        SELECT DISTINCT site_name, provider_name, circuit_purpose
        FROM circuits
        WHERE status = 'Enabled'
        AND data_source = 'csv_import'
        ORDER BY site_name, provider_name
    """)
    
    dsr_circuits = {}
    for circuit in cursor.fetchall():
        site = circuit['site_name']
        if site not in dsr_circuits:
            dsr_circuits[site] = []
        dsr_circuits[site].append(circuit)
    
    # Analyze failures
    failures = []
    provider_failure_patterns = defaultdict(list)
    
    for site in all_sites:
        # Skip sites with no IP addresses (not online)
        if not site['wan1_provider'] and not site['wan2_provider']:
            continue
        
        # Skip non-Discount-Tire sites
        if site['device_tags'] and 'Discount-Tire' not in site['device_tags']:
            continue
        
        # Skip hub/lab/voice/test sites
        if site['device_tags']:
            skip_tags = ['hub', 'lab', 'voice', 'test']
            if any(tag.lower() in ' '.join(site['device_tags']).lower() for tag in skip_tags):
                continue
        
        site_name = site['network_name']
        site_circuits = dsr_circuits.get(site_name, [])
        
        # Check WAN1
        if site['wan1_provider'] and site['wan1_speed'] and site['wan1_speed'].lower() not in ['cell', 'satellite']:
            # Try to find matching circuit
            found_match = False
            for circuit in site_circuits:
                if circuit['circuit_purpose'] == 'Primary':
                    found_match = True
                    break
            
            if not found_match:
                # Analyze why it failed
                wan1_fail = {
                    'site': site_name,
                    'wan': 'WAN1',
                    'device_notes': site['wan1_provider'],
                    'arin': site['wan1_arin_org'],
                    'speed': site['wan1_speed'],
                    'available_circuits': [f"{c['provider_name']} ({c['circuit_purpose']})" for c in site_circuits]
                }
                failures.append(wan1_fail)
                
                # Track provider patterns
                if site['wan1_provider']:
                    provider_failure_patterns[site['wan1_provider']].append({
                        'site': site_name,
                        'arin': site['wan1_arin_org'],
                        'circuits': wan1_fail['available_circuits']
                    })
        
        # Check WAN2
        if site['wan2_provider'] and site['wan2_speed'] and site['wan2_speed'].lower() not in ['cell', 'satellite']:
            # Try to find matching circuit
            found_match = False
            for circuit in site_circuits:
                if circuit['circuit_purpose'] == 'Secondary':
                    found_match = True
                    break
            
            if not found_match:
                # Analyze why it failed
                wan2_fail = {
                    'site': site_name,
                    'wan': 'WAN2',
                    'device_notes': site['wan2_provider'],
                    'arin': site['wan2_arin_org'],
                    'speed': site['wan2_speed'],
                    'available_circuits': [f"{c['provider_name']} ({c['circuit_purpose']})" for c in site_circuits]
                }
                failures.append(wan2_fail)
                
                # Track provider patterns
                if site['wan2_provider']:
                    provider_failure_patterns[site['wan2_provider']].append({
                        'site': site_name,
                        'arin': site['wan2_arin_org'],
                        'circuits': wan2_fail['available_circuits']
                    })
    
    return failures, provider_failure_patterns, dsr_circuits

def analyze_fuzzy_potential(failures, dsr_circuits):
    """Analyze if fuzzy matching would help"""
    
    fuzzy_opportunities = []
    
    for fail in failures:
        site_name = fail['site']
        device_notes = fail['device_notes']
        
        if not device_notes or site_name not in dsr_circuits:
            continue
        
        # Test fuzzy matching against available circuits
        best_match = None
        best_score = 0
        
        for circuit in dsr_circuits[site_name]:
            # Skip if wrong purpose
            if fail['wan'] == 'WAN1' and circuit['circuit_purpose'] != 'Primary':
                continue
            if fail['wan'] == 'WAN2' and circuit['circuit_purpose'] != 'Secondary':
                continue
            
            # Calculate fuzzy scores
            scores = [
                fuzz.ratio(device_notes.lower(), circuit['provider_name'].lower()),
                fuzz.partial_ratio(device_notes.lower(), circuit['provider_name'].lower()),
                fuzz.token_sort_ratio(device_notes.lower(), circuit['provider_name'].lower())
            ]
            max_score = max(scores)
            
            if max_score > best_score:
                best_score = max_score
                best_match = circuit['provider_name']
        
        if best_match:
            fuzzy_opportunities.append({
                'site': site_name,
                'wan': fail['wan'],
                'device_notes': device_notes,
                'best_match': best_match,
                'score': best_score,
                'would_match_70': best_score >= 70,
                'would_match_60': best_score >= 60
            })
    
    return fuzzy_opportunities

def main():
    """Main analysis"""
    
    print("=== Analyzing Failed Circuit Matches ===\n")
    
    failures, provider_patterns, dsr_circuits = analyze_failures()
    
    print(f"Total failures: {len(failures)}\n")
    
    # Analyze provider failure patterns
    print("=== Provider Failure Frequency ===\n")
    
    provider_summary = []
    for provider, fails in sorted(provider_patterns.items(), key=lambda x: -len(x[1])):
        provider_summary.append({
            'provider': provider,
            'count': len(fails),
            'sites': [f['site'] for f in fails[:5]]  # First 5 examples
        })
    
    print(f"{'Provider':<30} {'Failures':<10} {'Example Sites'}")
    print("-" * 80)
    
    for ps in provider_summary[:20]:  # Top 20
        sites_str = ', '.join(ps['sites'][:3])
        if len(ps['sites']) > 3:
            sites_str += f" +{len(ps['sites'])-3} more"
        print(f"{ps['provider']:<30} {ps['count']:<10} {sites_str}")
    
    # Analyze fuzzy matching potential
    print("\n\n=== Fuzzy Matching Analysis ===\n")
    
    fuzzy_ops = analyze_fuzzy_potential(failures, dsr_circuits)
    
    # Group by score ranges
    would_match_70 = [f for f in fuzzy_ops if f['would_match_70']]
    would_match_60 = [f for f in fuzzy_ops if f['would_match_60'] and not f['would_match_70']]
    no_match = [f for f in fuzzy_ops if not f['would_match_60']]
    
    print(f"Fuzzy matching at 70% threshold: {len(would_match_70)} matches")
    print(f"Fuzzy matching at 60% threshold: {len(would_match_60)} additional matches")
    print(f"No fuzzy match even at 60%: {len(no_match)} failures")
    
    # Show examples of each category
    print("\n=== Examples of 70%+ Fuzzy Matches ===")
    for f in would_match_70[:10]:
        print(f"{f['site']} {f['wan']}: '{f['device_notes']}' → '{f['best_match']}' (score: {f['score']}%)")
    
    print("\n=== Examples of 60-69% Fuzzy Matches ===")
    for f in would_match_60[:10]:
        print(f"{f['site']} {f['wan']}: '{f['device_notes']}' → '{f['best_match']}' (score: {f['score']}%)")
    
    # Analyze specific provider mapping opportunities
    print("\n\n=== Provider Mapping Opportunities ===\n")
    
    # Look for consistent patterns
    mapping_candidates = defaultdict(lambda: defaultdict(int))
    
    for fail in failures:
        if not fail['device_notes']:
            continue
        
        device_provider = fail['device_notes']
        
        # Look at what circuits are available
        for circuit_str in fail['available_circuits']:
            circuit_provider = circuit_str.split(' (')[0]
            mapping_candidates[device_provider][circuit_provider] += 1
    
    # Show top mapping candidates
    print("Device Notes Provider → Available Circuit Provider (frequency)")
    print("-" * 60)
    
    for device_provider, circuit_counts in sorted(mapping_candidates.items(), 
                                                  key=lambda x: sum(x[1].values()), 
                                                  reverse=True)[:20]:
        total = sum(circuit_counts.values())
        if total < 2:  # Skip one-offs
            continue
        
        print(f"\n'{device_provider}' ({total} sites):")
        for circuit_provider, count in sorted(circuit_counts.items(), key=lambda x: -x[1]):
            if count >= 2:  # Only show patterns with 2+ occurrences
                print(f"  → '{circuit_provider}' ({count} times)")
    
    # Export detailed failure list
    print("\n\n=== Exporting Detailed Failure List ===")
    
    with open('/usr/local/bin/Main/circuit_failures_detailed.csv', 'w') as f:
        f.write("Site,WAN,Device Notes Provider,ARIN Provider,Speed,Available Circuits\n")
        for fail in sorted(failures, key=lambda x: (x['device_notes'] or '', x['site'])):
            circuits_str = '; '.join(fail['available_circuits']) if fail['available_circuits'] else 'No circuits'
            f.write(f'"{fail["site"]}","{fail["wan"]}","{fail["device_notes"] or ""}","{fail["arin"] or ""}","{fail["speed"] or ""}","{circuits_str}"\n')
    
    print("✓ Exported to circuit_failures_detailed.csv")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()