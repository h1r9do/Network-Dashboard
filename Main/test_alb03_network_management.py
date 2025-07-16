#!/usr/bin/env python3
"""
Test script to get DDNS settings at network level for ALB 03
"""
import requests
import json
import socket
import os

API_KEY = os.getenv('MERAKI_API_KEY', '5174c907a7d57dea6a0788617287c985cc80b3c1')
network_id = "L_3790904986339115389"  # ALB 03 network ID

def resolve_ddns_hostname(hostname):
    """Resolve DDNS hostname to IP address"""
    try:
        ip = socket.gethostbyname(hostname)
        print(f"  Resolved {hostname} → {ip}")
        return ip
    except Exception as e:
        print(f"  Failed to resolve {hostname}: {e}")
        return None

print("=== Testing ALB 03 Network-Level DDNS Settings ===\n")

# Try network appliance settings
url = f"https://api.meraki.com/api/v1/networks/{network_id}/appliance/settings"
headers = {
    'X-Cisco-Meraki-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

print(f"1. Getting network appliance settings...")
print(f"   URL: {url}")

try:
    response = requests.get(url, headers=headers, timeout=30)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n2. Appliance Settings:")
        print(json.dumps(data, indent=2))
        
        # Check DDNS settings
        if 'dynamicDns' in data:
            ddns = data['dynamicDns']
            print("\n3. DDNS Configuration:")
            print(f"   Enabled: {ddns.get('enabled')}")
            print(f"   Prefix: {ddns.get('prefix')}")
            print(f"   URL: {ddns.get('url')}")
            
            if ddns.get('enabled') and ddns.get('url'):
                # The URL should be in format: prefix.dynamic-m.com
                print("\n4. Resolving DDNS URL:")
                ddns_url = ddns.get('url', '')
                if ddns_url:
                    public_ip = resolve_ddns_hostname(ddns_url)
                    
                    # Try WAN-specific URLs
                    base_url = ddns_url.replace('.dynamic-m.com', '')
                    wan1_url = f"{base_url}-wan1.dynamic-m.com"
                    wan2_url = f"{base_url}-wan2.dynamic-m.com"
                    
                    print(f"\n5. Trying WAN-specific DDNS URLs:")
                    wan1_ip = resolve_ddns_hostname(wan1_url)
                    wan2_ip = resolve_ddns_hostname(wan2_url)
                    
        else:
            print("\n   No DDNS settings found")
            
    else:
        print(f"Error: {response.text[:200]}")
        
except Exception as e:
    print(f"Exception: {e}")
    
# Also check what's in our database
print("\n\n=== Database Check ===")
import psycopg2
try:
    conn = psycopg2.connect(
        host="localhost",
        database="dsrcircuits",
        user="dsruser",
        password="dsrpass123"
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT wan1_ip, wan2_ip, wan1_mgmt_ip, wan2_mgmt_ip, ddns_hostname_wan1, ddns_hostname_wan2
        FROM meraki_inventory 
        WHERE device_serial = 'Q2KY-FBAF-VTHH'
    """)
    
    result = cursor.fetchone()
    if result:
        print("Current database values:")
        print(f"  WAN1 IP: {result[0]}")
        print(f"  WAN2 IP: {result[1]}")
        print(f"  WAN1 Mgmt IP: {result[2]}")
        print(f"  WAN2 Mgmt IP: {result[3]}")
        print(f"  DDNS WAN1: {result[4]}")
        print(f"  DDNS WAN2: {result[5]}")
        
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Database error: {e}")