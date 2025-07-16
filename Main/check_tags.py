#!/usr/bin/env python3
"""
Check what tags exist in the device_tags field
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='dsrcircuits',
            user='dsruser',
            password='dsrpass123'
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def check_tags():
    """Check what tags exist in device_tags"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get sample device_tags values
        print("=== Sample device_tags values ===")
        cursor.execute("""
            SELECT network_name, device_tags, device_model
            FROM meraki_inventory 
            WHERE device_tags IS NOT NULL 
            ORDER BY network_name
            LIMIT 15;
        """)
        results = cursor.fetchall()
        
        for row in results:
            print(f"Site: {row['network_name']} ({row['device_model']})")
            print(f"  Tags: {row['device_tags']}")
            
            # Try to parse as JSON if it looks like JSON
            if row['device_tags'].startswith('['):
                try:
                    tags_list = json.loads(row['device_tags'])
                    print(f"  Parsed: {tags_list}")
                except:
                    pass
            print()
        
        # Get unique tag patterns
        print("=== Unique tag patterns (first 20) ===")
        cursor.execute("""
            SELECT DISTINCT device_tags, COUNT(*) as count
            FROM meraki_inventory 
            WHERE device_tags IS NOT NULL 
            GROUP BY device_tags
            ORDER BY count DESC
            LIMIT 20;
        """)
        results = cursor.fetchall()
        
        for row in results:
            print(f"Count: {row['count']} - Tags: {row['device_tags']}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Query failed: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    check_tags()