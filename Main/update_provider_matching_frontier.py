#!/usr/bin/env python3
"""
Update provider matching logic to handle Frontier variants with fuzzy matching
"""

import sys
import os
sys.path.append('/usr/local/bin/Main')

import re
from thefuzz import fuzz
from thefuzz import process

# Define Frontier provider variants
FRONTIER_VARIANTS = [
    'Frontier',
    'Frontier Communications',
    'Frontier Dedicated',
    'Frontier Fios',
    'Frontier FIOS',
    'EB2-Frontier Fiber',
    'NAM Frontier Fiber',
    'Frontier Fiber',
    'Frontier Communications Corporation',
    'Frontier Communications of America'
]

def is_frontier_provider(provider_name):
    """Check if a provider name is a Frontier variant"""
    if not provider_name:
        return False
    
    provider_lower = provider_name.lower()
    
    # Simple keyword check first
    if 'frontier' in provider_lower:
        return True
    
    # Fuzzy match against known variants
    best_match, score = process.extractOne(
        provider_name,
        FRONTIER_VARIANTS,
        scorer=fuzz.ratio
    )
    
    return score >= 80  # 80% similarity threshold

def normalize_frontier_provider(provider_name):
    """Normalize Frontier provider names to a common format"""
    if not provider_name:
        return provider_name
    
    if is_frontier_provider(provider_name):
        # Find the best matching variant
        best_match, score = process.extractOne(
            provider_name,
            FRONTIER_VARIANTS,
            scorer=fuzz.ratio
        )
        
        # If it's clearly a Frontier variant, return normalized name
        if score >= 80:
            return "Frontier Communications"
    
    return provider_name

def providers_match_enhanced(provider1, provider2):
    """Enhanced provider matching with Frontier fuzzy logic"""
    if not provider1 or not provider2:
        return False
    
    # Exact match
    if provider1.lower() == provider2.lower():
        return True
    
    # Special handling for Frontier
    if is_frontier_provider(provider1) and is_frontier_provider(provider2):
        return True
    
    # General fuzzy matching
    return fuzz.ratio(provider1.lower(), provider2.lower()) >= 85

def test_frontier_matching():
    """Test the Frontier matching logic"""
    test_cases = [
        # (ARIN provider, Circuit provider, Expected result)
        ("Frontier Communications", "Frontier", True),
        ("Frontier Communications", "Frontier Dedicated", True),
        ("Frontier Communications", "Frontier Fios", True),
        ("Frontier Communications", "EB2-Frontier Fiber", True),
        ("Frontier", "Frontier Communications", True),
        ("Frontier", "NAM Frontier Fiber", True),
        ("Frontier Communications", "AT&T", False),
        ("Frontier", "Verizon", False),
    ]
    
    print("=== Testing Frontier Provider Matching ===\n")
    
    for arin_provider, circuit_provider, expected in test_cases:
        result = providers_match_enhanced(arin_provider, circuit_provider)
        status = "✓" if result == expected else "✗"
        print(f"{status} ARIN: '{arin_provider}' vs Circuit: '{circuit_provider}' → {result}")
    
    print("\n=== Testing is_frontier_provider ===\n")
    
    frontier_tests = [
        "Frontier",
        "Frontier Communications",
        "EB2-Frontier Fiber",
        "frontier dedicated",  # lowercase
        "FRONTIER FIOS",  # uppercase
        "AT&T",  # not frontier
        "Verizon"  # not frontier
    ]
    
    for provider in frontier_tests:
        result = is_frontier_provider(provider)
        print(f"'{provider}' → is Frontier: {result}")

def show_implementation_for_enrichment():
    """Show how to integrate this into nightly_enriched_db.py"""
    
    print("\n\n=== Implementation for nightly_enriched_db.py ===\n")
    
    implementation = '''
# Add to imports at top of file:
from thefuzz import fuzz

# Add Frontier variants list:
FRONTIER_VARIANTS = [
    'Frontier', 'Frontier Communications', 'Frontier Dedicated',
    'Frontier Fios', 'Frontier FIOS', 'EB2-Frontier Fiber',
    'NAM Frontier Fiber', 'Frontier Fiber'
]

# Add helper function:
def is_frontier_provider(provider_name):
    """Check if a provider name is a Frontier variant"""
    if not provider_name:
        return False
    return 'frontier' in provider_name.lower()

# Update providers_match_for_sync function:
def providers_match_for_sync(dsr_provider, meraki_provider):
    """Enhanced provider matching with Frontier fuzzy logic"""
    if not dsr_provider or not meraki_provider:
        return False
    
    # Normalize providers
    dsr_norm = normalize_provider(dsr_provider)
    meraki_norm = normalize_provider(meraki_provider)
    
    # Exact match after normalization
    if dsr_norm.lower() == meraki_norm.lower():
        return True
    
    # Special handling for Frontier variants
    if is_frontier_provider(dsr_norm) and is_frontier_provider(meraki_norm):
        logger.debug(f"Frontier match: '{dsr_provider}' matches '{meraki_provider}'")
        return True
    
    # Fuzzy matching with high threshold
    similarity = fuzz.ratio(dsr_norm.lower(), meraki_norm.lower())
    
    if similarity >= 85:
        logger.debug(f"Fuzzy match ({similarity}%): '{dsr_provider}' ~ '{meraki_provider}'")
        return True
    
    return False

# Also add to the enrichment logic where ARIN = Device Notes:
# Around line 640, add this check:
if wan1_comparison == "Match" and wan1_notes == wan1_arin:
    # When ARIN and device notes agree, look for any matching provider
    # This handles the case where both show "Frontier Communications"
    # but DSR has a variant like "Frontier Dedicated"
    for circuit in dsr_circuits:
        if is_frontier_provider(wan1_arin) and is_frontier_provider(circuit['provider']):
            wan1_dsr = circuit
            logger.info(f"{network_name}: Frontier variant match - ARIN/Notes: {wan1_arin} → DSR: {circuit['provider']}")
            break
'''
    
    print(implementation)

if __name__ == "__main__":
    # Run tests
    test_frontier_matching()
    
    # Show implementation
    show_implementation_for_enrichment()