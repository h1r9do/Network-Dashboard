#!/usr/bin/env python3
"""
Update inventory data to new format with device name in every row
"""
import psycopg2
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsruser'
}

def update_to_new_format():
    """Update inventory to show device name in every row"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # First, get all data ordered by row_order
        cur.execute("""
            SELECT id, hostname, ip_address, position, model, serial_number, 
                   port_location, vendor, notes, row_order
            FROM inventory_web_format 
            ORDER BY row_order
        """)
        
        all_rows = cur.fetchall()
        current_device = None
        current_device_ip = None
        
        updates = []
        
        for row in all_rows:
            id, hostname, ip, position, model, serial, port_loc, vendor, notes, row_order = row
            
            # If this is a device row (has hostname)
            if hostname and position in ['Master', 'Standalone', 'Parent Switch']:
                current_device = hostname
                current_device_ip = ip
                relationship = position
                parent_hostname = hostname
            elif hostname and position == 'Slave':
                # Slave has hostname in some cases
                relationship = position
                parent_hostname = current_device or hostname
            else:
                # Component row - use current device
                if position == 'Slave':
                    relationship = 'Slave'
                elif position in ['Module', 'SFP', 'FEX-105', 'FEX-106', 'FEX-107', 'FEX-108']:
                    relationship = 'Component'
                else:
                    relationship = position
                parent_hostname = current_device
            
            updates.append((parent_hostname, relationship, id))
        
        # Update all rows
        print(f"Updating {len(updates)} rows...")
        for parent, rel, id in updates:
            cur.execute("""
                UPDATE inventory_web_format 
                SET parent_hostname = %s, relationship = %s
                WHERE id = %s
            """, (parent, rel, id))
        
        conn.commit()
        print("Update complete!")
        
        # Verify the update
        cur.execute("""
            SELECT parent_hostname, relationship, position, model, serial_number 
            FROM inventory_web_format 
            ORDER BY row_order 
            LIMIT 20
        """)
        
        print("\nFirst 20 rows after update:")
        for row in cur.fetchall():
            print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("Updating inventory to new format...")
    update_to_new_format()