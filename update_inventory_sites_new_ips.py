#!/usr/bin/env python3
"""
Update inventory sites for new IP ranges:
- 192.168.255.x -> AZ-Scottsdale-HQ-Corp
- 172.16.4.x -> AZ-Scottsdale-HQ-Corp
"""
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsruser'
}

def update_sites():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # First check what we have
        cursor.execute("""
            SELECT COUNT(*), ip_address 
            FROM inventory_web_format 
            WHERE ip_address LIKE '192.168.255.%' 
               OR ip_address LIKE '172.16.4.%'
            GROUP BY ip_address
        """)
        
        print("Found devices with new IP ranges:")
        for row in cursor.fetchall():
            count, ip = row
            print(f"  {ip} - {count} devices/components")
        
        # Update devices with 192.168.255.x IPs
        cursor.execute("""
            UPDATE inventory_web_format
            SET site = 'AZ-Scottsdale-HQ-Corp'
            WHERE ip_address LIKE '192.168.255.%'
        """)
        count_192 = cursor.rowcount
        print(f"\nUpdated {count_192} rows with 192.168.255.x IPs to AZ-Scottsdale-HQ-Corp")
        
        # Update devices with 172.16.4.x IPs  
        cursor.execute("""
            UPDATE inventory_web_format
            SET site = 'AZ-Scottsdale-HQ-Corp'
            WHERE ip_address LIKE '172.16.4.%'
        """)
        count_172 = cursor.rowcount
        print(f"Updated {count_172} rows with 172.16.4.x IPs to AZ-Scottsdale-HQ-Corp")
        
        # Also update components (rows without IP) that have parent devices with these IPs
        cursor.execute("""
            UPDATE inventory_web_format child
            SET site = 'AZ-Scottsdale-HQ-Corp'
            FROM inventory_web_format parent
            WHERE child.parent_hostname = parent.hostname
              AND child.ip_address = ''
              AND (parent.ip_address LIKE '192.168.255.%' 
                   OR parent.ip_address LIKE '172.16.4.%')
        """)
        count_components = cursor.rowcount
        print(f"Updated {count_components} component rows based on parent device IPs")
        
        conn.commit()
        print(f"\nTotal updates: {count_192 + count_172 + count_components} rows")
        
        # Show updated devices
        cursor.execute("""
            SELECT hostname, ip_address, position, site
            FROM inventory_web_format
            WHERE site = 'AZ-Scottsdale-HQ-Corp'
              AND (ip_address LIKE '192.168.255.%' 
                   OR ip_address LIKE '172.16.4.%')
            ORDER BY ip_address, hostname
        """)
        
        print("\nUpdated devices:")
        for row in cursor.fetchall():
            hostname, ip, position, site = row
            print(f"  {hostname or '(component)'} - {ip} - {position} - {site}")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_sites()