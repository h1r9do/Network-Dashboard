#!/usr/bin/env python3
"""
Test the enhanced Frontier matching logic on the failing sites
"""

import sys
import os
sys.path.append('/usr/local/bin/Main')

import psycopg2
import psycopg2.extras
from config import Config
import re

# Import the enhanced functions from the patched enrichment script
sys.path.append('/usr/local/bin/Main/nightly')
from nightly_enriched_db import is_frontier_provider, providers_match_for_sync, normalize_provider_for_arin_match

def get_db_connection():
    """Get database connection using SQLAlchemy URI"""
    from sqlalchemy import create_engine
    from sqlalchemy.pool import NullPool
    
    # Use SQLAlchemy to parse the URI
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, poolclass=NullPool)
    
    # Extract connection parameters from the engine
    url = engine.url
    
    return psycopg2.connect(
        host=url.host,
        port=url.port,
        database=url.database,
        user=url.username,
        password=url.password
    )

def test_frontier_sites():
    """Test the Frontier matching logic on the failing sites"""
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=== Testing Enhanced Frontier Matching ===\\n")
    
    # Test sites - the ones that were failing before
    test_sites = ['CAL 13', 'CAL 17', 'CAL 20', 'CAL 24', 'CAN 16', 'CAS 35', 'CAS 40', 'CAS 41', 'CAS 48']
    
    # Get circuits for these sites
    circuit_query = """
        SELECT site_name, provider_name, data_source, status, circuit_purpose,
               details_ordered_service_speed, billing_monthly_cost
        FROM circuits
        WHERE site_name = ANY(%s)
        AND status = 'Enabled'
        ORDER BY site_name, circuit_purpose
    """
    
    cursor.execute(circuit_query, (test_sites,))
    circuits_by_site = {}
    
    for row in cursor.fetchall():
        site = row['site_name']
        if site not in circuits_by_site:
            circuits_by_site[site] = []
        circuits_by_site[site].append({
            'provider': row['provider_name'],
            'data_source': row['data_source'],
            'purpose': row['circuit_purpose'],
            'speed': row['details_ordered_service_speed'],
            'cost': row['billing_monthly_cost']
        })
    
    # Simulate the test scenarios
    test_scenarios = [
        # Format: (site, arin_provider, notes_provider, expected_match)
        ("CAL 13", "Frontier Communications", "Frontier Communications", True),
        ("CAL 17", "Frontier Communications", "Frontier Communications", True),
        ("CAL 20", "Frontier Communications", "Frontier Communications", True),
        ("CAL 24", "Frontier Communications", "Frontier Communications", True),
        ("CAN 16", "Frontier Communications", "Frontier Communications", True),
        ("CAS 35", "Frontier Communications", "Frontier Communications", True),
        ("CAS 40", "Frontier Communications", "Frontier Communications", True),
        ("CAS 41", "Frontier Communications", "Frontier Communications", True),
        ("CAS 48", "Frontier Communications", "Frontier Communications", True),
    ]
    
    print(f"{'Site':<8} {'ARIN Provider':<22} {'Notes Provider':<22} {'Circuit Providers':<30} {'Match Found':<12}")
    print("-" * 100)
    
    for site, arin_provider, notes_provider, expected in test_scenarios:
        circuits = circuits_by_site.get(site, [])
        circuit_providers = [c['provider'] for c in circuits]
        
        # Test the enhanced matching logic
        match_found = False
        matched_provider = None
        
        # Test 1: Direct provider matching
        for circuit in circuits:
            if providers_match_for_sync(circuit['provider'], arin_provider):
                match_found = True
                matched_provider = circuit['provider']
                break
        
        # Test 2: ARIN = Notes logic
        if not match_found and arin_provider.lower().strip() == notes_provider.lower().strip():
            for circuit in circuits:
                if providers_match_for_sync(circuit['provider'], arin_provider):
                    match_found = True
                    matched_provider = circuit['provider']
                    break
        
        status = "✓" if match_found else "✗"
        circuit_list = ", ".join(circuit_providers) if circuit_providers else "None"
        matched_info = f"→ {matched_provider}" if matched_provider else ""
        
        print(f"{site:<8} {arin_provider:<22} {notes_provider:<22} {circuit_list:<30} {status} {matched_info}")
    
    print("\\n=== Testing Specific Frontier Variants ===\\n")
    
    # Test specific provider combinations
    variant_tests = [
        ("Frontier Communications", "Frontier", True),
        ("Frontier Communications", "EB2-Frontier Fiber", True),
        ("Frontier", "Frontier Dedicated", True),
        ("Frontier", "Frontier Fios", True),
        ("frontier communications", "FRONTIER", True),  # case insensitive
        ("Frontier Communications", "AT&T", False),
        ("Frontier", "Verizon", False),
    ]
    
    print(f"{'ARIN Provider':<25} {'Circuit Provider':<25} {'Match':<8} {'Method'}")
    print("-" * 70)
    
    for arin, circuit, expected in variant_tests:
        is_frontier_match = is_frontier_provider(arin) and is_frontier_provider(circuit)
        direct_match = providers_match_for_sync(arin, circuit)
        
        method = ""
        if direct_match:
            if is_frontier_match:
                method = "Frontier"
            else:
                method = "Direct"
        
        status = "✓" if direct_match == expected else "✗"
        print(f"{arin:<25} {circuit:<25} {status:<8} {method}")
    
    conn.close()

if __name__ == "__main__":
    test_frontier_sites()