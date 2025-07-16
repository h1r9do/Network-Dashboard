#!/usr/bin/env python3
"""
Debug script to check static IP assignments in the database
"""

import psycopg2
from psycopg2.extras import RealDictCursor

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

def debug_assignments():
    """Debug static IP assignments"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check what assignment types exist
        print("=== WAN Assignment Types ===")
        cursor.execute("""
            SELECT wan1_assignment, COUNT(*) as count1
            FROM meraki_inventory 
            WHERE wan1_assignment IS NOT NULL
            GROUP BY wan1_assignment
            ORDER BY count1 DESC;
        """)
        results = cursor.fetchall()
        print("WAN1 Assignments:")
        for row in results:
            print(f"  {row['wan1_assignment']}: {row['count1']}")
        
        cursor.execute("""
            SELECT wan2_assignment, COUNT(*) as count2
            FROM meraki_inventory 
            WHERE wan2_assignment IS NOT NULL
            GROUP BY wan2_assignment
            ORDER BY count2 DESC;
        """)
        results = cursor.fetchall()
        print("\nWAN2 Assignments:")
        for row in results:
            print(f"  {row['wan2_assignment']}: {row['count2']}")
        
        # Check sample records with IP addresses
        print("\n=== Sample Records with IP Addresses ===")
        cursor.execute("""
            SELECT network_name, wan1_ip, wan1_assignment, wan2_ip, wan2_assignment
            FROM meraki_inventory 
            WHERE (wan1_ip IS NOT NULL AND wan1_ip != '') 
               OR (wan2_ip IS NOT NULL AND wan2_ip != '')
            LIMIT 10;
        """)
        results = cursor.fetchall()
        for row in results:
            print(f"Site: {row['network_name']}")
            print(f"  WAN1: {row['wan1_ip']} ({row['wan1_assignment']})")
            print(f"  WAN2: {row['wan2_ip']} ({row['wan2_assignment']})")
            print()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Query failed: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    debug_assignments()