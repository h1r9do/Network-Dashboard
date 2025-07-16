#!/usr/bin/env python3
"""
Check and query all unresolved ARIN IPs automatically
"""

import psycopg2
import requests
import json
import time
from datetime import datetime

def get_unresolved_ips():
    """Get all currently unresolved IPs from the database"""
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT network_name, wan1_ip, wan2_ip, wan1_arin_provider, wan2_arin_provider
        FROM meraki_inventory
        WHERE (wan1_ip IS NOT NULL AND wan1_ip != '' AND wan1_ip != 'None' 
               AND (wan1_arin_provider IS NULL OR wan1_arin_provider = '' OR wan1_arin_provider = 'Unknown'))
           OR (wan2_ip IS NOT NULL AND wan2_ip != '' AND wan2_ip != 'None' 
               AND (wan2_arin_provider IS NULL OR wan2_arin_provider = '' OR wan2_arin_provider = 'Unknown'))
        ORDER BY network_name
    """)
    
    unresolved = []
    for row in cursor.fetchall():
        network_name, wan1_ip, wan2_ip, wan1_arin, wan2_arin = row
        
        if wan1_ip and (not wan1_arin or wan1_arin in ['', 'Unknown']):
            unresolved.append({
                'network_name': network_name,
                'ip': wan1_ip,
                'interface': 'WAN1'
            })
        if wan2_ip and (not wan2_arin or wan2_arin in ['', 'Unknown']):
            unresolved.append({
                'network_name': network_name,
                'ip': wan2_ip,
                'interface': 'WAN2'
            })
    
    cursor.close()
    conn.close()
    return unresolved

def main():
    print("=== CHECKING AND UPDATING UNRESOLVED IPS ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Database connection for updates
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    # Get current unresolved IPs
    unresolved = get_unresolved_ips()
    
    if not unresolved:
        print("✅ No unresolved IPs found! All IPs have ARIN data.")
        return
    
    print(f"Found {len(unresolved)} unresolved IPs:\n")
    
    # Query each one
    success = 0
    failed = 0
    
    for item in unresolved:
        print(f"{item['network_name']:15} {item['interface']:5} {item['ip']:15}", end=' ')
        
        try:
            response = requests.get(f"https://rdap.arin.net/registry/ip/{item['ip']}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract provider
                provider = data.get('name', 'Unknown')
                entities = data.get('entities', [])
                
                for entity in entities:
                    vcard = entity.get('vcardArray', [])
                    if vcard and len(vcard) > 1:
                        for prop in vcard[1]:
                            if prop[0] == 'fn' and len(prop) >= 4:
                                name = prop[3]
                                # Clean name
                                name = name.replace(', LLC', '').replace(' Inc.', '')
                                name = name.replace('Private Customer - ', '')
                                
                                # Skip role names
                                if any(skip in name.lower() for skip in ['admin', 'technical', 'abuse', 'noc']):
                                    continue
                                
                                # Use known provider names
                                if 'Comcast' in name:
                                    provider = 'Comcast'
                                elif 'Cox' in name:
                                    provider = 'Cox Communications'
                                elif 'Charter' in name:
                                    provider = 'Charter Communications'
                                elif 'AT&T' in name:
                                    provider = 'AT&T'
                                elif 'Verizon' in name:
                                    provider = 'Verizon'
                                elif 'Century' in name or 'Lumen' in name:
                                    provider = 'CenturyLink'
                                elif provider == data.get('name', 'Unknown'):
                                    provider = name
                                break
                        
                        if provider != data.get('name', 'Unknown'):
                            break
                
                print(f"-> {provider} [SAVED]")
                
                # Save to database
                # Update cache
                cursor.execute("""
                    INSERT INTO rdap_cache (ip_address, provider_name, rdap_response, last_queried)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (ip_address) DO UPDATE SET
                        provider_name = EXCLUDED.provider_name,
                        rdap_response = EXCLUDED.rdap_response,
                        last_queried = NOW()
                """, (item['ip'], provider, json.dumps(data)))
                
                # Update meraki_inventory
                if item['interface'] == 'WAN1':
                    cursor.execute("UPDATE meraki_inventory SET wan1_arin_provider = %s WHERE wan1_ip = %s", 
                                 (provider, item['ip']))
                else:
                    cursor.execute("UPDATE meraki_inventory SET wan2_arin_provider = %s WHERE wan2_ip = %s", 
                                 (provider, item['ip']))
                
                success += 1
                
            else:
                print(f"-> HTTP {response.status_code}")
                failed += 1
                
        except requests.exceptions.Timeout:
            print("-> TIMEOUT")
            failed += 1
        except Exception as e:
            print(f"-> ERROR: {type(e).__name__}")
            failed += 1
        
        time.sleep(0.2)  # Be nice to the API
    
    # Commit all changes
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\nSummary:")
    print(f"  Successful lookups: {success}")
    print(f"  Failed lookups: {failed}")
    print(f"  Total: {len(unresolved)}")
    
    if success > 0:
        print(f"\n✅ Successfully updated {success} IPs in the database")

if __name__ == "__main__":
    main()