#!/usr/bin/env python3
"""
Clear failed ARIN lookups from RDAP cache to allow retry
"""

import psycopg2
from datetime import datetime

def clear_failed_lookups():
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    print("=== CLEARING FAILED ARIN LOOKUPS ===\n")
    
    # First, check how many we're going to delete
    cursor.execute("""
        SELECT COUNT(*) 
        FROM rdap_cache 
        WHERE provider_name = 'Unknown' 
        AND rdap_response IS NULL
    """)
    count = cursor.fetchone()[0]
    
    print(f"Found {count} failed ARIN lookups to clear")
    
    if count > 0:
        # Delete failed lookups
        cursor.execute("""
            DELETE FROM rdap_cache 
            WHERE provider_name = 'Unknown' 
            AND rdap_response IS NULL
        """)
        
        print(f"Deleted {cursor.rowcount} failed lookups from cache")
        
        # Commit the changes
        conn.commit()
        
        # Show remaining cache stats
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN provider_name = 'Unknown' THEN 1 END) as unknown_count
            FROM rdap_cache
        """)
        total, unknown = cursor.fetchone()
        print(f"\nRemaining cache entries: {total} (Unknown: {unknown})")
        
        print("\n✅ Failed lookups cleared. Next run of nightly_meraki_db.py will retry these IPs")
    else:
        print("No failed lookups to clear")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    clear_failed_lookups()