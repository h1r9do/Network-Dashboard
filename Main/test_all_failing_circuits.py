#!/usr/bin/env python3
"""
Test the improved fuzzy matching logic against all failing circuits
"""

import sys
import os
sys.path.append('/usr/local/bin/Main/nightly')

from thefuzz import fuzz

def test_all_failing_matches():
    """Test fuzzy matching for all the failing circuits from the original analysis"""
    
    print("=== Testing Improved Fuzzy Matching Against All Failing Circuits ===\n")
    
    # These are the failing matches from your original data
    # Format: (Site, WAN1 Notes Provider, WAN1 ARIN Provider, WAN2 Notes Provider, WAN2 ARIN Provider, DSR Count)
    failing_sites = [
        # Frontier sites
        ("CAL 13", "Frontier Communications", "Frontier Communications", "Digi", "AT&T", 1),
        ("CAL 17", "Frontier Communications", "Frontier Communications", "VZW Cell", "Verizon", 1),
        ("CAL 20", "Frontier Communications", "Frontier Communications", "VZW Cell", "Verizon", 1),
        ("CAL 24", "Frontier Communications", "Frontier Communications", "Verizon Business", "Verizon", 2),
        ("CAN 16", "Frontier Communications", "Frontier Communications", "Digi", "AT&T", 1),
        ("CAS 35", "Frontier Communications", "Frontier Communications", "VZW Cell", "Verizon", 1),
        ("CAS 40", "Frontier Communications", "Frontier Communications", "Digi", "AT&T", 1),
        ("CAS 41", "Frontier Communications", "Frontier Communications", "VZW Cell", "Verizon", 1),
        ("CAS 48", "Frontier Communications", "Frontier Communications", "Verizon Business", "Verizon", 1),
        
        # Other failing sites from your 6% analysis
        ("ALB 03", "Digi", "AT&T", "", "", 1),  # No WAN2
        ("CAL 35", "CableOne", "Cable One", "Digi", "AT&T", 1),
        ("CAS 13", "", "", "", "", 0),  # No IP addresses
        ("CAS 32", "Cox Business", "Cox Communications", "Digi", "AT&T", 1),
        ("FLO 21", "Starlink", "SpaceX", "", "", 1),
        ("GAA 41", "Starlink", "SpaceX", "", "", 1),
        ("IAI 11", "Mediacom", "Mediacom Communications", "Digi", "AT&T", 1),
        ("IDL 03", "CableOne", "Cable One", "Digi", "AT&T", 1),
        ("INW 31", "Altice", "Optimum", "VZW Digi", "Verizon", 1),
        ("KSC 01", "Cox Business", "Cox Communications", "VZW Digi", "Verizon", 1),
        ("MNG 11", "VZW Digi", "Verizon", "", "", 1),
        ("MSG 06", "Cox Business", "Cox Communications", "AT&T", "AT&T", 1),
        ("MTB 06", "Starlink", "SpaceX", "", "", 1),
        ("NJB 05", "Cox Business", "Cox Communications", "VZW Digi", "Verizon", 1),
        ("NMR 04", "Brightspeed", "CenturyLink", "VZW Digi", "Verizon", 1),
        ("NVL 13", "Cox", "Cox Communications", "VZW Cell", "Verizon", 1),
        ("OHC 08", "Charter Communications", "Charter Communications", "VZW Cell", "Verizon", 1),
        ("ORC 05", "Cox Business", "Cox Communications", "VZW Cell", "Verizon", 1),
        ("TNC 09", "Cox", "Cox Communications", "Digi", "AT&T", 1),
        ("TNN 12", "AT&T", "AT&T", "VZW Digi", "Verizon", 1),
        ("TXD 76", "Verizon", "Verizon", "VZW Digi", "Verizon", 2),
        ("TXL 19", "ATT Fixed Wireless", "AT&T", "VZW Digi", "Verizon", 1),
        ("UTL 02", "CableOne", "Cable One", "VZW Cell", "Verizon", 1),
        ("WAK 03", "CableOne", "Cable One", "Digi", "AT&T", 1),
        ("WAP 10", "Starlink", "SpaceX", "", "", 1),
    ]
    
    # Test provider pairs and their fuzzy scores
    provider_pairs = set()
    for site, wan1_notes, wan1_arin, wan2_notes, wan2_arin, _ in failing_sites:
        if wan1_notes and wan1_arin:
            provider_pairs.add((wan1_notes, wan1_arin))
        if wan2_notes and wan2_arin:
            provider_pairs.add((wan2_notes, wan2_arin))
    
    print("=== Provider Matching Analysis ===\n")
    print(f"{'Notes Provider':<25} {'ARIN Provider':<25} {'Ratio':<8} {'Partial':<8} {'Token':<8} {'Max':<8} {'Match?'}")
    print("-" * 100)
    
    matches_found = 0
    total_pairs = 0
    
    for notes_provider, arin_provider in sorted(provider_pairs):
        if not notes_provider or not arin_provider:
            continue
            
        total_pairs += 1
        
        # Calculate different fuzzy scores
        ratio_score = fuzz.ratio(notes_provider.lower(), arin_provider.lower())
        partial_score = fuzz.partial_ratio(notes_provider.lower(), arin_provider.lower())
        token_score = fuzz.token_sort_ratio(notes_provider.lower(), arin_provider.lower())
        max_score = max(ratio_score, partial_score, token_score)
        
        # Check if they match with 70% threshold
        matches = max_score > 70
        if matches:
            matches_found += 1
        
        status = "✓" if matches else "✗"
        
        print(f"{notes_provider:<25} {arin_provider:<25} {ratio_score:<8} {partial_score:<8} {token_score:<8} {max_score:<8} {status}")
    
    print(f"\n=== Summary ===")
    print(f"Total provider pairs tested: {total_pairs}")
    print(f"Matches found (>70% similarity): {matches_found}")
    print(f"Match rate: {matches_found/total_pairs*100:.1f}%")
    
    # Analyze specific problematic matches
    print("\n=== Specific Problem Cases ===\n")
    
    problem_cases = [
        ("CableOne", "Cable One"),
        ("Cox Business", "Cox Communications"),
        ("Altice", "Optimum"),
        ("Brightspeed", "CenturyLink"),
        ("ATT Fixed Wireless", "AT&T"),
        ("VZW Digi", "Verizon"),
        ("VZW Cell", "Verizon"),
        ("Digi", "AT&T"),
        ("Starlink", "SpaceX"),
    ]
    
    print(f"{'Case':<30} {'Score':<8} {'Needs Mapping?'}")
    print("-" * 55)
    
    for notes, arin in problem_cases:
        ratio_score = fuzz.ratio(notes.lower(), arin.lower())
        partial_score = fuzz.partial_ratio(notes.lower(), arin.lower())
        token_score = fuzz.token_sort_ratio(notes.lower(), arin.lower())
        max_score = max(ratio_score, partial_score, token_score)
        
        needs_mapping = max_score <= 70
        status = "Yes - Add to PROVIDER_MAPPING" if needs_mapping else "No - Fuzzy match works"
        
        print(f"{notes} → {arin:<20} {max_score:<8} {status}")

if __name__ == "__main__":
    test_all_failing_matches()