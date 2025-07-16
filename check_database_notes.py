#!/usr/bin/env python3
"""
Check database notes for AZP 08
"""

import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost',
        database='dsrcircuits',
        user='dsruser',
        password='dsrpass123'
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT network_name, device_notes 
        FROM meraki_inventory 
        WHERE network_name = 'AZP 08'
    """)
    
    row = cursor.fetchone()
    if row:
        print(f"Network: {row[0]}")
        print(f"Notes repr: {repr(row[1])}")
        print(f"Notes display:\n{row[1]}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")