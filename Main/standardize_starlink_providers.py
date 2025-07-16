#!/usr/bin/env python3
"""
One-time script to standardize all satellite providers to 'Starlink' in the database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2
from datetime import datetime

def standardize_starlink_providers():
    """Update all satellite speed entries to have 'Starlink' as provider"""
    
    # Create database connection
    conn = psycopg2.connect("postgresql://meraki:M3r@k1_2024!@localhost/meraki_database")
    
    try:
        cursor = conn.cursor()
        
        # First, let's check how many records we'll be updating
        cursor.execute("""
            SELECT COUNT(*) 
            FROM enriched_circuits 
            WHERE LOWER(wan1_speed) = 'satellite' 
            AND (wan1_provider != 'Starlink' OR wan1_provider IS NULL)
        """)
        check_wan1 = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM enriched_circuits 
            WHERE LOWER(wan2_speed) = 'satellite' 
            AND (wan2_provider != 'Starlink' OR wan2_provider IS NULL)
        """)
        check_wan2 = cursor.fetchone()[0]
        
        print(f"Found {check_wan1} WAN1 satellite entries to update")
        print(f"Found {check_wan2} WAN2 satellite entries to update")
        
        if check_wan1 == 0 and check_wan2 == 0:
            print("No updates needed - all satellite entries already show 'Starlink'")
            return
        
        # Update WAN1 providers
        if check_wan1 > 0:
            cursor.execute("""
                UPDATE enriched_circuits 
                SET wan1_provider = 'Starlink',
                    last_updated = %s
                WHERE LOWER(wan1_speed) = 'satellite'
                AND (wan1_provider != 'Starlink' OR wan1_provider IS NULL)
            """, (datetime.utcnow(),))
            print(f"Updated {cursor.rowcount} WAN1 entries to 'Starlink'")
        
        # Update WAN2 providers
        if check_wan2 > 0:
            cursor.execute("""
                UPDATE enriched_circuits 
                SET wan2_provider = 'Starlink',
                    last_updated = %s
                WHERE LOWER(wan2_speed) = 'satellite'
                AND (wan2_provider != 'Starlink' OR wan2_provider IS NULL)
            """, (datetime.utcnow(),))
            print(f"Updated {cursor.rowcount} WAN2 entries to 'Starlink'")
        
        # Commit the changes
        conn.commit()
        print("\nDatabase update complete!")
        
        # Show some examples of what was updated
        cursor.execute("""
            SELECT network_name, wan1_provider, wan1_speed, wan2_provider, wan2_speed
            FROM enriched_circuits
            WHERE LOWER(wan1_speed) = 'satellite' OR LOWER(wan2_speed) = 'satellite'
            LIMIT 5
        """)
        
        examples = cursor.fetchall()
        print("\nExample updated records:")
        for row in examples:
            print(f"  {row[0]}: WAN1={row[1]}/{row[2]}, WAN2={row[3]}/{row[4]}")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("Standardizing Starlink provider names in database...")
    standardize_starlink_providers()