#!/usr/bin/env python3
"""
Import inventory_ultimate_final.csv directly into inventory_web_format table
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

def import_csv_to_db():
    """Import CSV file directly into database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    csv_file = '/usr/local/bin/Main/inventory_ultimate_final.csv'
    
    try:
        # Read CSV file
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            row_count = 0
            for row in reader:
                # Insert each row
                cur.execute("""
                    INSERT INTO inventory_web_format (
                        hostname, ip_address, position, model, serial_number,
                        port_location, vendor, notes, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    row['hostname'] or '',
                    row['ip_address'] or '',
                    row['position'],
                    row['model'],
                    row['serial_number'],
                    row['port_location'] or '',
                    row['vendor'] or '',
                    row['notes'] or '',
                    datetime.now(),
                    datetime.now()
                ))
                
                row_count += 1
                if row_count % 100 == 0:
                    print(f"Imported {row_count} rows...")
        
        conn.commit()
        print(f"\nImport complete! Total rows imported: {row_count}")
        
        # Verify import
        cur.execute("SELECT COUNT(*) FROM inventory_web_format")
        db_count = cur.fetchone()[0]
        print(f"Database row count: {db_count}")
        
        # Check for FEX entries
        cur.execute("SELECT COUNT(*) FROM inventory_web_format WHERE position LIKE 'FEX-%'")
        fex_count = cur.fetchone()[0]
        print(f"FEX entries: {fex_count}")
        
        # Show sample data
        print("\nSample data:")
        cur.execute("""
            SELECT hostname, ip_address, position, model, serial_number 
            FROM inventory_web_format 
            LIMIT 10
        """)
        for row in cur.fetchall():
            print(f"  {row}")
            
    except Exception as e:
        print(f"Error during import: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("Importing inventory_ultimate_final.csv to inventory_web_format table...")
    import_csv_to_db()