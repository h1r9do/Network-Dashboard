#!/usr/bin/env python3
"""
Reimport CSV maintaining exact row order
"""
import csv
import psycopg2
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsruser'
}

def reimport_with_order():
    """Clear and reimport CSV with row order preserved"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        # First add a row_order column if it doesn't exist
        cur.execute("""
            ALTER TABLE inventory_web_format 
            ADD COLUMN IF NOT EXISTS row_order INTEGER
        """)
        conn.commit()
        
        # Clear the table
        cur.execute("TRUNCATE TABLE inventory_web_format")
        conn.commit()
        
        # Read and import CSV with row order
        csv_file = '/usr/local/bin/Main/inventory_ultimate_final.csv'
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            row_order = 0
            for row in reader:
                row_order += 1
                
                cur.execute("""
                    INSERT INTO inventory_web_format (
                        hostname, ip_address, position, model, serial_number,
                        port_location, vendor, notes, row_order, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    row['hostname'] or '',
                    row['ip_address'] or '',
                    row['position'],
                    row['model'],
                    row['serial_number'],
                    row['port_location'] or '',
                    row['vendor'] or '',
                    row['notes'] or '',
                    row_order,
                    datetime.now(),
                    datetime.now()
                ))
                
                if row_order % 100 == 0:
                    print(f"Imported {row_order} rows...")
        
        conn.commit()
        print(f"\nImport complete! Total rows: {row_order}")
        
        # Verify
        cur.execute("SELECT COUNT(*) FROM inventory_web_format")
        print(f"Database rows: {cur.fetchone()[0]}")
        
        # Check order
        print("\nFirst 10 rows in order:")
        cur.execute("""
            SELECT row_order, hostname, position, model, serial_number 
            FROM inventory_web_format 
            ORDER BY row_order 
            LIMIT 10
        """)
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1] or '(empty)'} - {row[2]} - {row[3]}")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("Reimporting CSV with exact row order...")
    reimport_with_order()