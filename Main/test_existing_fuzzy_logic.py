#!/usr/bin/env python3
"""
Test the existing fuzzy matching logic to see why Frontier isn't matching
"""

import sys
import os
sys.path.append('/usr/local/bin/Main/nightly')

from thefuzz import fuzz

def test_frontier_fuzzy_scores():
    """Test fuzzy scores for Frontier variants"""
    
    print("=== Testing Existing Fuzzy Logic for Frontier ===\n")
    
    # Test cases from the failing sites
    test_cases = [
        ("Frontier Communications", "Frontier"),
        ("Frontier Communications", "EB2-Frontier Fiber"),
        ("Frontier Communications", "Frontier Dedicated"),
        ("Frontier Communications", "Frontier Fios"),
        ("Frontier Communications", "NAM Frontier Fiber"),
    ]
    
    print(f"{'ARIN Provider':<25} {'Circuit Provider':<25} {'Ratio':<8} {'Partial':<8} {'Max':<8} {'Pass 60%':<10} {'Pass 80%'}")
    print("-" * 100)
    
    for arin, circuit in test_cases:
        ratio_score = fuzz.ratio(arin.lower(), circuit.lower())
        partial_score = fuzz.partial_ratio(arin.lower(), circuit.lower())
        max_score = max(ratio_score, partial_score)
        
        pass_60 = "✓" if max_score > 60 else "✗"
        pass_80 = "✓" if max_score >= 80 else "✗"
        
        print(f"{arin:<25} {circuit:<25} {ratio_score:<8} {partial_score:<8} {max_score:<8} {pass_60:<10} {pass_80}")
    
    print("\n=== Testing Normalization Impact ===\n")
    
    # Test with provider normalization (simulate what the enrichment script does)
    def normalize_provider_for_comparison(provider):
        """Simulate the normalization from enrichment script"""
        if not provider:
            return ""
        provider_lower = provider.lower().strip()
        # Remove common prefixes/suffixes  
        import re
        provider_clean = re.sub(
            r'^\\s*(?:dsr|agg|comcastagg|clink|not\\s*dsr|--|-)\\s+|\\s*(?:extended\\s+cable|dsl|fiber|adi|workpace)\\s*',
            '', provider_lower, flags=re.IGNORECASE
        ).strip()
        return provider_clean
    
    print(f"{'Original ARIN':<25} {'Original Circuit':<25} {'Normalized ARIN':<25} {'Normalized Circuit':<25} {'Score':<8}")
    print("-" * 120)
    
    for arin, circuit in test_cases:
        norm_arin = normalize_provider_for_comparison(arin)
        norm_circuit = normalize_provider_for_comparison(circuit)
        score = max(
            fuzz.ratio(norm_arin, norm_circuit),
            fuzz.partial_ratio(norm_arin, norm_circuit)
        )
        
        print(f"{arin:<25} {circuit:<25} {norm_arin:<25} {norm_circuit:<25} {score:<8}")

if __name__ == "__main__":
    test_frontier_fuzzy_scores()