#!/usr/bin/env python3
"""Test ARIN lookups for Discount-Tire tagged networks against meraki live JSON"""

import sys
import json
import requests
import time
import ipaddress
from datetime import datetime

sys.path.insert(0, '/usr/local/bin/Main')
from nightly_meraki_db import parse_arin_response, get_db_connection, KNOWN_IPS

def compare_providers(provider1, provider2):
    """Simple provider comparison"""
    if not provider1 or not provider2:
        return "Mismatch"
        
    if provider1.lower() == provider2.lower():
        return "Match"
    
    # Normalize common variations
    p1 = provider1.lower().replace(' ', '').replace(',', '').replace('.', '').replace('inc', '').replace('llc', '')
    p2 = provider2.lower().replace(' ', '').replace(',', '').replace('.', '').replace('inc', '').replace('llc', '')
    
    # Check if one contains the other
    if p1 in p2 or p2 in p1:
        return "Match"
    
    # Known equivalents
    equivalents = {
        'att': ['at&t', 'att', 'atandt', 'atminternet'],
        'charter': ['charter', 'spectrum', 'chartercommunications'],
        'verizon': ['verizon', 'vzw', 'verizonbusiness'],
        'centurylink': ['centurylink', 'lumen', 'level3', 'qwest'],
        'comcast': ['comcast', 'xfinity']
    }
    
    for group, variants in equivalents.items():
        if any(v in p1 for v in variants) and any(v in p2 for v in variants):
            return "Match"
    
    return "Mismatch"

# Load the meraki live JSON
json_file = '/var/www/html/meraki-data/mx_inventory_live.json'
with open(json_file, 'r') as f:
    meraki_data = json.load(f)

# Filter for Discount-Tire tagged networks
discount_tire_networks = []
for device in meraki_data:
    if device.get('device_tags') and 'Discount-Tire' in device.get('device_tags', []):
        discount_tire_networks.append(device)

# Take first 10 for quick test
test_networks = discount_tire_networks[:10]
print(f"Found {len(discount_tire_networks)} Discount-Tire tagged networks")
print(f"Testing first {len(test_networks)} networks\n")

# Test results
results = []
matches = 0
mismatches = 0
no_ip_count = 0

for device in test_networks:
    network_name = device.get('network_name', 'Unknown')
    print(f"\nTesting: {network_name}")
    print("-" * 60)
    
    # Get IPs from device
    wan1_ip = device.get('wan1', {}).get('ip', '')
    wan1_arin_from_json = device.get('wan1', {}).get('provider', '')
    wan2_ip = device.get('wan2', {}).get('ip', '')
    wan2_arin_from_json = device.get('wan2', {}).get('provider', '')
    
    # Test WAN1
    wan1_result = {'ip': wan1_ip, 'json_provider': wan1_arin_from_json, 'new_provider': ''}
    if wan1_ip:
        try:
            # Check if private IP
            ip_obj = ipaddress.ip_address(wan1_ip)
            if ip_obj.is_private:
                wan1_result['new_provider'] = 'Unknown'
                print(f"  WAN1: {wan1_ip} (Private IP)")
            elif wan1_ip in KNOWN_IPS:
                wan1_result['new_provider'] = KNOWN_IPS[wan1_ip]
                print(f"  WAN1: {wan1_ip} -> {KNOWN_IPS[wan1_ip]} (from KNOWN_IPS)")
            else:
                # Query ARIN
                rdap_url = f"https://rdap.arin.net/registry/ip/{wan1_ip}"
                response = requests.get(rdap_url, timeout=10)
                if response.status_code == 200:
                    rdap_data = response.json()
                    provider = parse_arin_response(rdap_data)
                    wan1_result['new_provider'] = provider
                    print(f"  WAN1: {wan1_ip} -> {provider}")
                else:
                    wan1_result['new_provider'] = 'Unknown'
                    print(f"  WAN1: {wan1_ip} -> Error: {response.status_code}")
                time.sleep(0.5)  # Rate limit
        except Exception as e:
            wan1_result['new_provider'] = 'Error'
            print(f"  WAN1: {wan1_ip} -> Error: {e}")
    else:
        no_ip_count += 1
        print(f"  WAN1: No IP")
    
    # Test WAN2
    wan2_result = {'ip': wan2_ip, 'json_provider': wan2_arin_from_json, 'new_provider': ''}
    if wan2_ip:
        try:
            # Check if private IP
            ip_obj = ipaddress.ip_address(wan2_ip)
            if ip_obj.is_private:
                wan2_result['new_provider'] = 'Unknown'
                print(f"  WAN2: {wan2_ip} (Private IP)")
            elif wan2_ip in KNOWN_IPS:
                wan2_result['new_provider'] = KNOWN_IPS[wan2_ip]
                print(f"  WAN2: {wan2_ip} -> {KNOWN_IPS[wan2_ip]} (from KNOWN_IPS)")
            else:
                # Query ARIN
                rdap_url = f"https://rdap.arin.net/registry/ip/{wan2_ip}"
                response = requests.get(rdap_url, timeout=10)
                if response.status_code == 200:
                    rdap_data = response.json()
                    provider = parse_arin_response(rdap_data)
                    wan2_result['new_provider'] = provider
                    print(f"  WAN2: {wan2_ip} -> {provider}")
                else:
                    wan2_result['new_provider'] = 'Unknown'
                    print(f"  WAN2: {wan2_ip} -> Error: {response.status_code}")
                time.sleep(0.5)  # Rate limit
        except Exception as e:
            wan2_result['new_provider'] = 'Error'
            print(f"  WAN2: {wan2_ip} -> Error: {e}")
    else:
        no_ip_count += 1
        print(f"  WAN2: No IP")
    
    # Compare results
    print(f"\n  Comparison:")
    if wan1_ip:
        json_provider = wan1_arin_from_json or 'None'
        new_provider = wan1_result['new_provider']
        match = compare_providers(json_provider, new_provider)
        print(f"    WAN1: JSON='{json_provider}' vs NEW='{new_provider}' -> {match}")
        if match == "Match":
            matches += 1
        else:
            mismatches += 1
    
    if wan2_ip:
        json_provider = wan2_arin_from_json or 'None'
        new_provider = wan2_result['new_provider']
        match = compare_providers(json_provider, new_provider)
        print(f"    WAN2: JSON='{json_provider}' vs NEW='{new_provider}' -> {match}")
        if match == "Match":
            matches += 1
        else:
            mismatches += 1
    
    results.append({
        'network': network_name,
        'wan1': wan1_result,
        'wan2': wan2_result
    })

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Networks tested: {len(test_networks)}")
print(f"Total comparisons: {matches + mismatches}")
print(f"Matches: {matches}")
print(f"Mismatches: {mismatches}")
print(f"No IP addresses: {no_ip_count}")
if matches + mismatches > 0:
    print(f"Match rate: {matches / (matches + mismatches) * 100:.1f}%")

# Save detailed results
output_file = '/tmp/arin_test_results.json'
with open(output_file, 'w') as f:
    json.dump({
        'test_date': datetime.now().isoformat(),
        'networks_tested': len(test_networks),
        'matches': matches,
        'mismatches': mismatches,
        'no_ip_count': no_ip_count,
        'results': results
    }, f, indent=2)

print(f"\nDetailed results saved to: {output_file}")