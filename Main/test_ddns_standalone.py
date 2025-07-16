#!/usr/bin/env python3
"""
Standalone test for DDNS enhanced provider lookup
"""

import socket
import ipaddress
import requests
import sys

def resolve_ddns_hostname(hostname, timeout=10):
    """Resolve DDNS hostname to IP address"""
    try:
        socket.setdefaulttimeout(timeout)
        ip = socket.gethostbyname(hostname)
        print(f"  DDNS resolved: {hostname} -> {ip}")
        return ip
    except socket.gaierror as e:
        print(f"  DDNS resolution failed for {hostname}: {e}")
        return None
    except Exception as e:
        print(f"  Unexpected error resolving {hostname}: {e}")
        return None
    finally:
        socket.setdefaulttimeout(None)

def construct_ddns_hostname(network_name, wan_number, base_url):
    """Construct DDNS hostname for specific WAN interface"""
    if '.dynamic-m.com' in base_url:
        base_hostname = base_url.split('.dynamic-m.com')[0]
        return f"{base_hostname}-{wan_number}.dynamic-m.com"
    else:
        prefix = network_name.lower().replace(' ', '-')
        return f"{prefix}-{wan_number}.dynamic-m.com"

def simple_arin_lookup(ip):
    """Simple ARIN lookup for testing"""
    try:
        rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
        response = requests.get(rdap_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Simple provider extraction
        provider = 'Unknown'
        entities = data.get('entities', [])
        for entity in entities:
            if entity.get('roles') and 'registrant' in entity.get('roles', []):
                if 'vcardArray' in entity:
                    vcard = entity['vcardArray'][1] if len(entity['vcardArray']) > 1 else []
                    for item in vcard:
                        if isinstance(item, list) and len(item) >= 4 and item[0] == 'fn':
                            provider = item[3]
                            break
                break
        
        if provider == 'Unknown' and 'name' in data:
            provider = data['name']
            
        return provider
        
    except Exception as e:
        print(f"  ARIN lookup error: {str(e)}")
        return "Unknown"

def test_enhanced_ddns_lookup():
    """Test enhanced DDNS functionality"""
    print("=== Enhanced DDNS Provider Lookup Test ===")
    print()
    
    # Test 1: Regular public IP
    print("Test 1: Public IP (Google DNS)")
    provider = simple_arin_lookup("8.8.8.8")
    print(f"  8.8.8.8 -> {provider}")
    print()
    
    # Test 2: Private IP with DDNS lookup (ALN 01 example)
    print("Test 2: Private IP with DDNS (ALN 01 WAN2 cellular)")
    private_ip = "192.168.2.118"
    network_name = "ALN 01"
    wan_number = 2
    ddns_url = "aln-01-rbzcbbnrrp.dynamic-m.com"
    
    print(f"  Original private IP: {private_ip}")
    print(f"  Network: {network_name}, WAN{wan_number}")
    
    # Construct DDNS hostname
    ddns_hostname = construct_ddns_hostname(network_name, wan_number, ddns_url)
    print(f"  DDNS hostname: {ddns_hostname}")
    
    # Try to resolve
    public_ip = resolve_ddns_hostname(ddns_hostname)
    
    if public_ip and public_ip != private_ip:
        print(f"  SUCCESS: DDNS revealed public IP: {public_ip}")
        
        # Now lookup the public IP provider
        provider = simple_arin_lookup(public_ip)
        print(f"  Provider: {provider}")
        print(f"  Final result: {private_ip} -> {provider} (via DDNS)")
    else:
        print(f"  FAILED: Could not resolve DDNS or got same IP")
        print(f"  Result: {private_ip} -> Private IP (DDNS failed)")
    
    print()
    
    # Test 3: Test ALB 03 as well
    print("Test 3: ALB 03 WAN2 cellular connection")
    private_ip = "192.168.0.151"
    network_name = "ALB 03"
    wan_number = 2
    ddns_url = "alb-03-qwnncvhhrp.dynamic-m.com"
    
    print(f"  Original private IP: {private_ip}")
    print(f"  Network: {network_name}, WAN{wan_number}")
    
    ddns_hostname = construct_ddns_hostname(network_name, wan_number, ddns_url)
    print(f"  DDNS hostname: {ddns_hostname}")
    
    public_ip = resolve_ddns_hostname(ddns_hostname)
    
    if public_ip and public_ip != private_ip:
        print(f"  SUCCESS: DDNS revealed public IP: {public_ip}")
        provider = simple_arin_lookup(public_ip)
        print(f"  Provider: {provider}")
        print(f"  Final result: {private_ip} -> {provider} (via DDNS)")
    else:
        print(f"  Result: {private_ip} -> Private IP (DDNS failed)")

if __name__ == "__main__":
    test_enhanced_ddns_lookup()