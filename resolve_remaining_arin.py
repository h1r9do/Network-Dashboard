#!/usr/bin/env python3
"""
Resolve remaining ARIN IPs with progress output
"""

import psycopg2
import requests
import json
import time
import sys
from datetime import datetime
import ipaddress

def parse_arin_response(rdap_data):
    """Parse ARIN response to get provider name"""
    if not rdap_data:
        return "Unknown"
    
    # First try network name
    network_name = rdap_data.get('name', '')
    
    # Known network patterns
    if network_name.startswith('SBC-'):
        return 'AT&T'
    elif 'COMCAST' in network_name.upper():
        return 'Comcast'
    elif 'CHARTER' in network_name.upper() or 'CC04' in network_name:
        return 'Charter Communications'
    elif 'COX' in network_name.upper():
        return 'Cox Communications'
    
    # Look in entities for org name
    entities = rdap_data.get('entities', [])
    for entity in entities:
        vcard = entity.get('vcardArray', [])
        if vcard and len(vcard) > 1:
            for prop in vcard[1]:
                if len(prop) >= 4 and prop[0] == 'fn':
                    org_name = prop[3]
                    # Skip role names
                    if any(skip in org_name.lower() for skip in ['admin', 'technical', 'abuse', 'noc']):
                        continue
                    # Clean up common suffixes
                    org_name = org_name.replace(', LLC', '').replace(' LLC', '')
                    org_name = org_name.replace(' Inc.', '').replace(' Inc', '')
                    org_name = org_name.replace('Private Customer - ', '')
                    
                    # Return known providers
                    if 'Comcast' in org_name:
                        return 'Comcast'
                    elif 'Cox' in org_name:
                        return 'Cox Communications'
                    elif 'Charter' in org_name:
                        return 'Charter Communications'
                    elif 'AT&T' in org_name:
                        return 'AT&T'
                    elif 'Verizon' in org_name:
                        return 'Verizon'
                    elif 'Century' in org_name or 'Lumen' in org_name:
                        return 'CenturyLink'
                    elif 'Frontier' in org_name:
                        return 'Frontier Communications'
                    elif org_name and org_name != network_name:
                        return org_name
    
    return network_name or "Unknown"

