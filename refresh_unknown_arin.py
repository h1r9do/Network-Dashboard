#!/usr/bin/env python3
"""
Refresh ARIN lookups for IPs showing as "Unknown" in the database
"""

import psycopg2
import requests
import time
import json

def get_arin_provider(ip_address):
    """Get ARIN provider information for an IP address"""
    if not ip_address or ip_address in ['', 'None', 'null']:
        return "Unknown"
    
    # Handle private IPs
    if ip_address.startswith(('192.168.', '10.', '172.')):
        return "Private IP"
    
    try:
        url = f'https://rdap.arin.net/registry/ip/{ip_address}'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract provider name
            provider = "Unknown"
            
            # Try different paths to find the provider name
            if 'entities' in data:
                for entity in data['entities']:
                    if 'vcardArray' in entity:
                        vcard = entity['vcardArray'][1]
                        for field in vcard:
                            if field[0] == 'fn':
                                provider = field[3]
                                break
                    if provider != "Unknown":
                        break
            
            # Alternative: check the name field directly
            if provider == "Unknown" and 'name' in data:
                provider = data['name']
                
            return provider
        else:
            return f"ARIN Error {response.status_code}"
            
    except Exception as e:
        print(f"   ❌ Error for {ip_address}: {str(e)}")
        return "Unknown"

def main():
    """Update ARIN providers for Unknown entries"""
    print("🔄 Refreshing ARIN Lookups for Unknown Providers")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='dsrcircuits',
            user='dsruser',
            password='dsrpass123'
        )
        cursor = conn.cursor()
        
        # Find all IPs with Unknown ARIN provider
        print("🔍 Finding IPs with Unknown ARIN provider...")
        cursor.execute("""
            SELECT network_name, wan1_ip, wan2_ip, wan1_arin_provider, wan2_arin_provider
            FROM meraki_inventory
            WHERE wan1_arin_provider = 'Unknown' OR wan2_arin_provider = 'Unknown'
            ORDER BY network_name
        """)
        
        unknown_ips = cursor.fetchall()
        print(f"✅ Found {len(unknown_ips)} networks with Unknown ARIN providers")
        
        # Update each one
        updated_count = 0
        for row in unknown_ips:
            network_name = row[0]
            wan1_ip = row[1]
            wan2_ip = row[2]
            wan1_arin = row[3]
            wan2_arin = row[4]
            
            updates_needed = []
            
            # Check WAN1
            if wan1_arin == 'Unknown' and wan1_ip:
                print(f"\n🔄 {network_name} WAN1: {wan1_ip}")
                new_provider = get_arin_provider(wan1_ip)
                if new_provider != 'Unknown' and not new_provider.startswith('ARIN Error'):
                    updates_needed.append(('wan1_arin_provider', new_provider))
                    print(f"   ✅ Found: {new_provider}")
                time.sleep(0.5)  # Rate limiting
            
            # Check WAN2
            if wan2_arin == 'Unknown' and wan2_ip:
                print(f"🔄 {network_name} WAN2: {wan2_ip}")
                new_provider = get_arin_provider(wan2_ip)
                if new_provider != 'Unknown' and not new_provider.startswith('ARIN Error'):
                    updates_needed.append(('wan2_arin_provider', new_provider))
                    print(f"   ✅ Found: {new_provider}")
                time.sleep(0.5)  # Rate limiting
            
            # Apply updates
            if updates_needed:
                for field, value in updates_needed:
                    cursor.execute(f"""
                        UPDATE meraki_inventory 
                        SET {field} = %s
                        WHERE network_name = %s
                    """, (value, network_name))
                conn.commit()
                updated_count += 1
        
        print(f"\n📊 SUMMARY:")
        print(f"   Networks checked: {len(unknown_ips)}")
        print(f"   Networks updated: {updated_count}")
        
        # Show some examples
        print("\n📋 Sample Updated Networks:")
        cursor.execute("""
            SELECT network_name, wan1_ip, wan1_arin_provider, wan2_ip, wan2_arin_provider
            FROM meraki_inventory
            WHERE network_name IN ('AZP 08', 'AZP 24', 'AZP 64')
            ORDER BY network_name
        """)
        
        for row in cursor.fetchall():
            print(f"\n   {row[0]}:")
            print(f"   WAN1: {row[1]} → {row[2]}")
            print(f"   WAN2: {row[3]} → {row[4]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ ARIN refresh completed!")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    main()