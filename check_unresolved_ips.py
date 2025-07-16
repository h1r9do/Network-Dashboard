#!/usr/bin/env python3
"""
Check and query unresolved ARIN IPs interactively
"""

import psycopg2
import requests
import json
import time
import sys
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
                'interface': 'WAN1',
                'current_value': wan1_arin
            })
        if wan2_ip and (not wan2_arin or wan2_arin in ['', 'Unknown']):
            unresolved.append({
                'network_name': network_name,
                'ip': wan2_ip,
                'interface': 'WAN2',
                'current_value': wan2_arin
            })
    
    cursor.close()
    conn.close()
    return unresolved

def query_arin(ip):
    """Query ARIN for a specific IP"""
    print(f"\nQuerying ARIN for {ip}...")
    print("-" * 60)
    
    try:
        response = requests.get(f"https://rdap.arin.net/registry/ip/{ip}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ ARIN Response Received\n")
            
            # Network info
            print(f"Network Name: {data.get('name', 'N/A')}")
            print(f"Handle: {data.get('handle', 'N/A')}")
            print(f"Type: {data.get('objectClassName', 'N/A')}")
            
            # CIDR info
            cidr = data.get('cidr0_cidrs', [])
            if cidr:
                cidr_blocks = [c.get('v4prefix', '') for c in cidr if c.get('v4prefix')]
                print(f"CIDR Blocks: {', '.join(cidr_blocks)}")
            
            # Get organization info from entities
            print("\nOrganizations:")
            entities = data.get('entities', [])
            org_found = False
            for entity in entities:
                roles = entity.get('roles', [])
                vcard = entity.get('vcardArray', [])
                if vcard and len(vcard) > 1:
                    for prop in vcard[1]:
                        if prop[0] == 'fn' and len(prop) >= 4:
                            name = prop[3]
                            print(f"  - {name} (Roles: {', '.join(roles)})")
                            org_found = True
            
            if not org_found:
                print("  None found")
            
            # Links
            print("\nLinks:")
            links = data.get('links', [])
            for link in links[:3]:  # Show first 3 links
                print(f"  - {link.get('rel', 'N/A')}: {link.get('href', 'N/A')}")
            
            # Events
            print("\nLast Events:")
            events = data.get('events', [])
            for event in events[:3]:  # Show last 3 events
                action = event.get('eventAction', 'N/A')
                date = event.get('eventDate', 'N/A')
                print(f"  - {action}: {date}")
            
            # Save option
            print("\nWould you like to save this to the database? (y/n): ", end='')
            if input().lower() == 'y':
                return data
            
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
    
    return None

def save_to_database(ip, interface, network_name, arin_data):
    """Save ARIN data to database"""
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    # Extract provider name
    provider = arin_data.get('name', 'Unknown')
    entities = arin_data.get('entities', [])
    for entity in entities:
        vcard = entity.get('vcardArray', [])
        if vcard and len(vcard) > 1:
            for prop in vcard[1]:
                if prop[0] == 'fn' and len(prop) >= 4:
                    if 'registrant' in entity.get('roles', []):
                        provider = prop[3]
                        break
    
    # Clean provider name
    provider = provider.replace(', LLC', '').replace(' Inc.', '').strip()
    
    print(f"\nSaving as provider: {provider}")
    
    # Update cache
    cursor.execute("""
        INSERT INTO rdap_cache (ip_address, provider_name, rdap_response, last_queried)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (ip_address) DO UPDATE SET
            provider_name = EXCLUDED.provider_name,
            rdap_response = EXCLUDED.rdap_response,
            last_queried = NOW()
    """, (ip, provider, json.dumps(arin_data)))
    
    # Update meraki_inventory
    if interface == 'WAN1':
        cursor.execute("UPDATE meraki_inventory SET wan1_arin_provider = %s WHERE wan1_ip = %s", (provider, ip))
    else:
        cursor.execute("UPDATE meraki_inventory SET wan2_arin_provider = %s WHERE wan2_ip = %s", (provider, ip))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("✅ Saved to database")

def main():
    print("=== UNRESOLVED IP CHECKER ===")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    while True:
        # Get current unresolved IPs
        unresolved = get_unresolved_ips()
        
        if not unresolved:
            print("🎉 No unresolved IPs found! All IPs have ARIN data.")
            break
        
        print(f"Found {len(unresolved)} unresolved IPs:\n")
        
        # Display them
        for i, item in enumerate(unresolved, 1):
            print(f"{i:2}. {item['network_name']:15} {item['interface']:5} {item['ip']:15} (Current: {item['current_value'] or 'NULL'})")
        
        print(f"\nOptions:")
        print("  Enter a number (1-{}) to query that IP".format(len(unresolved)))
        print("  Enter 'a' to query all")
        print("  Enter 'q' to quit")
        print("\nChoice: ", end='')
        
        choice = input().strip().lower()
        
        if choice == 'q':
            break
        elif choice == 'a':
            # Query all
            success = 0
            for item in unresolved:
                arin_data = query_arin(item['ip'])
                if arin_data:
                    save_to_database(item['ip'], item['interface'], item['network_name'], arin_data)
                    success += 1
                time.sleep(0.5)  # Be nice to the API
            print(f"\n✅ Resolved {success} out of {len(unresolved)} IPs")
        else:
            # Query specific IP
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(unresolved):
                    item = unresolved[idx]
                    arin_data = query_arin(item['ip'])
                    if arin_data:
                        save_to_database(item['ip'], item['interface'], item['network_name'], arin_data)
                else:
                    print("Invalid number")
            except ValueError:
                print("Invalid choice")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)