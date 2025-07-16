#!/usr/bin/env python3
"""
Test script to populate enriched_circuits_test with provider matching logic
This will test our provider mapping system before applying to production
"""

import os
import sys
import re
from datetime import datetime
import psycopg2
import psycopg2.extras

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def get_db_connection():
    """Get database connection using config"""
    match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
    if not match:
        raise ValueError("Invalid database URI")
    
    user, password, host, port, database = match.groups()
    
    return psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )

def load_provider_mappings(cursor):
    """Load provider mappings from database"""
    try:
        cursor.execute("""
            SELECT LOWER(dsr_provider) as dsr_lower, 
                   arin_provider, 
                   mapping_type, 
                   confidence_score
            FROM provider_mappings
            WHERE mapping_type != 'ignore'
            ORDER BY confidence_score DESC
        """)
        
        mappings = {}
        for row in cursor.fetchall():
            dsr_lower = row[0]
            if dsr_lower not in mappings:
                mappings[dsr_lower] = []
            mappings[dsr_lower].append({
                'arin_provider': row[1],
                'mapping_type': row[2],
                'confidence': row[3]
            })
        
        return mappings
    except Exception as e:
        print(f"Warning: Could not load provider mappings: {e}")
        return {}

def normalize_provider(provider):
    """Enhanced provider normalization"""
    if not provider:
        return ""
    
    # Convert to lowercase and strip
    provider = str(provider).lower().strip()
    
    # Handle EB2- prefix
    if provider.startswith('eb2-'):
        provider = provider[4:]
        provider = re.sub(r'\s*(dsl|fiber|cable|kinetic)$', '', provider)
    
    # Remove other prefixes
    provider = re.sub(r'^(dsr|agg|comcastagg|not\s+dsr|--|-)\s+', '', provider)
    
    # Remove service suffixes
    provider = re.sub(r'\s*(extended\s+cable|workplace|broadband\s+ii|fiber\s+plus|/boi|/embarq|/qwest|cable|dsl|fiber)$', '', provider)
    
    # Clean special characters
    provider = re.sub(r'[^\w\s&/-]', ' ', provider)
    provider = re.sub(r'\s+', ' ', provider).strip()
    
    return provider

def check_provider_match(dsr_provider, arin_provider, circuit_purpose, mappings):
    """
    Check provider match using mappings
    Returns dict with status, confidence, canonical provider, and reason
    """
    if not dsr_provider or not arin_provider:
        return {
            'status': 'no_data',
            'confidence': 0,
            'canonical': dsr_provider or 'Unknown',
            'reason': 'Missing provider data'
        }
    
    # Direct match
    if dsr_provider.lower().strip() == arin_provider.lower().strip():
        return {
            'status': 'matched',
            'confidence': 100,
            'canonical': arin_provider,
            'reason': 'Direct match'
        }
    
    # Check mapping table
    dsr_lower = dsr_provider.lower().strip()
    if dsr_lower in mappings:
        for mapping in mappings[dsr_lower]:
            if mapping['arin_provider'].lower() == arin_provider.lower():
                return {
                    'status': 'matched',
                    'confidence': mapping['confidence'],
                    'canonical': mapping['arin_provider'],
                    'reason': f"Mapped ({mapping['mapping_type']})"
                }
    
    # Normalize and try again
    dsr_norm = normalize_provider(dsr_provider)
    arin_norm = normalize_provider(arin_provider)
    
    if dsr_norm == arin_norm:
        return {
            'status': 'matched',
            'confidence': 95,
            'canonical': arin_provider,
            'reason': 'Normalized match'
        }
    
    # Check mapping with normalized names
    if dsr_norm in mappings:
        for mapping in mappings[dsr_norm]:
            if normalize_provider(mapping['arin_provider']) == arin_norm:
                return {
                    'status': 'matched',
                    'confidence': mapping['confidence'],
                    'canonical': mapping['arin_provider'],
                    'reason': f"Normalized mapped ({mapping['mapping_type']})"
                }
    
    # Handle secondary circuit conflicts
    if circuit_purpose == 'Secondary':
        if 'comcast' in dsr_norm and arin_provider == 'AT&T':
            return {
                'status': 'matched',
                'confidence': 70,
                'canonical': dsr_provider,
                'reason': 'Secondary circuit conflict (trust DSR)'
            }
        if 'cox' in dsr_norm and arin_provider in ['AT&T', 'Verizon']:
            return {
                'status': 'matched',
                'confidence': 70,
                'canonical': dsr_provider,
                'reason': 'Secondary circuit conflict (trust DSR)'
            }
        if 'spectrum' in dsr_norm and arin_provider == 'AT&T':
            return {
                'status': 'matched',
                'confidence': 70,
                'canonical': dsr_provider,
                'reason': 'Secondary circuit conflict (trust DSR)'
            }
    
    # No match
    return {
        'status': 'no_match',
        'confidence': 0,
        'canonical': dsr_provider,
        'reason': 'No match found'
    }

