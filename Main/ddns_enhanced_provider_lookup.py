#!/usr/bin/env python3
"""
Enhanced Provider Lookup with DDNS Support
Adds DDNS hostname resolution for private IP addresses to reveal true public IPs
"""

import socket
import ipaddress
import requests
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def resolve_ddns_hostname(hostname: str, timeout: int = 10) -> Optional[str]:
    """
    Resolve DDNS hostname to IP address
    
    Args:
        hostname: DDNS hostname (e.g., site-name-xxxxx-1.dynamic-m.com)
        timeout: DNS resolution timeout in seconds
        
    Returns:
        Resolved IP address or None if resolution fails
    """
    try:
        # Set socket timeout for DNS resolution
        socket.setdefaulttimeout(timeout)
        ip = socket.gethostbyname(hostname)
        logger.info(f"DDNS resolved: {hostname} -> {ip}")
        return ip
    except socket.gaierror as e:
        logger.warning(f"DDNS resolution failed for {hostname}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error resolving {hostname}: {e}")
        return None
    finally:
        # Reset socket timeout
        socket.setdefaulttimeout(None)

def construct_ddns_hostname(network_name: str, wan_number: int, base_url: str) -> str:
    """
    Construct DDNS hostname from network name and WAN interface number
    
    Args:
        network_name: Network name (e.g., "ALN 01")
        wan_number: WAN interface number (1 or 2)  
        base_url: Base DDNS URL (e.g., "aln-01-rbzcbbnrrp.dynamic-m.com")
        
    Returns:
        Full DDNS hostname for the specific WAN interface
    """
    # Extract the base hostname before .dynamic-m.com
    if '.dynamic-m.com' in base_url:
        base_hostname = base_url.split('.dynamic-m.com')[0]
        return f"{base_hostname}-{wan_number}.dynamic-m.com"
    else:
        # Fallback: construct from network name
        prefix = network_name.lower().replace(' ', '-')
        return f"{prefix}-{wan_number}.dynamic-m.com"

def get_provider_for_ip_enhanced(ip: str, cache: dict, missing_set: set, 
                                network_name: str = None, wan_number: int = None, 
                                ddns_url: str = None, ddns_enabled: bool = False) -> str:
    """
    Enhanced provider lookup that uses DDNS for private IP addresses
    
    Args:
        ip: IP address to lookup
        cache: Provider cache dictionary
        missing_set: Set to track failed lookups
        network_name: Network name for DDNS hostname construction
        wan_number: WAN interface number (1 or 2) 
        ddns_url: Base DDNS URL from network settings
        ddns_enabled: Whether DDNS is enabled for this network
        
    Returns:
        Provider name string
    """
    # Check cache first
    if ip in cache:
        return cache[ip]
    
    try:
        ip_addr = ipaddress.ip_address(ip)
        
        # Special handling for known IP ranges
        if ipaddress.IPv4Address("166.80.0.0") <= ip_addr <= ipaddress.IPv4Address("166.80.255.255"):
            provider = "Verizon Business"
            cache[ip] = provider
            return provider
            
    except ValueError:
        logger.warning(f"Invalid IP address format: {ip}")
        missing_set.add(ip)
        return "Unknown"
    
    # Check known static IPs (your existing KNOWN_IPS dict)
    from nightly_meraki_db import KNOWN_IPS
    if ip in KNOWN_IPS:
        provider = KNOWN_IPS[ip]
        cache[ip] = provider
        return provider
    
    # NEW LOGIC: Handle private IPs with DDNS
    if ip_addr.is_private:
        if ddns_enabled and ddns_url and network_name and wan_number:
            logger.info(f"Private IP {ip} detected for {network_name} WAN{wan_number}, attempting DDNS lookup")
            
            # Construct DDNS hostname for this specific WAN interface
            ddns_hostname = construct_ddns_hostname(network_name, wan_number, ddns_url)
            
            # Resolve DDNS hostname to get actual public IP
            public_ip = resolve_ddns_hostname(ddns_hostname)
            
            if public_ip and public_ip != ip:
                logger.info(f"DDNS revealed public IP: {ip} -> {public_ip} for {network_name}")
                
                # Recursively call this function with the resolved public IP
                # (without DDNS parameters to avoid infinite recursion)
                provider = get_provider_for_ip_enhanced(public_ip, cache, missing_set)
                
                # Cache the result for both the private IP and public IP
                cache[ip] = f"{provider} (via DDNS)"
                cache[public_ip] = provider
                
                return f"{provider} (via DDNS)"
            else:
                logger.warning(f"DDNS resolution failed or returned same IP for {network_name} WAN{wan_number}")
                cache[ip] = "Private IP (DDNS failed)"
                return "Private IP (DDNS failed)"
        else:
            # No DDNS available or not enabled
            cache[ip] = "Private IP"
            return "Private IP"
    
    # Public IP - perform ARIN lookup
    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
    
    try:
        response = requests.get(rdap_url, timeout=10)
        response.raise_for_status()
        rdap_data = response.json()
    except Exception as e:
        logger.warning(f"Error fetching RDAP data for {ip}: {e}")
        missing_set.add(ip)
        return "Unknown"
    
    # Parse ARIN response (use your existing parse_arin_response function)
    from nightly_meraki_db import parse_arin_response
    provider = parse_arin_response(rdap_data)
    cache[ip] = provider
    return provider

def test_ddns_enhanced_lookup():
    """Test the enhanced DDNS provider lookup functionality"""
    print("Testing Enhanced DDNS Provider Lookup")
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
        ddns_url="aln-01-rbzcbbnrrp.dynamic-m.com",
        ddns_enabled=True
    )
    print(f"  192.168.2.118 (ALN 01 WAN2) -> {provider}")
    print()
    
    print("Cache contents:")
    for ip, prov in cache.items():
        print(f"  {ip} -> {prov}")

if __name__ == "__main__":
    test_ddns_enhanced_lookup()