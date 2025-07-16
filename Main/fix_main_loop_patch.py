#!/usr/bin/env python3
"""
Fix the main loop to actually use private IP resolution
"""
import os

def apply_fix():
    script_path = '/usr/local/bin/Main/nightly/nightly_meraki_db.py'
    
    # Read the script
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Find and replace the WAN IP extraction section
    old_section = """                    wan1_ip = uplink_dict.get(serial, {}).get('wan1', {}).get('ip', '')
                    wan1_assign = uplink_dict.get(serial, {}).get('wan1', {}).get('assignment', '')
                    wan2_ip = uplink_dict.get(serial, {}).get('wan2', {}).get('ip', '')
                    wan2_assign = uplink_dict.get(serial, {}).get('wan2', {}).get('assignment', '')"""
    
    new_section = """                    wan1_ip_original = uplink_dict.get(serial, {}).get('wan1', {}).get('ip', '')
                    wan1_assign = uplink_dict.get(serial, {}).get('wan1', {}).get('assignment', '')
                    wan2_ip_original = uplink_dict.get(serial, {}).get('wan2', {}).get('ip', '')
                    wan2_assign = uplink_dict.get(serial, {}).get('wan2', {}).get('assignment', '')
                    
                    # Resolve private IPs via DDNS
                    wan1_ip = wan1_ip_original
                    wan2_ip = wan2_ip_original
                    
                    if wan1_ip_original and is_private_ip(wan1_ip_original):
                        logger.info(f"  WAN1 {wan1_ip_original} is private, attempting DDNS resolution...")
                        resolved = resolve_private_ip_via_ddns(net_id, 1)
                        if resolved:
                            logger.info(f"  Resolved WAN1 private IP {wan1_ip_original} to {resolved}")
                            wan1_ip = resolved
                        else:
                            logger.info(f"  Could not resolve WAN1 private IP {wan1_ip_original}")
                    
                    if wan2_ip_original and is_private_ip(wan2_ip_original):
                        logger.info(f"  WAN2 {wan2_ip_original} is private, attempting DDNS resolution...")
                        resolved = resolve_private_ip_via_ddns(net_id, 2)
                        if resolved:
                            logger.info(f"  Resolved WAN2 private IP {wan2_ip_original} to {resolved}")
                            wan2_ip = resolved
                        else:
                            logger.info(f"  Could not resolve WAN2 private IP {wan2_ip_original}")"""
    
    if old_section in content:
        content = content.replace(old_section, new_section)
        print("Updated main processing loop to resolve private IPs")
        
        # Write the updated content
        with open(script_path, 'w') as f:
            f.write(content)
        
        print("\nSuccessfully updated the main loop!")
        return True
    else:
        print("Could not find the expected code section to update")
        return False

if __name__ == "__main__":
    if apply_fix():
        print("\nThe script will now resolve private IPs in the main processing loop")