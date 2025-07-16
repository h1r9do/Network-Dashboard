#!/usr/bin/env python3
"""
Add Site column to database and populate based on IP address
"""
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsruser'
}

def get_site_from_ip(ip):
    """Determine site based on IP address"""
    if not ip:
        return 'Unknown'
    
    if ip.startswith('10.0.'):
        return 'AZ-Scottsdale-HQ-Corp'
    elif ip.startswith('10.101.'):
        return 'AZ-Alameda-DC'
    elif ip.startswith('10.44.'):
        return 'Equinix-Seattle'
    elif ip.startswith('10.41.'):
        return 'AZ-Desert-Ridge'
    elif ip.startswith('10.42.'):
        return 'TX-Dallas-DC'
    elif ip.startswith('10.43.'):
        return 'GA-Atlanta-DC'
    else:
        return 'Other'

def get_site_from_hostname(hostname):
    """Determine site based on hostname patterns"""
    if not hostname:
        return None
    
    hostname_lower = hostname.lower()
    if hostname_lower.startswith(('ala-', 'al-', 'ala')):
        return 'AZ-Alameda-DC'
    elif hostname_lower.startswith(('mdf-', 'n5k-', 'n7k-', '2960')):
        return 'AZ-Scottsdale-HQ-Corp'
    elif 'dtc_phx' in hostname_lower:
        return 'AZ-Scottsdale-HQ-Corp'
    
    return None

def add_site_column():
    """Add site column and populate it"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # Add site column if it doesn't exist
        cur.execute("""
            ALTER TABLE inventory_web_format 
            ADD COLUMN IF NOT EXISTS site VARCHAR(50)
        """)
        conn.commit()
        print("Added site column")
        
        # Get all rows with their parent device info
        cur.execute("""
            SELECT id, hostname, ip_address, parent_hostname
            FROM inventory_web_format
            ORDER BY row_order
        """)
        
        rows = cur.fetchall()
        print(f"Processing {len(rows)} rows...")
        
        # Build a map of parent hostnames to their IPs
        parent_ips = {}
        for row in rows:
            id, hostname, ip, parent = row
            if hostname and ip:
                parent_ips[hostname] = ip
        
        # Update each row with site information
        for row in rows:
            id, hostname, ip, parent = row
            
            # Try hostname first
            site = get_site_from_hostname(hostname or parent)
            
            # If no site from hostname, try IP
            if not site:
                # For components, use parent's IP
                if not ip and parent and parent in parent_ips:
                    ip = parent_ips[parent]
                site = get_site_from_ip(ip)
            
            # Update the row
            cur.execute("""
                UPDATE inventory_web_format 
                SET site = %s 
                WHERE id = %s
            """, (site, id))
        
        conn.commit()
        print("Updated all rows with site information")
        
        # Verify the update
        cur.execute("""
            SELECT site, COUNT(*) 
            FROM inventory_web_format 
            GROUP BY site 
            ORDER BY site
        """)
        
        print("\nSite distribution:")
        for site, count in cur.fetchall():
            print(f"  {site}: {count} rows")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    add_site_column()