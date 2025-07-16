#!/usr/bin/env python3
"""
Check for devices in the new IP ranges and their SNMP collection status
"""
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsruser'
}

def check_ip_ranges():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Check inventory_web_format for these IP ranges
        print("Checking inventory_web_format table:")
        print("-" * 60)
        
        ip_patterns = [
            ('192.168.4.%', 'AZ-Scottsdale-HQ-Corp'),
            ('192.168.5.%', 'AZ-Scottsdale-HQ-Corp'),
            ('192.168.12.%', 'AZ-Scottsdale-HQ-Corp'),
            ('192.168.13.%', 'AZ-Scottsdale-HQ-Corp'),
            ('192.168.200.%', 'AZ-Alameda-DC')
        ]
        
        for pattern, expected_site in ip_patterns:
            cursor.execute("""
                SELECT hostname, ip_address, position, site
                FROM inventory_web_format
                WHERE ip_address LIKE %s
                ORDER BY ip_address
            """, (pattern,))
            
            rows = cursor.fetchall()
            if rows:
                print(f"\nFound {len(rows)} devices with {pattern.replace('%', 'x')}:")
                for hostname, ip, position, site in rows:
                    site_status = "✓" if site == expected_site else "✗"
                    print(f"  {site_status} {hostname or '(component)':<30} {ip:<16} {position:<15} Site: {site or 'Not Set'}")
            else:
                print(f"\nNo devices found with {pattern.replace('%', 'x')}")
        
        # Check comprehensive_device_inventory for these IPs
        print("\n" + "="*60)
        print("Checking comprehensive_device_inventory (SNMP collection):")
        print("-" * 60)
        
        cursor.execute("""
            SELECT hostname, ip_address, model, collection_date
            FROM comprehensive_device_inventory
            WHERE ip_address LIKE '192.168.4.%'
               OR ip_address LIKE '192.168.5.%'
               OR ip_address LIKE '192.168.12.%'
               OR ip_address LIKE '192.168.13.%'
               OR ip_address LIKE '192.168.200.%'
            ORDER BY ip_address, collection_date DESC
        """)
        
        rows = cursor.fetchall()
        if rows:
            print(f"\nFound {len(rows)} entries in SNMP collection:")
            current_ip = None
            for hostname, ip, model, collection_date in rows:
                if ip != current_ip:
                    print(f"\n{ip}:")
                    current_ip = ip
                print(f"  {hostname:<30} Model: {model:<20} Collected: {collection_date}")
        else:
            print("\nNo devices found in SNMP collection for these IP ranges")
            
        # Check if we have any SNMP targets configured for these ranges
        print("\n" + "="*60)
        print("Checking for SNMP target configurations:")
        print("-" * 60)
        
        # Look for any configuration or target files
        cursor.execute("""
            SELECT DISTINCT ip_address, hostname 
            FROM datacenter_inventory
            WHERE ip_address LIKE '192.168.%'
            ORDER BY ip_address
        """)
        
        datacenter_ips = cursor.fetchall()
        if datacenter_ips:
            print(f"\nFound {len(datacenter_ips)} devices with 192.168.x.x IPs in datacenter_inventory:")
            for ip, hostname in datacenter_ips[:20]:  # Show first 20
                print(f"  {ip:<16} - {hostname}")
            if len(datacenter_ips) > 20:
                print(f"  ... and {len(datacenter_ips) - 20} more")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_ip_ranges()