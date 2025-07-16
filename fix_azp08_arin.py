#!/usr/bin/env python3
"""
Quick fix for AZP 08 ARIN provider
"""

import psycopg2

def main():
    """Fix AZP 08 ARIN provider"""
    print("🔧 Fixing AZP 08 ARIN Provider")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='dsrcircuits',
            user='dsruser',
            password='dsrpass123'
        )
        cursor = conn.cursor()
        
        # Update AZP 08
        cursor.execute("""
            UPDATE meraki_inventory 
            SET wan1_arin_provider = 'Cox Communications Inc.'
            WHERE network_name = 'AZP 08' AND wan1_ip = '68.15.185.94'
        """)
        
        conn.commit()
        print("✅ Updated AZP 08 WAN1 ARIN provider to 'Cox Communications Inc.'")
        
        # Verify
        cursor.execute("""
            SELECT network_name, wan1_ip, wan1_arin_provider, wan2_ip, wan2_arin_provider
            FROM meraki_inventory
            WHERE network_name = 'AZP 08'
        """)
        
        row = cursor.fetchone()
        if row:
            print(f"\n📊 AZP 08 Current Data:")
            print(f"   WAN1: {row[1]} → {row[2]}")
            print(f"   WAN2: {row[3]} → {row[4]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ AZP 08 ARIN fix completed!")
        print("\n📝 NOTE: The modal should now show:")
        print("   - Proper line breaks in the notes (after browser refresh)")
        print("   - Cox Communications Inc. for WAN1 ARIN")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    main()