#!/usr/bin/env python3
"""
Test specific provider matching cases to demonstrate the solution
"""

from enhanced_provider_matching import EnhancedProviderMatcher

def test_specific_cases():
    """Test specific provider matching cases"""
    
    # Create matcher instance (assumes mapping table exists)
    matcher = EnhancedProviderMatcher()
    
    # Test cases from our analysis
    test_cases = [
        # Rebrand cases
        ("Brightspeed", "CenturyLink", "Should match - rebrand"),
        ("Sparklight", "Cable One, Inc.", "Should match - rebrand"),
        
        # EB2- prefix cases
        ("EB2-CenturyLink DSL", "CenturyLink", "Should match - EB2 prefix"),
        ("EB2-Lumen DSL", "CenturyLink", "Should match - EB2/Lumen to CenturyLink"),
        ("EB2-Frontier Fiber", "Frontier Communications", "Should match - EB2 prefix"),
        
        # Business divisions
        ("Comcast Workplace", "Comcast", "Should match - business division"),
        ("Cox Business/BOI", "Cox Communications", "Should match - business division"),
        ("AT&T Broadband II", "AT&T", "Should match - service tier"),
        
        # Tricky cases
        ("TransWorld", "FAIRNET LLC", "Should match - DBA"),
        ("Lightpath", "Optimum", "Should match - Altice division"),
        ("CenturyLink Fiber Plus", "Cox Communications", "Should NOT match - different companies"),
        
        # Direct matches
        ("AT&T", "AT&T", "Should match - direct"),
        ("Spectrum", "Charter Communications", "Should match - brand name"),
    ]
    
    print("=== Testing Specific Provider Matching Cases ===\n")
    print(f"{'DSR Provider':<30} {'ARIN Provider':<30} {'Status':<15} {'Score':<6} {'Expected':<25}")
    print("-" * 110)
    
    for dsr, arin, expected in test_cases:
        status, score, reason = matcher.enhanced_match_providers(dsr, arin)
        
        # Determine if result matches expectation
        if "NOT match" in expected and status != "Match":
            result_icon = "✅"
        elif "Should match" in expected and status == "Match":
            result_icon = "✅"
        else:
            result_icon = "❌"
        
        print(f"{dsr:<30} {arin:<30} {status:<15} {score:<6} {result_icon} {expected:<23}")
    
    print("\n=== Matching Statistics ===")
    for key, value in matcher.stats.items():
        if value > 0:
            print(f"{key}: {value}")

if __name__ == "__main__":
    # Note: This assumes the mapping table has been created
    print("Note: This test assumes the provider_mappings table exists.")
    print("Run ./apply_provider_mappings.py first if needed.\n")
    
    test_specific_cases()