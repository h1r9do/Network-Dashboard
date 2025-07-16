#!/usr/bin/env python3
"""
Check for non-cell circuits with $0.00 cost in the database
and look for matching cost data in the master circuit JSON file
"""

import os
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the script directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import Config

# Configuration
DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI
JSON_FILE = "/var/www/html/circuitinfo/master_circuit_data_20250701_150111.json"

def get_db_session():
    """Create database session"""
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session()

def normalize_provider_name(provider):
    """Normalize provider names for comparison"""
    if not provider:
        return ""
    
    # Convert to string and strip whitespace
    provider = str(provider).strip().upper()
    
    # Common normalizations
    replacements = {
        'AT&T BROADBAND II': 'AT&T',
        'ATT': 'AT&T',
        'CHARTER COMMUNICATIONS': 'SPECTRUM',
        'CHARTER': 'SPECTRUM',
        'COMCAST WORKPLACE': 'COMCAST',
        'COX BUSINESS/BOI': 'COX',
        'COX BUSINESS': 'COX',
        'VERIZON BUSINESS': 'VERIZON',
        'VZ': 'VERIZON',
        'VZG': 'VERIZON',
        'CENTURYLINK': 'CENTURYLINK',
        'CLINK': 'CENTURYLINK',
        'LUMEN': 'CENTURYLINK'
    }
    
    for old, new in replacements.items():
        if old in provider:
            provider = new
            break
    
    return provider

def is_cell_or_satellite(speed):
    """Check if speed indicates cell or satellite service"""
    if not speed:
        return False
    speed_lower = str(speed).lower()
    return 'cell' in speed_lower or 'satellite' in speed_lower

def main():
    print(f"\n{'='*80}")
    print(f"Zero Cost Circuit Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Load master circuit JSON data
    print(f"Loading master circuit data from: {JSON_FILE}")
    with open(JSON_FILE, 'r') as f:
        master_data = json.load(f)
    
    # Create lookup dictionary by store name
    master_lookup = {}
    for record in master_data:
        store = record.get('Store')
        if store:
            master_lookup[store.upper()] = record
    
    print(f"Loaded {len(master_lookup)} stores from master list\n")
    
    session = get_db_session()
    
    try:
        # Find all enriched circuits with $0.00 cost that are not cell/satellite
        result = session.execute(text("""
            SELECT DISTINCT ec.network_name,
                   ec.wan1_provider, ec.wan1_speed, ec.wan1_monthly_cost,
                   ec.wan2_provider, ec.wan2_speed, ec.wan2_monthly_cost
            FROM enriched_circuits ec
            WHERE (ec.wan1_monthly_cost = '$0.00' OR ec.wan2_monthly_cost = '$0.00')
            ORDER BY ec.network_name
        """))
        
        zero_cost_circuits = []
        for row in result:
            circuit = {
                'site_name': row[0],
                'circuit_purpose': row[1],
                'provider_name': row[2],
                'speed': row[3],
                'billing_monthly_cost': row[4],
                'wan1_provider': row[5],
                'wan1_speed': row[6],
                'wan1_monthly_cost': row[7],
                'wan2_provider': row[8],
                'wan2_speed': row[9],
                'wan2_monthly_cost': row[10]
            }
            
            # Skip if this is a cell/satellite circuit
            if is_cell_or_satellite(circuit['speed']):
                continue
                
            zero_cost_circuits.append(circuit)
        
        print(f"Found {len(zero_cost_circuits)} non-cell/satellite circuits with $0.00 cost\n")
        
        # Check each zero-cost circuit against master data
        matches_found = []
        no_matches = []
        
        for circuit in zero_cost_circuits:
            site_name = circuit['site_name'].upper() if circuit['site_name'] else ''
            
            if site_name in master_lookup:
                master = master_lookup[site_name]
                
                # Normalize provider names for comparison
                circuit_provider = normalize_provider_name(circuit['provider_name'])
                
                # Check if this is primary or secondary circuit
                is_primary = 'primary' in (circuit['circuit_purpose'] or '').lower()
                
                if is_primary:
                    master_provider = normalize_provider_name(master.get('Active A Circuit Carrier'))
                    master_cost = master.get('MRC')
                    master_speed = master.get('Active A Speed')
                else:
                    master_provider = normalize_provider_name(master.get('Active B Circuit Carrier'))
                    master_cost = master.get('MRC3')
                    master_speed = master.get('Active B Speed')
                
                # Check if providers match
                if circuit_provider and master_provider and circuit_provider == master_provider:
                    if master_cost and master_cost != 0:
                        matches_found.append({
                            'site_name': circuit['site_name'],
                            'circuit_purpose': circuit['circuit_purpose'],
                            'provider': circuit['provider_name'],
                            'speed': circuit['speed'],
                            'current_cost': 0,
                            'master_cost': master_cost,
                            'master_provider': master.get('Active A Circuit Carrier' if is_primary else 'Active B Circuit Carrier'),
                            'master_speed': master_speed
                        })
                    else:
                        no_matches.append({
                            'site_name': circuit['site_name'],
                            'circuit_purpose': circuit['circuit_purpose'],
                            'provider': circuit['provider_name'],
                            'reason': 'Provider matches but no cost in master'
                        })
                else:
                    no_matches.append({
                        'site_name': circuit['site_name'],
                        'circuit_purpose': circuit['circuit_purpose'],
                        'provider': circuit['provider_name'],
                        'reason': f'Provider mismatch: DB={circuit_provider}, Master={master_provider}'
                    })
            else:
                no_matches.append({
                    'site_name': circuit['site_name'],
                    'circuit_purpose': circuit['circuit_purpose'],
                    'provider': circuit['provider_name'],
                    'reason': 'Site not found in master list'
                })
        
        # Display results
        print(f"\n{'='*80}")
        print(f"CIRCUITS WITH MATCHING COST DATA IN MASTER LIST: {len(matches_found)}")
        print(f"{'='*80}\n")
        
        if matches_found:
            for match in matches_found[:20]:  # Show first 20
                print(f"Site: {match['site_name']}")
                print(f"  Purpose: {match['circuit_purpose']}")
                print(f"  Provider: {match['provider']} → {match['master_provider']}")
                print(f"  Speed: {match['speed']} → {match['master_speed']}")
                print(f"  Cost: ${match['current_cost']:.2f} → ${match['master_cost']:.2f}")
                print()
            
            if len(matches_found) > 20:
                print(f"... and {len(matches_found) - 20} more matches found\n")
        
        print(f"\n{'='*80}")
        print(f"CIRCUITS WITHOUT MATCHING COST DATA: {len(no_matches)}")
        print(f"{'='*80}\n")
        
        # Group no matches by reason
        reason_counts = {}
        for no_match in no_matches:
            reason = no_match['reason']
            if reason not in reason_counts:
                reason_counts[reason] = 0
            reason_counts[reason] += 1
        
        for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {reason}: {count}")
        
        # Save matches to file for potential update
        if matches_found:
            output_file = f"/usr/local/bin/Main/zero_cost_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump(matches_found, f, indent=2)
            print(f"\n✅ Saved {len(matches_found)} matches to: {output_file}")
        
        return matches_found
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        session.close()

if __name__ == "__main__":
    matches = main()
    sys.exit(0 if matches else 1)