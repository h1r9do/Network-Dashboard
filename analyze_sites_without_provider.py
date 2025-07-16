#!/usr/bin/env python3
"""
Analyze sites without provider information from live data
"""

import json
import os

# Load the data
INPUT_FILE = "/tmp/live_meraki_all_except_55.json"

def is_valid_provider(provider):
    """Check if provider info is valid"""
    if not provider:
        return False
    
    provider_str = str(provider).strip().lower()
    
    # Invalid provider strings
    invalid = ['unknown', 'private ip', 'no ip', '', 'none', 'null']
    if provider_str in invalid:
        return False
    
    # ARIN errors
    if provider_str.startswith('arin error'):
        return False
    
    return True

def main():
    """Analyze sites without provider information"""
    print("🔍 Analyzing Sites Without Provider Information")
    print("=" * 60)
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ File not found: {INPUT_FILE}")
        return
    
    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)
    
    print(f"📊 Total sites analyzed: {len(data)}")
    
    sites_without_provider = []
    sites_with_partial_provider = []
    starlink_sites = []
    cell_sites = []
    
    for site in data:
        network_name = site['network_name']
        wan1 = site['wan1']
        wan2 = site['wan2']
        
        # Check WAN1 provider
        wan1_has_provider = False
        if wan1.get('dsr_match'):
            wan1_has_provider = True
            wan1_provider = wan1['dsr_match']['provider']
        elif is_valid_provider(wan1.get('arin_provider')):
            wan1_has_provider = True
            wan1_provider = wan1['arin_provider']
        else:
            wan1_provider = wan1.get('arin_provider', 'Unknown')
        
        # Check WAN2 provider
        wan2_has_provider = False
        if wan2.get('dsr_match'):
            wan2_has_provider = True
            wan2_provider = wan2['dsr_match']['provider']
        elif is_valid_provider(wan2.get('arin_provider')):
            wan2_has_provider = True
            wan2_provider = wan2['arin_provider']
        else:
            wan2_provider = wan2.get('arin_provider', 'Unknown')
        
        # Categorize sites
        if not wan1_has_provider and not wan2_has_provider:
            sites_without_provider.append({
                'name': network_name,
                'wan1_ip': wan1.get('ip', ''),
                'wan1_arin': wan1.get('arin_provider', ''),
                'wan2_ip': wan2.get('ip', ''),
                'wan2_arin': wan2.get('arin_provider', '')
            })
        elif not wan1_has_provider or not wan2_has_provider:
            sites_with_partial_provider.append({
                'name': network_name,
                'wan1_provider': wan1_provider if wan1_has_provider else 'Unknown',
                'wan2_provider': wan2_provider if wan2_has_provider else 'Unknown'
            })
        
        # Check for Starlink
        if 'starlink' in wan1_provider.lower() or 'spacex' in wan1_provider.lower():
            starlink_sites.append(f"{network_name} (WAN1)")
        if 'starlink' in wan2_provider.lower() or 'spacex' in wan2_provider.lower():
            starlink_sites.append(f"{network_name} (WAN2)")
        
        # Check for Cell
        cell_keywords = ['vzw', 'verizon', 'digi', 'cell', 'inseego']
        if any(keyword in wan1_provider.lower() for keyword in cell_keywords):
            cell_sites.append(f"{network_name} (WAN1: {wan1_provider})")
        if any(keyword in wan2_provider.lower() for keyword in cell_keywords):
            cell_sites.append(f"{network_name} (WAN2: {wan2_provider})")
    
    # Print results
    print(f"\n📊 SUMMARY:")
    print(f"   Sites with no provider info: {len(sites_without_provider)}")
    print(f"   Sites with partial provider info: {len(sites_with_partial_provider)}")
    print(f"   Starlink sites: {len(starlink_sites)}")
    print(f"   Cell provider sites: {len(cell_sites)}")
    
    if sites_without_provider:
        print(f"\n❌ Sites Without Any Provider Information ({len(sites_without_provider)}):")
        for site in sites_without_provider[:20]:  # Show first 20
            print(f"   {site['name']}:")
            print(f"      WAN1: {site['wan1_ip']} → {site['wan1_arin']}")
            print(f"      WAN2: {site['wan2_ip']} → {site['wan2_arin']}")
        if len(sites_without_provider) > 20:
            print(f"   ... and {len(sites_without_provider) - 20} more")
    
    if sites_with_partial_provider:
        print(f"\n⚠️  Sites With Partial Provider Information ({len(sites_with_partial_provider)}):")
        for site in sites_with_partial_provider[:10]:  # Show first 10
            print(f"   {site['name']}: WAN1={site['wan1_provider']}, WAN2={site['wan2_provider']}")
        if len(sites_with_partial_provider) > 10:
            print(f"   ... and {len(sites_with_partial_provider) - 10} more")
    
    if starlink_sites:
        print(f"\n🛰️  Starlink Sites ({len(starlink_sites)}):")
        for site in sorted(set(starlink_sites)):
            print(f"   - {site}")
    
    # Save sites without provider to file
    if sites_without_provider:
        output_file = "/tmp/sites_without_provider.json"
        with open(output_file, 'w') as f:
            json.dump(sites_without_provider, f, indent=2)
        print(f"\n📄 Sites without provider saved to: {output_file}")

if __name__ == "__main__":
    main()