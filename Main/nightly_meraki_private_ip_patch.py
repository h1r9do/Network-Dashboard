#!/usr/bin/env python3
"""
Patch nightly_meraki_db.py to add private IP resolution via DDNS
"""
import os
import sys

def apply_patch():
    script_path = '/usr/local/bin/Main/nightly/nightly_meraki_db.py'
    
    # Read the script
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Check if already patched
    if 'def is_private_ip' in content:
        print("Script appears to already have private IP resolution.")
        return False
    
    # 1. Add import for socket if not present
    if 'import socket' not in content:
        content = content.replace('import ipaddress', 'import ipaddress\nimport socket')
        print("Added socket import")
    
    # 2. Add helper functions before get_provider_for_ip
    helper_functions = '''
def is_private_ip(ip):
    """Check if IP address is private."""
    try:
        return ipaddress.ip_address(ip).is_private
    except:
        return False

def resolve_private_ip_via_ddns(network_id, wan_number):
    """Resolve private IP to public IP using DDNS."""
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
                            logger.info(f"    Resolved via DDNS hostname {wan2_hostname}")
                            return resolved_ip
                    except Exception as e:
                        logger.debug(f"    Could not resolve {wan2_hostname}: {e}")
                
                # Try base hostname
                try:
                    resolved_ip = socket.gethostbyname(base_hostname)
                    if not ipaddress.ip_address(resolved_ip).is_private:
                        logger.info(f"    Resolved via DDNS hostname {base_hostname}")
                        return resolved_ip
                except Exception as e:
                    logger.debug(f"    Could not resolve {base_hostname}: {e}")
    except Exception as e:
        logger.error(f"Error resolving DDNS for network {network_id}: {e}")
    return None
'''
    
    # Insert before get_provider_for_ip
    content = content.replace(
        '    return "Unknown"\n\ndef get_provider_for_ip(ip, cache, missing_set):',
        f'    return "Unknown"\n{helper_functions}\ndef get_provider_for_ip(ip, cache, missing_set):'
    )
    print("Added helper functions")
    
    # 3. Update the main processing loop
    # Find where WAN IPs are extracted
    old_wan_extraction = '''wan1_ip = uplink_dict.get(serial, {}).get('wan1', {}).get('ip', '')
            wan1_assign = uplink_dict.get(serial, {}).get('wan1', {}).get('assignment', '')
            wan2_ip = uplink_dict.get(serial, {}).get('wan2', {}).get('ip', '')
            wan2_assign = uplink_dict.get(serial, {}).get('wan2', {}).get('assignment', '')'''
    
    new_wan_extraction = '''wan1_ip_original = uplink_dict.get(serial, {}).get('wan1', {}).get('ip', '')
            wan1_assign = uplink_dict.get(serial, {}).get('wan1', {}).get('assignment', '')
            wan2_ip_original = uplink_dict.get(serial, {}).get('wan2', {}).get('ip', '')
            wan2_assign = uplink_dict.get(serial, {}).get('wan2', {}).get('assignment', '')
            
            # Resolve private IPs via DDNS
            wan1_ip = wan1_ip_original
            wan2_ip = wan2_ip_original
            
            if wan1_ip_original and is_private_ip(wan1_ip_original):
                logger.info(f"  WAN1 {wan1_ip_original} is private, attempting DDNS resolution...")
                resolved = resolve_private_ip_via_ddns(network_id, 1)
                if resolved:
                    logger.info(f"  Resolved WAN1 private IP {wan1_ip_original} to {resolved}")
                    wan1_ip = resolved
                else:
                    logger.info(f"  Could not resolve WAN1 private IP {wan1_ip_original}")
            
            if wan2_ip_original and is_private_ip(wan2_ip_original):
                logger.info(f"  WAN2 {wan2_ip_original} is private, attempting DDNS resolution...")
                resolved = resolve_private_ip_via_ddns(network_id, 2)
                if resolved:
                    logger.info(f"  Resolved WAN2 private IP {wan2_ip_original} to {resolved}")
                    wan2_ip = resolved
                else:
                    logger.info(f"  Could not resolve WAN2 private IP {wan2_ip_original}")'''
    
    content = content.replace(old_wan_extraction, new_wan_extraction)
    print("Updated main processing loop")
    
    # Write the patched content
    try:
        with open(script_path, 'w') as f:
            f.write(content)
        print(f"\nSuccessfully patched {script_path}")
        print("Private IP resolution via DDNS has been added.")
        return True
    except Exception as e:
        print(f"Error writing file: {e}")
        return False

if __name__ == "__main__":
    if apply_patch():
        print("\nThe script will now:")
        print("1. Detect private IPs (192.168.x.x, 10.x.x.x, etc.)")
        print("2. Attempt to resolve them via DDNS")
        print("3. Store the resolved public IPs in the database")
        print("4. Properly identify providers via ARIN lookups")