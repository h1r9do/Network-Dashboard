#!/usr/bin/env python3
"""
Import consolidated inventory data into database
"""
import json
import psycopg2
from psycopg2.extras import Json
import csv
from datetime import datetime
import re

class ConsolidatedInventoryImporter:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            database="network_inventory",
            user="postgres",
            password="postgres"
        )
        self.cursor = self.conn.cursor()
        
    def ensure_table_structure(self):
        """Ensure the database table exists with proper structure"""
        print("Ensuring table structure...")
        
        # Create main inventory table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS comprehensive_device_inventory (
                id SERIAL PRIMARY KEY,
                device_name VARCHAR(255) UNIQUE NOT NULL,
                ip_address INET NOT NULL,
                entity_data JSONB,
                physical_inventory JSONB,
                summary JSONB,
                collection_timestamp TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_device_inventory_device_name 
            ON comprehensive_device_inventory(device_name);
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_device_inventory_physical_gin 
            ON comprehensive_device_inventory USING gin(physical_inventory);
        """)
        
        # Create web format table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_web_format (
                id SERIAL PRIMARY KEY,
                hostname VARCHAR(255),
                ip_address VARCHAR(45),
                position VARCHAR(50),
                model VARCHAR(255),
                serial_number VARCHAR(255),
                port_location VARCHAR(255),
                vendor VARCHAR(100),
                notes VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_web_format_hostname 
            ON inventory_web_format(hostname);
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_web_format_serial 
            ON inventory_web_format(serial_number);
        """)
        
        self.conn.commit()
        print("✓ Table structure ready")
    
    def import_consolidated_json(self):
        """Import the consolidated JSON data"""
        print("\nImporting consolidated inventory JSON...")
        
        try:
            with open('/usr/local/bin/Main/physical_inventory_consolidated.json', 'r') as f:
                devices = json.load(f)
        except FileNotFoundError:
            print("Consolidated file not found, trying original...")
            with open('/usr/local/bin/Main/physical_inventory_stacks_output.json', 'r') as f:
                devices = json.load(f)
        
        collection_time = datetime.now()
        imported_count = 0
        
        for device in devices:
            try:
                # Insert into comprehensive_device_inventory
                self.cursor.execute("""
                    INSERT INTO comprehensive_device_inventory 
                    (device_name, ip_address, entity_data, physical_inventory, 
                     summary, collection_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (device_name) DO UPDATE SET
                        ip_address = EXCLUDED.ip_address,
                        entity_data = EXCLUDED.entity_data,
                        physical_inventory = EXCLUDED.physical_inventory,
                        summary = EXCLUDED.summary,
                        collection_timestamp = EXCLUDED.collection_timestamp,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    device['hostname'],
                    device['ip'],
                    Json(device.get('entity_data', {})),
                    Json(device['physical_inventory']),
                    Json(device['summary']),
                    collection_time
                ))
                imported_count += 1
                
            except Exception as e:
                print(f"Error importing {device['hostname']}: {str(e)}")
        
        self.conn.commit()
        print(f"✓ Imported {imported_count} devices into comprehensive_device_inventory")
        
        return devices
    
    def import_web_format_csv(self):
        """Import the CSV data for web display"""
        print("\nImporting web format CSV...")
        
        # Clear existing data
        self.cursor.execute("TRUNCATE TABLE inventory_web_format")
        
        imported_count = 0
        with open('/usr/local/bin/Main/inventory_ultimate_final.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:
                try:
                    self.cursor.execute("""
                        INSERT INTO inventory_web_format 
                        (hostname, ip_address, position, model, serial_number, 
                         port_location, vendor, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        row['hostname'] or None,
                        row['ip_address'] or None,
                        row['position'],
                        row['model'],
                        row['serial_number'],
                        row['port_location'] or None,
                        row['vendor'] or None,
                        row['notes'] or None
                    ))
                    imported_count += 1
                    
                except Exception as e:
                    print(f"Error importing row: {str(e)}")
                    print(f"Row data: {row}")
        
        self.conn.commit()
        print(f"✓ Imported {imported_count} rows into inventory_web_format")
    
    def verify_import(self):
        """Verify the import was successful"""
        print("\n=== Import Verification ===")
        
        # Check comprehensive_device_inventory
        self.cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT device_name) as unique_devices
            FROM comprehensive_device_inventory
        """)
        result = self.cursor.fetchone()
        print(f"\nComprehensive inventory:")
        print(f"  Total records: {result[0]}")
        print(f"  Unique devices: {result[1]}")
        
        # Check for VDC consolidation
        self.cursor.execute("""
            SELECT device_name, summary->>'consolidated_vdcs' as vdcs
            FROM comprehensive_device_inventory
            WHERE summary->>'consolidated_vdcs' IS NOT NULL
            LIMIT 5
        """)
        vdc_devices = self.cursor.fetchall()
        if vdc_devices:
            print(f"\nVDC consolidated devices:")
            for name, vdcs in vdc_devices:
                print(f"  {name}: {vdcs}")
        
        # Check web format
        self.cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT serial_number) as unique_serials,
                   COUNT(DISTINCT hostname) as devices
            FROM inventory_web_format
            WHERE hostname IS NOT NULL AND hostname != ''
        """)
        result = self.cursor.fetchone()
        print(f"\nWeb format inventory:")
        print(f"  Total rows: {result[0]}")
        print(f"  Unique serials: {result[1]}")
        print(f"  Devices: {result[2]}")
        
        # Check for duplicates
        self.cursor.execute("""
            SELECT serial_number, COUNT(*) as count
            FROM inventory_web_format
            WHERE serial_number IS NOT NULL
            GROUP BY serial_number
            HAVING COUNT(*) > 1
            LIMIT 5
        """)
        duplicates = self.cursor.fetchall()
        if duplicates:
            print(f"\n⚠️  Found duplicate serials:")
            for serial, count in duplicates:
                print(f"  {serial}: {count} occurrences")
        else:
            print(f"\n✓ No duplicate serials found!")
    
    def close(self):
        """Close database connection"""
        self.cursor.close()
        self.conn.close()

def main():
    print("=== Consolidated Inventory Import ===")
    
    importer = ConsolidatedInventoryImporter()
    
    try:
        # Ensure tables exist
        importer.ensure_table_structure()
        
        # Import JSON data
        importer.import_consolidated_json()
        
        # Import CSV data
        importer.import_web_format_csv()
        
        # Verify import
        importer.verify_import()
        
        print("\n✓ Import completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Import failed: {str(e)}")
        importer.conn.rollback()
    finally:
        importer.close()

if __name__ == "__main__":
    main()