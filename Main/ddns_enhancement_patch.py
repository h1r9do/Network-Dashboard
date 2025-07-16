#!/usr/bin/env python3
"""
DDNS Enhancement Patch for nightly_meraki_db.py
This patch adds DDNS hostname resolution for private IP addresses
"""

import socket
import ipaddress
import logging

logger = logging.getLogger(__name__)

def resolve_ddns_hostname(hostname, timeout=10):
    """
    Resolve DDNS hostname to IP address with error handling
    
    Args:
        hostname: DDNS hostname (e.g., site-name-xxxxx-1.dynamic-m.com)
        timeout: DNS resolution timeout in seconds
        
    Returns:
        Resolved IP address or None if resolution fails
    """
    try:
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
        socket.setdefaulttimeout(None)

def construct_ddns_hostname(network_name, wan_number, ddns_url):
    """
    Construct DDNS hostname for specific WAN interface
    
    Args:
        network_name: Network name (e.g., "ALN 01")
        wan_number: WAN interface number (1 or 2)  
        ddns_url: Base DDNS URL (e.g., "aln-01-rbzcbbnrrp.dynamic-m.com")
        
    Returns:
        Full DDNS hostname for the specific WAN interface
    """
    if not ddns_url:
        return None
        
    if '.dynamic-m.com' in ddns_url:
        base_hostname = ddns_url.split('.dynamic-m.com')[0]
        return f"{base_hostname}-{wan_number}.dynamic-m.com"
    else:
        # Fallback: construct from network name
        prefix = network_name.lower().replace(' ', '-')
        return f"{prefix}-{wan_number}.dynamic-m.com"

def get_network_ddns_settings(network_id):
    """
    Get DDNS settings for a network using the existing API infrastructure
    
    Args:
        network_id: Network ID
        
    Returns:
        Dictionary with DDNS settings or empty dict
    """
    try:
        # Use the existing make_api_request function from the main script
        from nightly_meraki_db import make_api_request, MERAKI_API_KEY, BASE_URL
        
        url = f"{BASE_URL}/networks/{network_id}/appliance/settings"
        response = make_api_request(url, MERAKI_API_KEY)
        
        if response and isinstance(response, dict):
            return response.get('dynamicDns', {})
        else:
            return {}
            
    except Exception as e:
        logger.warning(f"Failed to get DDNS settings for network {network_id}: {e}")
        return {}

def get_provider_for_ip_enhanced(ip, cache, missing_set, network_name=None, 
                                wan_number=None, network_id=None):
    """
    Enhanced provider lookup that uses DDNS for private IP addresses
    
    This is a drop-in replacement for the original get_provider_for_ip function
    with added DDNS functionality for private IP addresses.
    
    Args:
        ip: IP address to lookup
        cache: Provider cache dictionary
        missing_set: Set to track failed lookups
        network_name: Network name for DDNS hostname construction
        wan_number: WAN interface number (1 or 2) 
        network_id: Network ID for getting DDNS settings
        
    Returns:
        Provider name string
    """
    # Import the functions from the main script to avoid duplication
    try:
        from nightly_meraki_db import KNOWN_IPS, parse_arin_response, fetch_json
    except ImportError:
        # Fallback for testing
        KNOWN_IPS = {}
        def parse_arin_response(data):
            return "Unknown"
        def fetch_json(url, context):
            import requests
            try:
                response = requests.get(url, timeout=10)
                return response.json()
            except:
                return None
    
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
    
    # Check known static IPs
    if ip in KNOWN_IPS:
        provider = KNOWN_IPS[ip]
        cache[ip] = provider
        return provider
    
    # NEW LOGIC: Handle private IPs with DDNS
    if ip_addr.is_private:
        if network_name and wan_number and network_id:
            logger.info(f"Private IP {ip} detected for {network_name} WAN{wan_number}, checking DDNS")
            
            # Get DDNS settings for this network
            ddns_settings = get_network_ddns_settings(network_id)
            ddns_enabled = ddns_settings.get('enabled', False)
            ddns_url = ddns_settings.get('url', '')
            
            if ddns_enabled and ddns_url:
                logger.info(f"DDNS enabled for {network_name}, attempting lookup")
                
                # Construct DDNS hostname for this specific WAN interface
                ddns_hostname = construct_ddns_hostname(network_name, wan_number, ddns_url)
                
                if ddns_hostname:
                    # Resolve DDNS hostname to get actual public IP
                    public_ip = resolve_ddns_hostname(ddns_hostname)
                    
                    if public_ip and public_ip != ip:
                        logger.info(f"DDNS revealed public IP: {ip} -> {public_ip} for {network_name}")
                        
                        # Recursively call this function with the resolved public IP
                        # (without DDNS parameters to avoid infinite recursion)
                        provider = get_provider_for_ip_enhanced(public_ip, cache, missing_set)
                        
                        # Cache the result for both the private IP and public IP
                        enhanced_provider = f"{provider} (via DDNS)"
                        cache[ip] = enhanced_provider
                        if public_ip not in cache:
                            cache[public_ip] = provider
                        
                        return enhanced_provider
                    else:
                        logger.warning(f"DDNS resolution failed or returned same IP for {network_name} WAN{wan_number}")
            else:
                logger.debug(f"DDNS not enabled for {network_name}")
        
        # No DDNS available, enabled, or resolution failed
        cache[ip] = "Private IP"
        return "Private IP"
    
    # Public IP - perform ARIN lookup (original logic)
    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
    rdap_data = fetch_json(rdap_url, ip)
    if not rdap_data:
        missing_set.add(ip)
        return "Unknown"
    
    provider = parse_arin_response(rdap_data)
    cache[ip] = provider
    return provider

# Instructions for integration:
print("""
DDNS Enhancement Patch Instructions:
===================================

To integrate this DDNS functionality into nightly_meraki_db.py:

1. Add the socket import at the top of the file
2. Add the four DDNS functions after the existing provider functions
3. Replace calls to get_provider_for_ip() with get_provider_for_ip_enhanced()
4. Pass additional parameters: network_name, wan_number, network_id

Example replacement in main loop (around lines 1063 and 1070):

OLD:
    wan1_provider = get_provider_for_ip(wan1_ip, ip_cache, missing_ips)
    wan2_provider = get_provider_for_ip(wan2_ip, ip_cache, missing_ips)

NEW:
    wan1_provider = get_provider_for_ip_enhanced(
        wan1_ip, ip_cache, missing_ips, 
        network_name=net_name, wan_number=1, network_id=net_id
    )
    wan2_provider = get_provider_for_ip_enhanced(
        wan2_ip, ip_cache, missing_ips,
        network_name=net_name, wan_number=2, network_id=net_id
    )

This enhancement will:
- Automatically detect private IP addresses on WAN interfaces
- Check if DDNS is enabled for the network
- Resolve DDNS hostnames to reveal true public IPs for cellular connections
- Perform ARIN lookups on the resolved public IPs
- Cache results for efficiency
- Mark providers as "(via DDNS)" for tracking
""")