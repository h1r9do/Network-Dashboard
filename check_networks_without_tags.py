#!/usr/bin/env python3
"""
Check for networks in Meraki inventory without any tags
"""

import psycopg2
import psycopg2.extras
from config import Config
import re
import csv
from datetime import datetime

# Parse database connection
match = re.match(r'postgresql://(.+):(.+)@(.+):(\d+)/(.+)', Config.SQLALCHEMY_DATABASE_URI)
if match:
    user, password, host, port, database = match.groups()
    
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password
    )
    
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    print("=== Networks Without Tags in Meraki Inventory ===\n")
    
    # Query for networks without tags
    cursor.execute("""
        SELECT DISTINCT
            network_name,
            network_id,
            device_serial,
            device_model,
            device_name,
            device_tags,
            wan1_ip,
            wan2_ip,
            organization_name,
            last_updated
        FROM meraki_inventory
        WHERE (device_tags IS NULL OR device_tags = '{}' OR array_length(device_tags, 1) IS NULL)
        AND device_model LIKE 'MX%'
        ORDER BY network_name
    """)
    
    results = cursor.fetchall()
    
    # Create CSV file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'/usr/local/bin/networks_without_tags_{timestamp}.csv'
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow([
            'Network Name',
            'Network ID',
            'Device Serial',
            'Device Model',
            'Device Name',
            'WAN1 IP',
            'WAN2 IP',
            'Organization',
            'Last Updated'
        ])
        
        # Write data
        for row in results:
            writer.writerow([
                row['network_name'],
                row['network_id'],
                row['device_serial'],
                row['device_model'],
                row['device_name'] or 'N/A',
                row['wan1_ip'] or 'N/A',
                row['wan2_ip'] or 'N/A',
                row['organization_name'],
                row['last_updated'].strftime('%Y-%m-%d %H:%M:%S') if row['last_updated'] else 'N/A'
            ])
    
    conn.close()
    
    print(f"Total networks without tags: {len(results)}")
    print(f"\nCSV file saved to: {filename}")
    
    # Show first 20 examples
    if results:
        print("\nFirst 20 networks without tags:")
        print("-" * 80)
        for i, row in enumerate(results[:20]):
            print(f"{row['network_name']:<30} Model: {row['device_model']:<10} IPs: WAN1={row['wan1_ip'] or 'None'}, WAN2={row['wan2_ip'] or 'None'}")