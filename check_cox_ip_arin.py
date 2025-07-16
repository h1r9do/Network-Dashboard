#!/usr/bin/env python3
"""
Check ARIN for Cox IP 68.15.185.94
"""

import requests
import json

def get_arin_provider(ip_address):
    """Get ARIN provider information for an IP address"""
    print(f"🔍 Checking ARIN for IP: {ip_address}")
    print("=" * 60)
    
    try:
        url = f'https://rdap.arin.net/registry/ip/{ip_address}'
        print(f"URL: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Print full response for debugging
            print("\n📊 Full RDAP Response:")
            print(json.dumps(data, indent=2)[:1000] + "..." if len(json.dumps(data)) > 1000 else json.dumps(data, indent=2))
            
            # Extract provider name
            provider = "Unknown"
            
            # Check name field
            if 'name' in data:
                provider = data['name']
                print(f"\n✅ Found in 'name' field: {provider}")
            
            # Check entities
            if 'entities' in data:
                for entity in data['entities']:
                    if 'vcardArray' in entity:
                        vcard = entity['vcardArray'][1]
                        for field in vcard:
                            if field[0] == 'fn':
                                provider = field[3]
                                print(f"✅ Found in vcard 'fn' field: {provider}")
                                break
                    
                    # Also check roles
                    if 'roles' in entity:
                        print(f"   Entity roles: {entity['roles']}")
            
            # Check remarks for additional info
            if 'remarks' in data:
                print("\n📝 Remarks:")
                for remark in data['remarks']:
                    if 'title' in remark:
                        print(f"   - {remark['title']}")
            
            return provider
        else:
            print(f"❌ ARIN Error: Status {response.status_code}")
            print(f"Response: {response.text}")
            return f"ARIN Error {response.status_code}"
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return f"ARIN Error: {str(e)}"

def main():
    # Check the Cox IP
    cox_ip = "68.15.185.94"
    provider = get_arin_provider(cox_ip)
    
    print(f"\n📊 Final Result:")
    print(f"   IP: {cox_ip}")
    print(f"   Provider: {provider}")
    
    # Also check the database
    print("\n🔍 Checking database for this IP...")
    import psycopg2
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='dsrcircuits',
            user='dsruser',
            password='dsrpass123'
        )
        cursor = conn.cursor()
        
        # Check meraki_inventory
        cursor.execute("""
            SELECT network_name, wan1_ip, wan1_arin_provider, wan2_ip, wan2_arin_provider
            FROM meraki_inventory
            WHERE wan1_ip = %s OR wan2_ip = %s
        """, (cox_ip, cox_ip))
        
        results = cursor.fetchall()
        if results:
            print("\n📊 Database Records with this IP:")
            for row in results:
                print(f"   Network: {row[0]}")
                if row[1] == cox_ip:
                    print(f"   WAN1 IP: {row[1]} -> ARIN: {row[2]}")
                if row[3] == cox_ip:
                    print(f"   WAN2 IP: {row[3]} -> ARIN: {row[4]}")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    main()