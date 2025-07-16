#!/usr/bin/env python3
"""
Test script that properly resolves private IPs to public IPs for ALB 03
and stores them in the original wan1_ip/wan2_ip fields
"""
import requests
import json
import socket
import os
import re

API_KEY = os.getenv('MERAKI_API_KEY', '5174c907a7d57dea6a0788617287c985cc80b3c1')
ORG_ID = '436883'
network_id = "L_3790904986339115389"  # ALB 03
device_serial = "Q2KY-FBAF-VTHH"

def is_private_ip(ip):
    """Check if IP is private"""
    if not ip:
        return False
    try:
        # Check for common private IP ranges
        if re.match(r'^10\.', ip):
            return True
        if re.match(r'^172\.(1[6-9]|2[0-9]|3[0-1])\.', ip):
            return True
        if re.match(r'^192\.168\.', ip):
            return True
        return False
    except:
        return False

def resolve_ddns_to_public_ip(network_id, wan_number):
    """Get public IP by resolving DDNS hostname"""
    try:
        # Get network appliance settings for DDNS info
        url = f"https://api.meraki.com/api/v1/networks/{network_id}/appliance/settings"
        headers = {
            'X-Cisco-Meraki-API-Key': API_KEY,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            ddns = data.get('dynamicDns', {})
            
            if ddns.get('enabled') and ddns.get('url'):
                base_hostname = ddns.get('url')
                print(f"   DDNS base hostname: {base_hostname}")
                
                # Try to resolve the base hostname (usually gives active WAN)
                try:
                    base_ip = socket.gethostbyname(base_hostname)
                    print(f"   Base DDNS resolves to: {base_ip}")
                    
                    # For WAN2, we need a different approach
                    # Some networks append -wan2 or similar
                    if wan_number == 2:
                        # Try common WAN2 DDNS patterns
                        wan2_patterns = [
                            base_hostname.replace('.dynamic-m.com', '-wan2.dynamic-m.com'),
                            base_hostname.replace('.dynamic-m.com', '-2.dynamic-m.com'),
                            base_hostname  # Sometimes both WANs use same hostname
                        ]
                        
                        for pattern in wan2_patterns:
                            try:
                                test_ip = socket.gethostbyname(pattern)
                                if test_ip != base_ip:  # Different from WAN1
                                    print(f"   WAN2 pattern {pattern} resolves to: {test_ip}")
                                    return test_ip
                            except:
                                continue
                                
                    return base_ip
                    
                except Exception as e:
                    print(f"   Failed to resolve DDNS: {e}")
                    
    except Exception as e:
        print(f"   Error getting DDNS settings: {e}")
    
    return None

def get_public_ip_from_uplink_status(device_serial, interface_name):
    """
    Since the individual device uplink endpoint doesn't work,
    we need to extract from batch data or use other methods
    """
    # The batch uplink status doesn't include publicIp field
    # So we'll use DDNS resolution instead
    return None

print("=== Testing Proper IP Resolution for ALB 03 ===\n")

# Step 1: Get current IPs from batch uplink status
print("1. Getting current uplink IPs from batch API...")
url = f"https://api.meraki.com/api/v1/organizations/{ORG_ID}/appliance/uplink/statuses"
headers = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

try:
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code == 200:
        data = response.json()
        
        # Find ALB 03 device
        device_data = None
        for device in data:
            if device.get('serial') == device_serial:
                device_data = device
                break
        
        if device_data:
            uplinks = device_data.get('uplinks', [])
            wan1_ip = uplinks[0].get('ip', '') if len(uplinks) > 0 else ''
            wan2_ip = uplinks[1].get('ip', '') if len(uplinks) > 1 else ''
            
            print(f"   WAN1 IP: {wan1_ip}")
            print(f"   WAN2 IP: {wan2_ip}")
            
            # Step 2: Check if IPs are private and resolve if needed
            print("\n2. Checking for private IPs and resolving...")
            
            # Process WAN1
            if wan1_ip and is_private_ip(wan1_ip):
                print(f"   WAN1 {wan1_ip} is PRIVATE - attempting resolution...")
                wan1_public = resolve_ddns_to_public_ip(network_id, 1)
                if wan1_public and not is_private_ip(wan1_public):
                    print(f"   ✓ Resolved WAN1 to public IP: {wan1_public}")
                    wan1_ip = wan1_public
                else:
                    print(f"   ✗ Could not resolve WAN1 to public IP")
            else:
                print(f"   WAN1 {wan1_ip} is already public")
            
            # Process WAN2
            if wan2_ip and is_private_ip(wan2_ip):
                print(f"   WAN2 {wan2_ip} is PRIVATE - attempting resolution...")
                wan2_public = resolve_ddns_to_public_ip(network_id, 2)
                if wan2_public and not is_private_ip(wan2_public):
                    print(f"   ✓ Resolved WAN2 to public IP: {wan2_public}")
                    wan2_ip = wan2_public
                else:
                    print(f"   ✗ Could not resolve WAN2 to public IP")
            else:
                print(f"   WAN2 {wan2_ip} is already public")
                
            # Step 3: Show final results
            print("\n3. Final IP Resolution Results:")
            print(f"   WAN1 final IP: {wan1_ip}")
            print(f"   WAN2 final IP: {wan2_ip}")
            
            # Step 4: This is where we would update the database
            print("\n4. Database Update (simulation):")
            print(f"   UPDATE meraki_inventory SET")
            print(f"     wan1_ip = '{wan1_ip}',")
            print(f"     wan2_ip = '{wan2_ip}'")
            print(f"   WHERE device_serial = '{device_serial}'")
            print("\n   Note: This would store the resolved public IPs directly in wan1_ip/wan2_ip columns")
            
except Exception as e:
    print(f"Error: {e}")