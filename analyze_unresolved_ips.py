#!/usr/bin/env python3
"""
Analyze patterns in unresolved ARIN IPs
"""

import json
import ipaddress
from collections import defaultdict, Counter

def analyze_unresolved_ips():
    # Load the JSON file
    with open('/usr/local/bin/unresolved_arin_ips.json', 'r') as f:
        data = json.load(f)
    
    print("=== UNRESOLVED ARIN IPS ANALYSIS ===\n")
    
    # Overall statistics
    stats = data['statistics']
    print("Overall Statistics:")
    print(f"  Total IPs: {stats['total_ips_found']}")
    print(f"  Resolved: {stats['resolved_ips']} ({stats['resolution_rate']})")
    print(f"  Unresolved: {stats['unresolved_ips']}")
    print(f"  Unique unresolved IPs: {stats['unique_unresolved_ips']}\n")
    
    # Analyze by interface
    interface_count = Counter()
    for item in data['unresolved_ips_by_site']:
        interface_count[item['interface']] += 1
    
    print("By Interface:")
    for interface, count in interface_count.items():
        percent = (count / len(data['unresolved_ips_by_site'])) * 100
        print(f"  {interface}: {count} ({percent:.1f}%)")
    print()
    
    # Analyze by IP prefix (first octet)
    prefix_count = defaultdict(int)
    prefix_samples = defaultdict(list)
    
    unique_ips = data['unique_unresolved_ips']
    for ip, sites in unique_ips.items():
        first_octet = ip.split('.')[0]
        prefix_count[first_octet] += 1
        if len(prefix_samples[first_octet]) < 3:
            prefix_samples[first_octet].append(ip)
    
    print("By IP Prefix (First Octet):")
    sorted_prefixes = sorted(prefix_count.items(), key=lambda x: x[1], reverse=True)
    for prefix, count in sorted_prefixes[:15]:
        percent = (count / len(unique_ips)) * 100
        print(f"  {prefix}.x.x.x: {count} IPs ({percent:.1f}%)")
        print(f"    Examples: {', '.join(prefix_samples[prefix])}")
    
    # Analyze by /8 network blocks
    print("\nBy Major Network Blocks:")
    network_blocks = defaultdict(list)
    
    for ip in unique_ips.keys():
        try:
            ip_obj = ipaddress.ip_address(ip)
            # Get /8 network
            network = ipaddress.ip_network(f"{ip.split('.')[0]}.0.0.0/8")
            network_blocks[str(network)].append(ip)
        except:
            pass
    
    sorted_blocks = sorted(network_blocks.items(), key=lambda x: len(x[1]), reverse=True)
    for network, ips in sorted_blocks[:10]:
        print(f"  {network}: {len(ips)} IPs")
    
    # Check for private IPs
    print("\nPrivate IP Analysis:")
    private_ips = []
    for ip in unique_ips.keys():
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                private_ips.append(ip)
        except:
            pass
    
    if private_ips:
        print(f"  Found {len(private_ips)} private IPs (should not be resolved via ARIN)")
        for ip in private_ips[:5]:
            print(f"    - {ip}")
    else:
        print("  No private IPs found (good)")
    
    # Site name patterns
    print("\nSite Name Patterns:")
    site_prefixes = Counter()
    for item in data['unresolved_ips_by_site']:
        prefix = item['network_name'].split()[0] if ' ' in item['network_name'] else item['network_name'][:3]
        site_prefixes[prefix] += 1
    
    print("  Top site prefixes with unresolved IPs:")
    for prefix, count in site_prefixes.most_common(10):
        percent = (count / len(data['unresolved_ips_by_site'])) * 100
        print(f"    {prefix}: {count} ({percent:.1f}%)")
    
    # Check for known CDN/Cloud ranges
    print("\nKnown Provider IP Ranges:")
    cdn_ranges = {
        '166.': 'Potentially Optimum/Altice',
        '75.': 'Potentially Comcast',
        '72.': 'Potentially Charter/Spectrum',
        '98.': 'Potentially Cox',
        '24.': 'Potentially Comcast',
        '107.': 'Potentially Verizon',
        '68.': 'Potentially Cox',
        '96.': 'Potentially Charter/Spectrum',
        '65.': 'Potentially Multiple providers',
        '173.': 'Potentially Comcast'
    }
    
    for prefix, provider in cdn_ranges.items():
        count = sum(1 for ip in unique_ips.keys() if ip.startswith(prefix))
        if count > 0:
            percent = (count / len(unique_ips)) * 100
            print(f"  {prefix}x.x.x: {count} IPs ({percent:.1f}%) - {provider}")

if __name__ == "__main__":
    analyze_unresolved_ips()