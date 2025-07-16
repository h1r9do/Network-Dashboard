#!/usr/bin/env python3
"""
Debug the modal notes issue - check what's actually being sent
"""

import psycopg2
import json

def main():
    """Debug modal notes"""
    print("🔍 Debugging Modal Notes Issue")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='dsrcircuits',
            user='dsruser',
            password='dsrpass123'
        )
        cursor = conn.cursor()
        
        # Check meraki_inventory for AZP 08
        print("\n📊 Checking meraki_inventory table:")
        cursor.execute("""
            SELECT network_name, device_notes, last_updated
            FROM meraki_inventory
            WHERE network_name = 'AZP 08'
        """)
        
        row = cursor.fetchone()
        if row:
            print(f"   Network: {row[0]}")
            print(f"   Last Updated: {row[2]}")
            print(f"\n   Device Notes (display):")
            print("   " + "-" * 40)
            if row[1]:
                print(row[1])
            print("   " + "-" * 40)
            print(f"\n   Device Notes (repr): {repr(row[1])}")
            
            # Check for literal backslash-n
            if row[1] and '\\n' in row[1]:
                print("\n   ⚠️  FOUND LITERAL \\n IN DATABASE!")
        
        # Check enriched_circuits table
        print("\n\n📊 Checking enriched_circuits table:")
        cursor.execute("""
            SELECT site_name, device_notes, last_updated
            FROM enriched_circuits
            WHERE site_name = 'AZP 08'
        """)
        
        row = cursor.fetchone()
        if row:
            print(f"   Site: {row[0]}")
            print(f"   Last Updated: {row[2]}")
            print(f"\n   Device Notes (display):")
            print("   " + "-" * 40)
            if row[1]:
                print(row[1])
            print("   " + "-" * 40)
            print(f"\n   Device Notes (repr): {repr(row[1])}")
            
            # Check for literal backslash-n
            if row[1] and '\\n' in row[1]:
                print("\n   ⚠️  FOUND LITERAL \\n IN DATABASE!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    main()