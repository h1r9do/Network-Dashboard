#!/usr/bin/env python3
"""
Retry the 18 failed ARIN lookups
"""

import psycopg2
import requests
import json
import time

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='dsrcircuits',
    user='dsruser',
    password='dsrpass123'
)
cursor = conn.cursor()

# Get the 18 unresolved IPs
cursor.execute("""
    SELECT DISTINCT network_name, wan1_ip, wan2_ip, wan1_arin_provider, wan2_arin_provider
    FROM meraki_inventory
    WHERE (wan1_ip IS NOT NULL AND wan1_ip != '' AND wan1_ip != 'None' 
           AND (wan1_arin_provider IS NULL OR wan1_arin_provider = '' OR wan1_arin_provider = 'Unknown'))
       OR (wan2_ip IS NOT NULL AND wan2_ip != '' AND wan2_ip != 'None' 
           AND (wan2_arin_provider IS NULL OR wan2_arin_provider = '' OR wan2_arin_provider = 'Unknown'))
    ORDER BY network_name
""")

print("=== RETRYING 18 FAILED IPS ===\n")

failed_ips = []
for row in cursor.fetchall():
    network_name, wan1_ip, wan2_ip, wan1_arin, wan2_arin = row
    
    if wan1_ip and (not wan1_arin or wan1_arin in ['', 'Unknown']):
        failed_ips.append((network_name, wan1_ip, 'WAN1'))
    if wan2_ip and (not wan2_arin or wan2_arin in ['', 'Unknown']):
        failed_ips.append((network_name, wan2_ip, 'WAN2'))

print(f"Found {len(failed_ips)} unresolved IPs to retry:\n")

for network_name, ip, interface in failed_ips:
    print(f"{network_name} - {interface}: {ip}")

print("\nPress Enter to retry these lookups...")
input()

# Retry each one
success = 0
for network_name, ip, interface in failed_ips:
    print(f"\n{network_name} - {interface}: {ip}")
    try:
        response = requests.get(f"https://rdap.arin.net/registry/ip/{ip}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Got RDAP response")
            # Show what's in the response
            print(f"     Network name: {data.get('name', 'N/A')}")
            entities = data.get('entities', [])
            if entities:
                for entity in entities[:2]:  # Show first 2 entities
                    vcard = entity.get('vcardArray', [])
                    if vcard and len(vcard) > 1:
                        for prop in vcard[1]:
                            if prop[0] == 'fn':
                                print(f"     Entity: {prop[3]}")
            success += 1
        else:
            print(f"  ❌ HTTP {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {type(e).__name__}: {e}")
    
    time.sleep(0.5)

print(f"\n{success} out of {len(failed_ips)} got responses")
cursor.close()
conn.close()