#!/usr/bin/env python3
"""
Update network tags for untagged networks based on classifications
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
    
    print("=== Network Tag Updates ===")
    print(f"Started at: {datetime.now()}")
    print()
    
    # Define the updates
    updates = [
        # Regional Offices (all _00 ending networks)
        {
            'pattern': "network_name LIKE '%_00'",
            'tag': 'Regional-Office',
            'description': 'Regional Office networks ending in _00'
        },
        # MDC
        {
            'pattern': "network_name = 'WAX 01'",
            'tag': 'MDC',
            'description': 'WAX 01 as MDC'
        },
        # Lab
        {
            'pattern': "network_name = 'VAF 01 - appliance'",
            'tag': 'Lab',
            'description': 'VAF 01 as Lab'
        },
        # Discount-Tire stores (remaining untagged networks that aren't special)
        {
            'pattern': """network_name NOT LIKE '%_00' 
                         AND network_name != 'WAX 01' 
                         AND network_name != 'VAF 01 - appliance'
                         AND network_name != 'Desert Ridge Building I Security'""",
            'tag': 'Discount-Tire',
            'description': 'Remaining networks as Discount-Tire stores'
        }
    ]
    
    try:
        total_updated = 0
        
        for update in updates:
            # First count what we'll update
            cursor.execute(f"""
                SELECT COUNT(*) as count
                FROM meraki_inventory
                WHERE (device_tags IS NULL OR device_tags = '{{}}' OR array_length(device_tags, 1) IS NULL)
                AND device_model LIKE 'MX%'
                AND ({update['pattern']})
            """)
            
            count = cursor.fetchone()['count']
            print(f"{update['description']}: {count} networks")
            
            if count > 0:
                # Perform the update
                cursor.execute(f"""
                    UPDATE meraki_inventory
                    SET device_tags = ARRAY['{update['tag']}']
                    WHERE (device_tags IS NULL OR device_tags = '{{}}' OR array_length(device_tags, 1) IS NULL)
                    AND device_model LIKE 'MX%'
                    AND ({update['pattern']})
                """)
                
                updated = cursor.rowcount
                total_updated += updated
                print(f"  ✅ Updated {updated} records with '{update['tag']}' tag")
                
                # Show examples
                cursor.execute(f"""
                    SELECT network_name, device_tags
                    FROM meraki_inventory
                    WHERE device_tags = ARRAY['{update['tag']}']
                    AND device_model LIKE 'MX%'
                    AND ({update['pattern']})
                    LIMIT 5
                """)
                
                examples = cursor.fetchall()
                for example in examples:
                    print(f"    {example['network_name']}: {example['device_tags']}")
            
            print()
        
        # Commit all changes
        conn.commit()
        print(f"✅ Successfully updated {total_updated} total networks")
        
        # Final verification
        print("\n=== Final Verification ===")
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM meraki_inventory
            WHERE (device_tags IS NULL OR device_tags = '{}' OR array_length(device_tags, 1) IS NULL)
            AND device_model LIKE 'MX%'
        """)
        
        remaining = cursor.fetchone()['count']
        print(f"Networks still without tags: {remaining}")
        
        if remaining > 0:
            cursor.execute("""
                SELECT network_name
                FROM meraki_inventory
                WHERE (device_tags IS NULL OR device_tags = '{}' OR array_length(device_tags, 1) IS NULL)
                AND device_model LIKE 'MX%'
                ORDER BY network_name
            """)
            
            untagged = cursor.fetchall()
            print("Remaining untagged networks:")
            for network in untagged:
                print(f"  {network['network_name']}")
        
    except Exception as e:
        print(f"❌ Error during update: {e}")
        conn.rollback()
    
    finally:
        conn.close()
        print(f"\nCompleted at: {datetime.now()}")