def populate_test_enriched_circuits():
    """Populate the test enriched circuits table with provider matching logic"""
    
    print("Starting test provider enrichment...")
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Load provider mappings
    mappings = load_provider_mappings(cursor)
    print(f"Loaded {len(mappings)} provider mappings")
    
    # Get all DSR circuits
    cursor.execute("""
        SELECT 
            c.site_id,
            c.site_name,
            c.circuit_purpose,
            c.provider_name as dsr_provider,
            c.ip_address_start as dsr_ip,
            c.details_ordered_service_speed as speed,
            c.billing_monthly_cost as cost
        FROM circuits c
        WHERE c.status = 'Enabled'
        AND c.provider_name IS NOT NULL
        AND c.provider_name != ''
        ORDER BY c.site_name, c.circuit_purpose
    """)
    
    circuits = cursor.fetchall()
    print(f"Found {len(circuits)} DSR circuits to process")
    
    processed = 0
    matched = 0
    
    for circuit in circuits:
        site_id = circuit['site_id']
        site_name = circuit['site_name']
        circuit_purpose = circuit['circuit_purpose']
        dsr_provider = circuit['dsr_provider']
        dsr_ip = circuit['dsr_ip']
        speed = circuit['speed']
        cost = circuit['cost']
        
        # Get Meraki data for this site
        cursor.execute("""
            SELECT DISTINCT ON (network_name)
                wan1_ip, wan1_arin_provider,
                wan2_ip, wan2_arin_provider
            FROM meraki_inventory
            WHERE network_name = %s
            AND device_model LIKE 'MX%'
            ORDER BY network_name, last_updated DESC
        """, (site_name,))
        
        meraki_row = cursor.fetchone()
        
        # Initialize variables
        wan_port = None
        arin_provider = None
        matched_ip = None
        
        if meraki_row:
            # Check for direct IP match
            if dsr_ip == meraki_row['wan1_ip']:
                wan_port = 'WAN1'
                arin_provider = meraki_row['wan1_arin_provider']
                matched_ip = meraki_row['wan1_ip']
            elif dsr_ip == meraki_row['wan2_ip']:
                wan_port = 'WAN2'
                arin_provider = meraki_row['wan2_arin_provider']
                matched_ip = meraki_row['wan2_ip']
            else:
                # No IP match, try provider matching
                if meraki_row['wan1_arin_provider']:
                    wan1_match = check_provider_match(dsr_provider, meraki_row['wan1_arin_provider'], circuit_purpose, mappings)
                    if wan1_match['confidence'] >= 70:
                        wan_port = 'WAN1'
                        arin_provider = meraki_row['wan1_arin_provider']
                        matched_ip = meraki_row['wan1_ip']
                
                if not wan_port and meraki_row['wan2_arin_provider']:
                    wan2_match = check_provider_match(dsr_provider, meraki_row['wan2_arin_provider'], circuit_purpose, mappings)
                    if wan2_match['confidence'] >= 70:
                        wan_port = 'WAN2'
                        arin_provider = meraki_row['wan2_arin_provider']
                        matched_ip = meraki_row['wan2_ip']
        
        # Get match result
        if arin_provider:
            match_result = check_provider_match(dsr_provider, arin_provider, circuit_purpose, mappings)
        else:
            match_result = {
                'status': 'no_data',
                'confidence': 0,
                'canonical': dsr_provider,
                'reason': 'No ARIN data available'
            }
        
        # Insert into test table
        cursor.execute("""
            INSERT INTO enriched_circuits_test (
                site_id, site_name, circuit_purpose, dsr_provider, arin_provider,
                wan_port, provider_match_status, provider_match_confidence,
                provider_canonical, match_reason, dsr_ip, matched_ip,
                speed, cost, last_updated
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (site_id, circuit_purpose) DO UPDATE SET
                dsr_provider = EXCLUDED.dsr_provider,
                arin_provider = EXCLUDED.arin_provider,
                wan_port = EXCLUDED.wan_port,
                provider_match_status = EXCLUDED.provider_match_status,
                provider_match_confidence = EXCLUDED.provider_match_confidence,
                provider_canonical = EXCLUDED.provider_canonical,
                match_reason = EXCLUDED.match_reason,
                dsr_ip = EXCLUDED.dsr_ip,
                matched_ip = EXCLUDED.matched_ip,
                speed = EXCLUDED.speed,
                cost = EXCLUDED.cost,
                last_updated = EXCLUDED.last_updated
        """, (
            site_id, site_name, circuit_purpose, dsr_provider, arin_provider,
            wan_port, match_result['status'], match_result['confidence'],
            match_result['canonical'], match_result['reason'], dsr_ip, matched_ip,
            speed, cost
        ))
        
        processed += 1
        if match_result['status'] == 'matched':
            matched += 1
        
        if processed % 100 == 0:
            print(f"Processed {processed} circuits...")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\nTest enrichment complete!")
    print(f"Processed: {processed} circuits")
    print(f"Matched: {matched} circuits")
    print(f"Match rate: {matched/processed*100:.1f}%")
    
    return processed, matched

