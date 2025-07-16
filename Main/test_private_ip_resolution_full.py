#!/usr/bin/env python3
"""
Comprehensive test of private IP resolution using DDNS lookup and ARIN provider identification
"""
import requests
import ipaddress
import socket
import json
import os
from datetime import datetime

API_KEY = os.getenv('MERAKI_API_KEY', '5174c907a7d57dea6a0788617287c985cc80b3c1')
ORG_ID = '436883'

# Test sites with private IPs from the log
TEST_SITES = [
    ('COD 37', 'Q2QN-ZBUX-WYC8', '50.246.196.57', '192.168.0.151'),
    ('COD 38', 'Q2QN-JTXQ-W9AW', '63.229.225.1', '192.168.2.103'),
    ('COD 39', 'Q2QN-D7LY-WDUS', '96.84.240.97', '192.168.0.151'),
    ('COD 40', 'Q2QN-J8UM-NFSR', '71.24.134.221', '192.168.0.151'),
    ('COD 41', 'Q2QN-GZ99-25PZ', '65.56.84.242', '166.156.147.159'),  # This one has public WAN2
    ('COD 42', 'Q2KY-XHSM-AYM6', '23.24.156.189', '192.168.0.152'),
    ('COD_00', 'Q2KY-NDXY-RXJV', '173.164.63.45', '192.168.2.104'),
]

