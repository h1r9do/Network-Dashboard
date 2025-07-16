#!/usr/bin/env python3
"""
Test the DDNS enhancement patch functionality
"""

import sys
sys.path.append('/usr/local/bin/Main')

from ddns_enhancement_patch import get_provider_for_ip_enhanced

def test_ddns_enhanced_lookup():
    """Test the enhanced DDNS provider lookup functionality"""
    print("Testing DDNS Enhanced Provider Lookup")
    print("=" * 50)
    
    cache = {}
    missing_set = set()
    
    # Test case 1: Public IP (should work normally)
    print("Test 1: Public IP lookup")
    provider = get_provider_for_ip_enhanced("8.8.8.8", cache, missing_set)
    print(f"  8.8.8.8 -> {provider}")
    print()
    
    # Test case 2: Private IP without DDNS (should return "Private IP")
    print("Test 2: Private IP without DDNS")
    provider = get_provider_for_ip_enhanced("192.168.1.100", cache, missing_set)
    print(f"  192.168.1.100 -> {provider}")
    print()
    
    # Test case 3: Private IP with DDNS (ALN 01 example)
    print("Test 3: Private IP with DDNS (ALN 01)")
    provider = get_provider_for_ip_enhanced(
        "192.168.2.118",  # Private IP from ALN 01
        cache, missing_set,
        network_name="ALN 01",
        wan_number=2,
        network_id="L_650207196201636735"  # ALN 01 network ID
    )
    print(f"  192.168.2.118 (ALN 01 WAN2) -> {provider}")
    print()
    
    # Test case 4: Private IP with DDNS (ALB 03 example)
    print("Test 4: Private IP with DDNS (ALB 03)")
    provider = get_provider_for_ip_enhanced(
        "192.168.0.151",  # Private IP from ALB 03
        cache, missing_set,
        network_name="ALB 03",
        wan_number=2,
        network_id="L_650207196201636610"  # Need to get actual ALB 03 network ID
    )
    print(f"  192.168.0.151 (ALB 03 WAN2) -> {provider}")
    print()
    
    print("Cache contents:")
    for ip, prov in cache.items():
        print(f"  {ip} -> {prov}")
    
    if missing_set:
        print(f"\nMissing IPs: {missing_set}")

if __name__ == "__main__":
    test_ddns_enhanced_lookup()