def main():
    print("=== RESOLVING REMAINING ARIN IPS ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Connect to database
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    # Get all unresolved IPs
    print("Gathering unresolved IPs...")
    cursor.execute("""
        SELECT DISTINCT ip_address, site_name, interface
        FROM (
            SELECT wan1_ip as ip_address, network_name as site_name, 'WAN1' as interface
            FROM meraki_inventory
            WHERE wan1_ip IS NOT NULL 
              AND wan1_ip != '' 
              AND wan1_ip != 'None'
              AND (wan1_arin_provider IS NULL OR wan1_arin_provider = '' OR wan1_arin_provider = 'Unknown')
            
            UNION ALL
            
            SELECT wan2_ip as ip_address, network_name as site_name, 'WAN2' as interface
            FROM meraki_inventory
            WHERE wan2_ip IS NOT NULL 
              AND wan2_ip != '' 
              AND wan2_ip != 'None'
              AND (wan2_arin_provider IS NULL OR wan2_arin_provider = '' OR wan2_arin_provider = 'Unknown')
        ) AS unresolved
        ORDER BY ip_address
    """)
    
    unresolved_ips = cursor.fetchall()
    total = len(unresolved_ips)
    print(f"Found {total} unresolved IPs\n")
    
    if total == 0:
        print("No unresolved IPs found!")
        return
    
    # Process in batches
    successful = 0
    failed = 0
    batch_size = 10
    
    print(f"Processing in batches of {batch_size}...")
    print("-" * 80)
    
    for i in range(0, total, batch_size):
        batch = unresolved_ips[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total + batch_size - 1) // batch_size
        
        print(f"\nBatch {batch_num}/{total_batches} ({i+1}-{min(i+batch_size, total)} of {total}):")
        
        for ip, site_name, interface in batch:
            # Check if private IP
            try:
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj.is_private:
                    print(f"  {ip:15} ({site_name:10} {interface}) -> Private IP [SKIP]")
                    continue
            except:
                pass
            
            # Special handling for Verizon Business range
            try:
                if ipaddress.IPv4Address("166.80.0.0") <= ip_obj <= ipaddress.IPv4Address("166.80.255.255"):
                    provider = "Verizon Business"
                    print(f"  {ip:15} ({site_name:10} {interface}) -> {provider} [SPECIAL]")
                    
                    # Update database
                    if interface == 'WAN1':
                        cursor.execute("UPDATE meraki_inventory SET wan1_arin_provider = %s WHERE wan1_ip = %s", (provider, ip))
                    else:
                        cursor.execute("UPDATE meraki_inventory SET wan2_arin_provider = %s WHERE wan2_ip = %s", (provider, ip))
                    
                    successful += 1
                    continue
            except:
                pass
            
            # ARIN lookup
            try:
                rdap_url = f"https://rdap.arin.net/registry/ip/{ip}"
                response = requests.get(rdap_url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    provider = parse_arin_response(data)
                    
                    if provider and provider != "Unknown":
                        print(f"  {ip:15} ({site_name:10} {interface}) -> {provider} [OK]")
                        
                        # Update cache
                        cursor.execute("""
                            INSERT INTO rdap_cache (ip_address, provider_name, rdap_response, last_queried)
                            VALUES (%s, %s, %s, NOW())
                            ON CONFLICT (ip_address) DO UPDATE SET
                                provider_name = EXCLUDED.provider_name,
                                rdap_response = EXCLUDED.rdap_response,
                                last_queried = NOW()
                        """, (ip, provider, json.dumps(data)))
                        
                        # Update meraki_inventory
                        if interface == 'WAN1':
                            cursor.execute("UPDATE meraki_inventory SET wan1_arin_provider = %s WHERE wan1_ip = %s", (provider, ip))
                        else:
                            cursor.execute("UPDATE meraki_inventory SET wan2_arin_provider = %s WHERE wan2_ip = %s", (provider, ip))
                        
                        successful += 1
                    else:
                        print(f"  {ip:15} ({site_name:10} {interface}) -> No provider found [FAIL]")
                        failed += 1
                else:
                    print(f"  {ip:15} ({site_name:10} {interface}) -> HTTP {response.status_code} [FAIL]")
                    failed += 1
                    
            except requests.exceptions.Timeout:
                print(f"  {ip:15} ({site_name:10} {interface}) -> Timeout [FAIL]")
                failed += 1
            except Exception as e:
                print(f"  {ip:15} ({site_name:10} {interface}) -> Error: {type(e).__name__} [FAIL]")
                failed += 1
            
            # Small delay to be nice to API
            time.sleep(0.1)
        
        # Commit after each batch
        conn.commit()
        print(f"  Batch committed. Running totals: {successful} successful, {failed} failed")
        
        # Progress indicator
        progress = ((i + len(batch)) / total) * 100
        print(f"  Overall progress: {progress:.1f}%")
    
    # Final statistics
    print("\n" + "=" * 80)
    print(f"COMPLETED at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nFinal Results:")
    print(f"  Total processed: {total}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  Success rate: {(successful/total*100):.1f}%" if total > 0 else "N/A")
    
    # Show updated resolution rates
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN wan1_ip IS NOT NULL AND wan1_ip != '' AND wan1_ip != 'None' THEN 1 END) as wan1_total,
            COUNT(CASE WHEN wan1_arin_provider IS NOT NULL AND wan1_arin_provider != '' AND wan1_arin_provider != 'Unknown' THEN 1 END) as wan1_resolved,
            COUNT(CASE WHEN wan2_ip IS NOT NULL AND wan2_ip != '' AND wan2_ip != 'None' THEN 1 END) as wan2_total,
            COUNT(CASE WHEN wan2_arin_provider IS NOT NULL AND wan2_arin_provider != '' AND wan2_arin_provider != 'Unknown' THEN 1 END) as wan2_resolved
        FROM meraki_inventory
    """)
    
    wan1_total, wan1_resolved, wan2_total, wan2_resolved = cursor.fetchone()
    print(f"\nUpdated ARIN Resolution Rates:")
    print(f"  WAN1: {wan1_resolved}/{wan1_total} ({wan1_resolved/wan1_total*100:.1f}%)")
    print(f"  WAN2: {wan2_resolved}/{wan2_total} ({wan2_resolved/wan2_total*100:.1f}%)")
    print(f"  Overall: {wan1_resolved+wan2_resolved}/{wan1_total+wan2_total} ({(wan1_resolved+wan2_resolved)/(wan1_total+wan2_total)*100:.1f}%)")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()