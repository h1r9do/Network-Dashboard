#!/usr/bin/env python3
"""
Test Notes Update - Test on 5 sites first
"""

import os
import sys
import json
from push_corrected_notes_to_meraki import format_circuit_notes, get_organization_id, get_networks

def test_notes_formatting():
    """Test the notes formatting function"""
    print("🔧 Testing notes formatting...")
    
    # Test case 1: Both WAN1 and WAN2 with providers and speeds
    wan1_data = {'provider': 'Sparklight', 'speed': '300.0M x 30.0M'}
    wan2_data = {'provider': 'Digi', 'speed': 'Cell'}
    result = format_circuit_notes(wan1_data, wan2_data)
    print(f"Test 1 - Full data:")
    print(f"  Input: WAN1={wan1_data}, WAN2={wan2_data}")
    print(f"  Output: {repr(result)}")
    print()
    
    # Test case 2: WAN1 only
    wan1_data = {'provider': 'AT&T Broadband II', 'speed': '200.0M x 200.0M'}
    wan2_data = {'provider': '', 'speed': ''}
    result = format_circuit_notes(wan1_data, wan2_data)
    print(f"Test 2 - WAN1 only:")
    print(f"  Input: WAN1={wan1_data}, WAN2={wan2_data}")
    print(f"  Output: {repr(result)}")
    print()
    
    # Test case 3: Provider without speed
    wan1_data = {'provider': 'Spectrum', 'speed': ''}
    wan2_data = {'provider': 'VZW Cell', 'speed': ''}
    result = format_circuit_notes(wan1_data, wan2_data)
    print(f"Test 3 - Providers only:")
    print(f"  Input: WAN1={wan1_data}, WAN2={wan2_data}")
    print(f"  Output: {repr(result)}")
    print()

def test_api_connection():
    """Test Meraki API connection"""
    print("🔗 Testing Meraki API connection...")
    
    org_id = get_organization_id()
    if org_id:
        print(f"  ✅ Successfully connected to organization: {org_id}")
        
        networks = get_networks(org_id)
        print(f"  ✅ Found {len(networks)} networks")
        
        # Show a few network names
        sample_networks = [net['name'] for net in networks[:5]]
        print(f"  📊 Sample networks: {sample_networks}")
        return True
    else:
        print("  ❌ Failed to connect to Meraki API")
        return False

def show_sample_enriched_data():
    """Show sample data from enriched JSON"""
    enriched_file = "/tmp/enriched_from_may2nd.json"
    
    if not os.path.exists(enriched_file):
        print(f"❌ Enriched file not found: {enriched_file}")
        return
    
    print("📊 Sample enriched data:")
    with open(enriched_file, 'r') as f:
        data = json.load(f)
    
    print(f"  Total sites: {len(data)}")
    
    # Show first 3 sites
    for i, site in enumerate(data[:3]):
        network_name = site.get('network_name', 'Unknown')
        wan1 = site.get('wan1', {})
        wan2 = site.get('wan2', {})
        print(f"  Site {i+1}: {network_name}")
        print(f"    WAN1: {wan1.get('provider', 'empty')} - {wan1.get('speed', 'empty')}")
        print(f"    WAN2: {wan2.get('provider', 'empty')} - {wan2.get('speed', 'empty')}")
        print(f"    Formatted notes: {repr(format_circuit_notes(wan1, wan2))}")
        print()

def main():
    print("🧪 Testing Meraki Notes Update Components")
    print("=" * 60)
    
    # Test 1: Notes formatting
    test_notes_formatting()
    
    # Test 2: API connection
    if test_api_connection():
        print("✅ API connection test passed")
    else:
        print("❌ API connection test failed")
        return
    
    # Test 3: Sample data
    show_sample_enriched_data()
    
    print("=" * 60)
    print("🎯 All tests completed. Ready to run full update if tests look good.")

if __name__ == "__main__":
    main()