def fetch_json(url, context=""):
    """Helper to fetch JSON from URL"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"  Error fetching {context}: {e}")
    return None

def is_private_ip(ip):
    """Check if IP is private"""
    if not ip:
        return False
    try:
        ip_addr = ipaddress.ip_address(ip)
        return ip_addr.is_private
    except:
        return False

def get_network_id_for_device(serial):
    """Get network ID for a device serial"""
    url = f"https://api.meraki.com/api/v1/devices/{serial}"
    headers = {
        'X-Cisco-Meraki-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('networkId')
    except:
        pass
    return None

def resolve_private_ip_via_ddns(network_id, network_name, wan_number):
    """Resolve private IP to public IP using DDNS"""
    url = f"https://api.meraki.com/api/v1/networks/{network_id}/appliance/settings"
    headers = {
        'X-Cisco-Meraki-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            ddns = data.get('dynamicDns', {})
            
            if ddns.get('enabled') and ddns.get('url'):
                base_hostname = ddns.get('url')
                
                # First try to resolve base hostname
                try:
                    base_ip = socket.gethostbyname(base_hostname)
                    
                    # For WAN2, try common patterns
                    if wan_number == 2:
                        # Try various WAN2 patterns
                        patterns = [
                            base_hostname.replace('.dynamic-m.com', '-2.dynamic-m.com'),
                            base_hostname.replace('.dynamic-m.com', '-wan2.dynamic-m.com'),
                            base_hostname.replace('.dynamic-m.com', '-b.dynamic-m.com')
                        ]
                        
                        for pattern in patterns:
                            try:
                                test_ip = socket.gethostbyname(pattern)
                                if test_ip != base_ip and not is_private_ip(test_ip):
                                    return test_ip, pattern
                            except:
                                continue
                    
                    # If WAN1 or no WAN2 pattern worked, return base
                    if not is_private_ip(base_ip):
                        return base_ip, base_hostname
                        
                except Exception as e:
                    print(f"    Failed to resolve {base_hostname}: {e}")
                    
    except Exception as e:
        print(f"    Error getting DDNS settings: {e}")
    
    return None, None

def parse_arin_response(rdap_data):
    """Parse ARIN RDAP response (same logic as nightly script)"""
    def collect_org_entities(entities):
        """Recursively collect organization names with their latest event dates"""
        org_candidates = []
        
        for entity in entities:
            vcard = entity.get("vcardArray", [])
            if vcard and isinstance(vcard, list) and len(vcard) > 1:
                vcard_props = vcard[1]
                name = None
                kind = None
                
                for prop in vcard_props:
                    if len(prop) >= 4:
                        label = prop[0]
                        value = prop[3]
                        if label == "fn":
                            name = value
                        elif label == "kind":
                            kind = value
                
                if kind and kind.lower() == "org" and name:
                    if not any(keyword in name for keyword in ["Mr.", "Ms.", "Dr.", "Mrs.", "Miss"]):
                        if not any(indicator in name.lower() for indicator in ["admin", "technical", "abuse", "noc"]):
                            latest_date = None
                            for event in entity.get("events", []):
                                date_str = event.get("eventDate", "")
                                if date_str:
                                    try:
                                        event_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                                        if latest_date is None or event_date > latest_date:
                                            latest_date = event_date
                                    except:
                                        pass
                            
                            org_candidates.append((name, latest_date))
            
            if "entities" in entity:
                nested_orgs = collect_org_entities(entity["entities"])
                org_candidates.extend(nested_orgs)
        
        return org_candidates
    
    entities = rdap_data.get("entities", [])
    org_candidates = collect_org_entities(entities)
    
    org_candidates.sort(key=lambda x: x[1] if x[1] else datetime.min, reverse=True)
    
    if org_candidates:
        provider = org_candidates[0][0]
        
        # Clean up common corporate designations
        for suffix in [", LLC", " LLC", ", Inc.", " Inc.", " Corporation", " Corp.", " Company", " Co."]:
            if provider.endswith(suffix):
                provider = provider[:-len(suffix)]
        
        # Map common providers
        if "CELLCO-PART" in provider:
            provider = "Verizon Wireless"
        elif "MCICS" in provider:
            provider = "Verizon Wireless"
        
        return provider
    
    network_name = rdap_data.get("name", "")
    if network_name:
        return network_name
    
    return "Unknown"

def get_provider_for_ip(ip, network_id=None, network_name=None, wan_number=None):
    """Enhanced provider lookup that resolves private IPs via DDNS"""
    try:
        ip_addr = ipaddress.ip_address(ip)
        
        # Check for private IP
        if ip_addr.is_private:
            if network_id:
                # Try to resolve via DDNS
                resolved_ip, ddns_hostname = resolve_private_ip_via_ddns(network_id, network_name, wan_number)
                if resolved_ip:
                    print(f"      Resolved via DDNS ({ddns_hostname}): {resolved_ip}")
                    # Now lookup the resolved public IP
                    ip = resolved_ip
                    ip_addr = ipaddress.ip_address(ip)
                else:
                    return "Private IP (No DDNS resolution)"
            else:
                return "Private IP"
        
        # Special handling for 166.80.0.0/16 range
        if ipaddress.IPv4Address("166.80.0.0") <= ip_addr <= ipaddress.IPv4Address("166.80.255.255"):
            return "Verizon Business"
    except ValueError:
        return "Invalid IP"
    
    # Do ARIN lookup for public IP
    rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
    rdap_data = fetch_json(rdap_url, f"ARIN for {ip}")
    if not rdap_data:
        return "Unknown"
    
    return parse_arin_response(rdap_data)

print("=== Comprehensive Private IP Resolution Test ===\n")

# Test each site
for network_name, serial, wan1_ip, wan2_ip in TEST_SITES:
    print(f"\n{network_name} ({serial}):")
    print(f"  Original WAN1: {wan1_ip}")
    print(f"  Original WAN2: {wan2_ip}")
    
    # Get network ID for DDNS lookup
    network_id = get_network_id_for_device(serial)
    if not network_id:
        print(f"  Could not get network ID for device")
        continue
    
    print(f"  Network ID: {network_id}")
    
    # Process WAN1
    print(f"\n  WAN1 Analysis:")
    if is_private_ip(wan1_ip):
        print(f"    {wan1_ip} is PRIVATE")
    wan1_provider = get_provider_for_ip(wan1_ip, network_id, network_name, 1)
    print(f"    Provider: {wan1_provider}")
    
    # Process WAN2
    print(f"\n  WAN2 Analysis:")
    if is_private_ip(wan2_ip):
        print(f"    {wan2_ip} is PRIVATE")
    wan2_provider = get_provider_for_ip(wan2_ip, network_id, network_name, 2)
    print(f"    Provider: {wan2_provider}")
    
    print("-" * 60)