def show_test_statistics():
    """Show statistics from the test enrichment"""
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cursor.execute("SELECT * FROM provider_match_test_statistics")
    stats = cursor.fetchone()
    
    print("\n=== Test Enrichment Statistics ===")
    print(f"Total circuits: {stats['total_circuits']}")
    print(f"Matched: {stats['matched_circuits']}")
    print(f"No match: {stats['no_match_circuits']}")
    print(f"No data: {stats['no_data_circuits']}")
    print(f"Match rate: {stats['match_rate']}%")
    print(f"Average confidence: {stats['avg_match_confidence']}%")
    print(f"Excellent matches (90%+): {stats['excellent_matches']}")
    print(f"Good matches (70-89%): {stats['good_matches']}")
    print(f"Poor matches (<70%): {stats['poor_matches']}")
    
    # Show some examples
    print("\n=== Example Matches ===")
    cursor.execute("""
        SELECT site_name, circuit_purpose, dsr_provider, arin_provider,
               provider_match_status, provider_match_confidence, match_reason
        FROM enriched_circuits_test
        WHERE provider_match_status = 'matched'
        ORDER BY provider_match_confidence DESC
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print(f"{row['site_name']} ({row['circuit_purpose']}): {row['dsr_provider']} → {row['arin_provider']} ({row['provider_match_confidence']}% - {row['match_reason']})")
    
    print("\n=== No Match Examples ===")
    cursor.execute("""
        SELECT site_name, circuit_purpose, dsr_provider, arin_provider, match_reason
        FROM enriched_circuits_test
        WHERE provider_match_status = 'no_match'
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"{row['site_name']} ({row['circuit_purpose']}): {row['dsr_provider']} vs {row['arin_provider']} - {row['match_reason']}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        processed, matched = populate_test_enriched_circuits()
        show_test_statistics()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()