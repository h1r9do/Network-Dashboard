#!/usr/bin/env python3
"""
Preview WAN2 updates for Unknown providers with Discount-Tire tag and AT&T/Verizon ARIN data
Shows what would be changed to "cell" speed and "AT&T Cell" or "VZW Cell" provider
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
    
    # Query for WAN2 Unknown providers with Discount-Tire tag and AT&T/Verizon ARIN
    cursor.execute("""
        SELECT 
            e.network_name,
            e.wan2_provider as current_provider,
            e.wan2_speed as current_speed,
            m.wan2_ip,
            m.wan2_arin_provider,
            m.device_tags,
            CASE 
                WHEN m.wan2_arin_provider ILIKE '%at&t%' OR m.wan2_arin_provider ILIKE '%att%' THEN 'AT&T Cell'
                WHEN m.wan2_arin_provider ILIKE '%verizon%' OR m.wan2_arin_provider ILIKE '%vzw%' THEN 'VZW Cell'
                ELSE NULL
            END as new_provider,
            'cell' as new_speed
        FROM enriched_circuits e
        JOIN meraki_inventory m ON e.network_name = m.network_name
        WHERE (e.wan2_provider = 'Unknown' OR e.wan2_provider IS NULL OR e.wan2_provider = 'N/A')
        AND m.device_tags @> ARRAY['Discount-Tire']
        AND m.wan2_arin_provider IS NOT NULL
        AND m.wan2_arin_provider != ''
        AND (
            m.wan2_arin_provider ILIKE '%at&t%' OR 
            m.wan2_arin_provider ILIKE '%att%' OR
            m.wan2_arin_provider ILIKE '%verizon%' OR 
            m.wan2_arin_provider ILIKE '%vzw%'
        )
        AND e.network_name NOT ILIKE '%hub%'
        AND e.network_name NOT ILIKE '%lab%'
        AND e.network_name NOT ILIKE '%voice%'
        AND e.network_name NOT ILIKE '%test%'
        ORDER BY e.network_name
    """)
    
    results = cursor.fetchall()
    
    # Create CSV file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'/usr/local/bin/wan2_cell_updates_preview_{timestamp}.csv'
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow([
            'Network Name',
            'Current WAN2 Provider',
            'Current WAN2 Speed',
            'WAN2 IP',
            'ARIN Provider',
            'New Provider (Proposed)',
            'New Speed (Proposed)',
            'Device Tags'
        ])
        
        # Counters
        att_count = 0
        vzw_count = 0
        
        # Write data
        for row in results:
            # Convert tags to string
            tags = row['device_tags'] if row['device_tags'] else []
            tags_str = ', '.join(tags) if isinstance(tags, list) else str(tags)
            
            writer.writerow([
                row['network_name'],
                row['current_provider'] or 'Unknown',
                row['current_speed'] or 'N/A',
                row['wan2_ip'],
                row['wan2_arin_provider'],
                row['new_provider'],
                row['new_speed'],
                tags_str
            ])
            
            # Count by provider
            if row['new_provider'] == 'AT&T Cell':
                att_count += 1
            elif row['new_provider'] == 'VZW Cell':
                vzw_count += 1
    
    conn.close()
    
    print(f"=== WAN2 Cell Update Preview ===")
    print(f"\nTotal circuits to update: {len(results)}")
    print(f"  AT&T Cell: {att_count}")
    print(f"  VZW Cell: {vzw_count}")
    print(f"\nPreview CSV saved to: {filename}")
    print(f"\nThese are WAN2 interfaces that:")
    print(f"  - Currently show 'Unknown' provider in enriched_circuits")
    print(f"  - Have 'Discount-Tire' tag")
    print(f"  - Have AT&T or Verizon in ARIN provider data")
    print(f"  - Would be updated to 'cell' speed and appropriate cell provider")