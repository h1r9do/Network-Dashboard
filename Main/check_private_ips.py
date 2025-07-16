#!/usr/bin/env python3
"""
Check for sites with private IP addresses
"""
import psycopg2
import re
import ipaddress

# Read config
with open('/usr/local/bin/Main/config.py', 'r') as f:
    config_content = f.read()
    
uri_match = re.search(r"SQLALCHEMY_DATABASE_URI = ['\"]postgresql://([^:]+):([^@]+)@([^/]+)/([^'\"]+)['\"]", config_content)
if uri_match:
    user, password, host, database = uri_match.groups()

def is_private_ip(ip):
    """Check if IP address is private."""
    try:
        return ipaddress.ip_address(ip).is_private
    except:
        return False

try:
    conn = psycopg2.connect(
        host=host.split(':')[0],
        port=5432,
        database=database,
        user=user,
        password=password
    )
    cursor = conn.cursor()
    
    # Check Meraki inventory for private IPs
    cursor.execute("""
        SELECT network_name, device_name, wan1_ip, wan2_ip, last_updated
        FROM meraki_inventory
        WHERE wan1_ip IS NOT NULL OR wan2_ip IS NOT NULL
        ORDER BY network_name
    """)
    
    private_ip_sites = []
    total_sites = 0
    
    for row in cursor.fetchall():
        total_sites += 1
        network_name, device_name, wan1_ip, wan2_ip, last_updated = row
        
        has_private = False
        private_info = []
        
        if wan1_ip and is_private_ip(wan1_ip):
            has_private = True
            private_info.append(f"WAN1: {wan1_ip}")
            
        if wan2_ip and is_private_ip(wan2_ip):
            has_private = True
            private_info.append(f"WAN2: {wan2_ip}")
            
        if has_private:
            private_ip_sites.append({
                'network': network_name,
                'device': device_name,
                'private_ips': private_info,
                'last_updated': last_updated
            })
    
    print(f"Total sites checked: {total_sites}")
    print(f"Sites with private IPs: {len(private_ip_sites)}")
    
    if private_ip_sites:
        print("\nSites with private IP addresses:")
        print("-" * 80)
        
        # Group by common private IPs
        by_ip_pattern = {}
        for site in private_ip_sites:
            for ip_info in site['private_ips']:
                ip = ip_info.split(': ')[1]
                pattern = '.'.join(ip.split('.')[:3]) + '.x'
                if pattern not in by_ip_pattern:
                    by_ip_pattern[pattern] = []
                by_ip_pattern[pattern].append(site)
        
        # Show summary by pattern
        print("\nSummary by IP pattern:")
        for pattern, sites in sorted(by_ip_pattern.items()):
            print(f"\n{pattern} - {len(sites)} sites:")
            for site in sites[:5]:  # Show first 5
                print(f"  - {site['network']} ({', '.join(site['private_ips'])}) - Updated: {site['last_updated']}")
            if len(sites) > 5:
                print(f"  ... and {len(sites) - 5} more")
    
    # Check when the nightly script last ran
    cursor.execute("""
        SELECT MAX(last_updated) as last_run
        FROM meraki_inventory
    """)
    last_run = cursor.fetchone()[0]
    print(f"\n\nLast nightly Meraki script run: {last_run}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()