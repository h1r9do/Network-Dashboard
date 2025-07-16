#!/usr/bin/env python3
"""
Simple test of the Frontier matching logic without database connection
"""

import sys
import os

# Import the enhanced functions from the patched enrichment script
sys.path.append('/usr/local/bin/Main/nightly')
from nightly_enriched_db import is_frontier_provider, providers_match_for_sync

def test_frontier_matching():
    """Test the Frontier matching logic"""
    
    print("=== Testing Enhanced Frontier Matching Logic ===\\n")
    
    # Test scenarios matching your failing sites
    test_scenarios = [
        # (ARIN Provider, Circuit Provider, Expected Match, Description)
        ("Frontier Communications", "Frontier", True, "ARIN Frontier Communications vs DB Frontier"),
        ("Frontier Communications", "EB2-Frontier Fiber", True, "ARIN Frontier Communications vs DB EB2-Frontier Fiber"),
        ("Frontier Communications", "Frontier Dedicated", True, "ARIN Frontier Communications vs DB Frontier Dedicated"),
        ("Frontier Communications", "Frontier Fios", True, "ARIN Frontier Communications vs DB Frontier Fios"),
        ("Frontier", "Frontier Communications", True, "ARIN Frontier vs DB Frontier Communications"),
        ("frontier communications", "FRONTIER", True, "Case insensitive test"),
        ("Frontier Communications", "AT&T", False, "Should not match non-Frontier"),
        ("Frontier", "Verizon Business", False, "Should not match non-Frontier"),
    ]
    
    print(f"{'ARIN Provider':<25} {'Circuit Provider':<25} {'Expected':<10} {'Result':<8} {'Status'}")
    print("-" * 85)
    
    all_passed = True
    
    for arin_provider, circuit_provider, expected, description in test_scenarios:
        result = providers_match_for_sync(circuit_provider, arin_provider)  # Note: swapped order to match function signature
        status = "✓ PASS" if result == expected else "✗ FAIL"
        
        if result != expected:
            all_passed = False
        
        print(f"{arin_provider:<25} {circuit_provider:<25} {expected:<10} {result:<8} {status}")
    
    print("\\n=== Testing is_frontier_provider Function ===\\n")
    
    frontier_tests = [
        ("Frontier", True),
        ("Frontier Communications", True),
        ("EB2-Frontier Fiber", True),
        ("Frontier Dedicated", True),
        ("Frontier Fios", True),
        ("frontier", True),  # lowercase
        ("FRONTIER COMMUNICATIONS", True),  # uppercase
        ("AT&T", False),
        ("Verizon Business", False),
        ("Cox Communications", False),
        ("", False),
        (None, False),
    ]
    
    print(f"{'Provider Name':<30} {'Expected':<10} {'Result':<8} {'Status'}")
    print("-" * 60)
    
    for provider, expected in frontier_tests:
        result = is_frontier_provider(provider)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        
        if result != expected:
            all_passed = False
        
        provider_display = str(provider) if provider is not None else "None"
        print(f"{provider_display:<30} {expected:<10} {result:<8} {status}")
    
    print("\\n=== Summary ===")
    if all_passed:
        print("✓ All tests passed! The Frontier fuzzy matching logic is working correctly.")
        print("\\nThis should resolve the matching issues for these sites:")
        print("- CAL 13, CAL 17, CAL 20, CAL 24, CAN 16, CAS 35, CAS 40, CAS 41, CAS 48")
        print("\\nThe enrichment script will now recognize:")
        print("- ARIN 'Frontier Communications' matches circuit 'Frontier'")
        print("- ARIN 'Frontier Communications' matches circuit 'EB2-Frontier Fiber'") 
        print("- ARIN 'Frontier Communications' matches circuit 'Frontier Dedicated'")
        print("- ARIN 'Frontier Communications' matches circuit 'Frontier Fios'")
    else:
        print("✗ Some tests failed. The logic may need adjustment.")

if __name__ == "__main__":
    test_frontier_matching()