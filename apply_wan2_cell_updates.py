#!/usr/bin/env python3
"""
Apply WAN2 cell updates to enriched_circuits table
Updates Unknown providers with Discount-Tire tag and AT&T/Verizon ARIN data
"""

import psycopg2
import psycopg2.extras
from config import Config
import re
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
    
    print(f"=== WAN2 Cell Update Script ===")
    print(f"Started at: {datetime.now()}")
    print()
    
    # First, let's count what we're going to update
    cursor.execute("""
        SELECT COUNT(*) as count
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
    """)
    
    total_count = cursor.fetchone()['count']
    print(f"Total records to update: {total_count}")
    
    if total_count == 0:
        print("No records to update.")
        conn.close()
        exit()
    
    # Perform the update
    try:
        # Update AT&T entries
        cursor.execute("""
            UPDATE enriched_circuits
            SET 
                wan2_provider = 'AT&T Cell',
                wan2_speed = 'cell',
                last_updated = NOW()
            FROM meraki_inventory m
            WHERE enriched_circuits.network_name = m.network_name
            AND (enriched_circuits.wan2_provider = 'Unknown' OR enriched_circuits.wan2_provider IS NULL OR enriched_circuits.wan2_provider = 'N/A')
            AND m.device_tags @> ARRAY['Discount-Tire']
            AND m.wan2_arin_provider IS NOT NULL
            AND m.wan2_arin_provider != ''
            AND (m.wan2_arin_provider ILIKE '%at&t%' OR m.wan2_arin_provider ILIKE '%att%')
            AND enriched_circuits.network_name NOT ILIKE '%hub%'
            AND enriched_circuits.network_name NOT ILIKE '%lab%'
            AND enriched_circuits.network_name NOT ILIKE '%voice%'
            AND enriched_circuits.network_name NOT ILIKE '%test%'
        """)
        
        att_updated = cursor.rowcount
        print(f"\nUpdated {att_updated} entries to 'AT&T Cell'")
        
        # Update Verizon entries
        cursor.execute("""
            UPDATE enriched_circuits
            SET 
                wan2_provider = 'VZW Cell',
                wan2_speed = 'cell',
                last_updated = NOW()
            FROM meraki_inventory m
            WHERE enriched_circuits.network_name = m.network_name
            AND (enriched_circuits.wan2_provider = 'Unknown' OR enriched_circuits.wan2_provider IS NULL OR enriched_circuits.wan2_provider = 'N/A')
            AND m.device_tags @> ARRAY['Discount-Tire']
            AND m.wan2_arin_provider IS NOT NULL
            AND m.wan2_arin_provider != ''
            AND (m.wan2_arin_provider ILIKE '%verizon%' OR m.wan2_arin_provider ILIKE '%vzw%')
            AND enriched_circuits.network_name NOT ILIKE '%hub%'
            AND enriched_circuits.network_name NOT ILIKE '%lab%'
            AND enriched_circuits.network_name NOT ILIKE '%voice%'
            AND enriched_circuits.network_name NOT ILIKE '%test%'
        """)
        
        vzw_updated = cursor.rowcount
        print(f"Updated {vzw_updated} entries to 'VZW Cell'")
        
        # Commit the changes
        conn.commit()
        
        print(f"\n✅ Successfully updated {att_updated + vzw_updated} total records")
        
        # Verify a few updates
        print("\n=== Verification - Sample of Updated Records ===")
        cursor.execute("""
            SELECT network_name, wan2_provider, wan2_speed
            FROM enriched_circuits
            WHERE wan2_provider IN ('AT&T Cell', 'VZW Cell')
            AND wan2_speed = 'cell'
            ORDER BY last_updated DESC
            LIMIT 10
        """)
        
        for row in cursor.fetchall():
            print(f"  {row['network_name']}: {row['wan2_provider']}, Speed: {row['wan2_speed']}")
        
    except Exception as e:
        print(f"\n❌ Error during update: {e}")
        conn.rollback()
    
    finally:
        conn.close()
        print(f"\nCompleted at: {datetime.now()}")