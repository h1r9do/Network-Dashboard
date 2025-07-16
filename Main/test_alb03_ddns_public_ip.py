#!/usr/bin/env python3
"""
Test script to get public IP for ALB 03 using DDNS from management interface settings
"""
import requests
import json
import socket
import os

API_KEY = os.getenv('MERAKI_API_KEY', '5174c907a7d57dea6a0788617287c985cc80b3c1')
device_serial = "Q2KY-FBAF-VTHH"

def resolve_ddns_hostname(hostname):
    """Resolve DDNS hostname to IP address"""
    try:
        ip = socket.gethostbyname(hostname)
        print(f"  Resolved {hostname} → {ip}")
        return ip
    except Exception as e:
        print(f"  Failed to resolve {hostname}: {e}")
        return None

print("=== Testing ALB 03 DDNS Public IP Resolution ===\n")

# Get management interface settings
url = f"https://api.meraki.com/api/v1/devices/{device_serial}/management"
headers = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

print(f"1. Getting management interface settings for {device_serial}...")
print(f"   URL: {url}")

try:
    response = requests.get(url, headers=headers, timeout=30)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n2. Management Interface Data:")
        print(json.dumps(data, indent=2))
        
        # Check DDNS settings
        print("\n3. DDNS Analysis:")
        ddns = data.get('ddnsHostnames', {})
        
        if ddns:
            print("   DDNS Enabled: Yes")
            print(f"   Active DDNS: {ddns.get('activeDdnsHostname')}")
            print(f"   DDNS Hostname Wan1: {ddns.get('ddnsHostnameWan1')}")
            print(f"   DDNS Hostname Wan2: {ddns.get('ddnsHostnameWan2')}")
            
            # Resolve DDNS hostnames
            print("\n4. Resolving DDNS hostnames to IPs:")
            
            wan1_ddns = ddns.get('ddnsHostnameWan1')
            if wan1_ddns:
                wan1_public_ip = resolve_ddns_hostname(wan1_ddns)
            
            wan2_ddns = ddns.get('ddnsHostnameWan2')
            if wan2_ddns:
                wan2_public_ip = resolve_ddns_hostname(wan2_ddns)
                
            # Also check active DDNS
            active_ddns = ddns.get('activeDdnsHostname')
            if active_ddns:
                active_public_ip = resolve_ddns_hostname(active_ddns)
                
        else:
            print("   DDNS not configured")
            
        # Check WAN settings
        print("\n5. WAN Settings:")
        wan1 = data.get('wan1', {})
        wan2 = data.get('wan2', {})
        
        print(f"   WAN1 Using Static IP: {wan1.get('usingStaticIp')}")
        print(f"   WAN1 Static IP: {wan1.get('staticIp')}")
        print(f"   WAN1 VLAN: {wan1.get('vlan')}")
        
        print(f"   WAN2 Using Static IP: {wan2.get('usingStaticIp')}")
        print(f"   WAN2 Static IP: {wan2.get('staticIp')}")
        print(f"   WAN2 VLAN: {wan2.get('vlan')}")
        
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Exception: {e}")
    
print("\n=== Summary ===")
print("The management interface settings should contain DDNS hostnames")
print("which can be resolved to get the public IP addresses.")