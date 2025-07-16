#!/usr/bin/env python3
"""
Check why some provider names are empty
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='dsrcircuits',
            user='dsruser',
            password='dsrpass123'
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def check_empty_providers():
    """Check why provider names are empty for specific IPs"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check the specific IPs that have empty providers
        test_ips = ['12.71.205.234', '50.247.154.153', '96.75.247.185', '96.75.245.37', '96.75.151.233']
        
        for ip in test_ips:
            print(f"\n=== Checking IP: {ip} ===")
            
            # Check meraki_inventory data
            cursor.execute("""
                SELECT network_name, wan1_ip, wan2_ip, wan1_provider_label, wan2_provider_label, 
                       wan1_arin_provider, wan2_arin_provider
                FROM meraki_inventory 
                WHERE wan1_ip = %s OR wan2_ip = %s
            """, (ip, ip))
            meraki_result = cursor.fetchone()
            
            if meraki_result:
                print(f"  Meraki data:")
                print(f"    Network: {meraki_result['network_name']}")
                print(f"    WAN1 IP: {meraki_result['wan1_ip']}")
                print(f"    WAN2 IP: {meraki_result['wan2_ip']}")
                print(f"    WAN1 Provider Label: {meraki_result['wan1_provider_label']}")
                print(f"    WAN2 Provider Label: {meraki_result['wan2_provider_label']}")
                print(f"    WAN1 ARIN Provider: {meraki_result['wan1_arin_provider']}")
                print(f"    WAN2 ARIN Provider: {meraki_result['wan2_arin_provider']}")
            
            # Check enriched_circuits data
            cursor.execute("""
                SELECT network_name, wan1_provider, wan2_provider, wan1_ip, wan2_ip
                FROM enriched_circuits 
                WHERE wan1_ip = %s OR wan2_ip = %s
            """, (ip, ip))
            enriched_result = cursor.fetchone()
            
            if enriched_result:
                print(f"  Enriched data:")
                print(f"    Network: {enriched_result['network_name']}")
                print(f"    WAN1 Provider: {enriched_result['wan1_provider']}")
                print(f"    WAN2 Provider: {enriched_result['wan2_provider']}")
            
            # Check RDAP cache
            cursor.execute("""
                SELECT ip_address, provider_name
                FROM rdap_cache 
                WHERE ip_address = %s
            """, (ip,))
            rdap_result = cursor.fetchone()
            
            if rdap_result:
                print(f"  RDAP cache:")
                print(f"    Provider: {rdap_result['provider_name']}")
            else:
                print(f"  RDAP cache: No entry found")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Query failed: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    check_empty_providers()