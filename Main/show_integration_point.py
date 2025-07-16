#!/usr/bin/env python3
"""
Show exactly where to integrate the private IP resolution in nightly_meraki_db.py
"""

print("""
=== Integration Point for Private IP Resolution ===

In /usr/local/bin/Main/nightly/nightly_meraki_db.py:

1. Add helper function after line 600 (before get_provider_for_ip):

def resolve_private_ip_via_ddns(network_id, wan_number):
    '''Resolve private IP to public IP using DDNS'''
    try:
        url = f"{BASE_URL}/networks/{network_id}/appliance/settings"
        data = make_api_request(url, MERAKI_API_KEY)
        if data:
            ddns = data.get('dynamicDns', {})
            if ddns.get('enabled') and ddns.get('url'):
                base_hostname = ddns.get('url')
                
                # For WAN2, try -2 pattern
                if wan_number == 2:
                    wan2_hostname = base_hostname.replace('.dynamic-m.com', '-2.dynamic-m.com')
                    try:
                        resolved_ip = socket.gethostbyname(wan2_hostname)
                        if not ipaddress.ip_address(resolved_ip).is_private:
                            return resolved_ip
                    except:
                        pass
                
                # Try base hostname
                try:
                    resolved_ip = socket.gethostbyname(base_hostname)
                    if not ipaddress.ip_address(resolved_ip).is_private:
                        return resolved_ip
                except:
                    pass
    except:
        pass
    return None

2. Modify the main processing loop (around line 1061-1080):

CURRENT CODE:
    wan1_ip = uplink_dict.get(serial, {}).get('wan1', {}).get('ip', '')
    wan2_ip = uplink_dict.get(serial, {}).get('wan2', {}).get('ip', '')

CHANGE TO:
    wan1_ip_original = uplink_dict.get(serial, {}).get('wan1', {}).get('ip', '')
    wan2_ip_original = uplink_dict.get(serial, {}).get('wan2', {}).get('ip', '')
    
    # Resolve private IPs
    wan1_ip = wan1_ip_original
    wan2_ip = wan2_ip_original
    
    if wan1_ip_original and is_private_ip(wan1_ip_original):
        resolved = resolve_private_ip_via_ddns(network_id, 1)
        if resolved:
            logger.info(f"  Resolved WAN1 private IP {wan1_ip_original} to {resolved} via DDNS")
            wan1_ip = resolved
    
    if wan2_ip_original and is_private_ip(wan2_ip_original):
        resolved = resolve_private_ip_via_ddns(network_id, 2)
        if resolved:
            logger.info(f"  Resolved WAN2 private IP {wan2_ip_original} to {resolved} via DDNS")
            wan2_ip = resolved

3. Add is_private_ip helper function (if not exists):

def is_private_ip(ip):
    '''Check if IP is private'''
    try:
        return ipaddress.ip_address(ip).is_private
    except:
        return False

This way, the script will:
1. Store the resolved public IPs in wan1_ip/wan2_ip columns
2. ARIN lookups will work correctly
3. Providers will be identified properly
""")

print("\n=== Summary ===")
print("The key change is to resolve private IPs BEFORE doing the ARIN lookup.")
print("This ensures wan1_ip and wan2_ip columns contain public IPs when possible.")
print("Private IPs are only stored when DDNS resolution fails.")