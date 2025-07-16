#!/usr/bin/env python3
"""
Clean and re-import inventory data to match CSV structure
Keeps existing database schema but reduces data to essential fields
"""
import psycopg2
import json
from datetime import datetime
import sys

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsruser'
}

def export_current_data():
    """Export current inventory data from database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    print("Exporting current inventory data...")
    
    # Export from comprehensive_device_inventory
    cursor.execute("""
        SELECT 
            hostname, 
            ip_address, 
            collection_timestamp,
            physical_components,
            summary
        FROM comprehensive_device_inventory
        ORDER BY hostname
    """)
    
    exported_data = []
    for row in cursor.fetchall():
        hostname, ip, timestamp, components, summary = row
        exported_data.append({
            'hostname': hostname,
            'ip_address': str(ip),
            'collection_timestamp': timestamp.isoformat() if timestamp else None,
            'physical_components': components,
            'summary': summary
        })
    
    # Save backup
    backup_file = f'/tmp/inventory_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(backup_file, 'w') as f:
        json.dump(exported_data, f, indent=2)
    
    print(f"Backed up {len(exported_data)} devices to {backup_file}")
    
    cursor.close()
    conn.close()
    
    return exported_data

def transform_to_csv_format(device_data):
    """Transform device data to match CSV format structure"""
    transformed = []
    
    for device in device_data:
        hostname = device['hostname']
        ip = device['ip_address']
        components = device.get('physical_components', {})
        
        # Process chassis
        chassis_list = components.get('chassis', [])
        if chassis_list:
            # Determine position based on number of chassis
            if len(chassis_list) > 1:
                # Check if it's a stack or N5K with FEX
                first_model = chassis_list[0].get('model_name', '')
                if 'N5K' in first_model or 'N56' in first_model:
                    # N5K with FEX
                    # Main chassis
                    transformed.append({
                        'hostname': hostname,
                        'ip_address': ip,
                        'position': 'Parent Switch',
                        'model': first_model.strip(),
                        'serial_number': chassis_list[0].get('serial_number', '').strip(),
                        'port_location': '',
                        'vendor': 'Cisco',
                        'notes': ''
                    })
                    
                    # FEX units
                    for i, chassis in enumerate(chassis_list[1:], 1):
                        fex_num = f"{100 + i}"
                        if 'Fex-' in chassis.get('name', ''):
                            import re
                            match = re.search(r'Fex-(\d+)', chassis['name'])
                            if match:
                                fex_num = match.group(1)
                        
                        transformed.append({
                            'hostname': '',
                            'ip_address': '',
                            'position': f'FEX-{fex_num}',
                            'model': chassis.get('model_name', '').strip(),
                            'serial_number': chassis.get('serial_number', '').strip(),
                            'port_location': chassis.get('name', ''),
                            'vendor': 'Cisco',
                            'notes': ''
                        })
                else:
                    # Regular stack
                    # Master
                    transformed.append({
                        'hostname': hostname,
                        'ip_address': ip,
                        'position': 'Master',
                        'model': chassis_list[0].get('model_name', '').strip(),
                        'serial_number': chassis_list[0].get('serial_number', '').strip(),
                        'port_location': '',
                        'vendor': '',
                        'notes': ''
                    })
                    
                    # Slaves
                    for chassis in chassis_list[1:]:
                        transformed.append({
                            'hostname': '',
                            'ip_address': '',
                            'position': 'Slave',
                            'model': chassis.get('model_name', '').strip(),
                            'serial_number': chassis.get('serial_number', '').strip(),
                            'port_location': '',
                            'vendor': '',
                            'notes': ''
                        })
            else:
                # Single device
                transformed.append({
                    'hostname': hostname,
                    'ip_address': ip,
                    'position': 'Standalone',
                    'model': chassis_list[0].get('model_name', '').strip(),
                    'serial_number': chassis_list[0].get('serial_number', '').strip(),
                    'port_location': '',
                    'vendor': '',
                    'notes': ''
                })
        
        # Process modules (limit to significant ones)
        modules = components.get('modules', [])
        module_count = 0
        for module in modules:
            model = module.get('model_name', '').strip()
            serial = module.get('serial_number', '').strip()
            
            # Skip empty or invalid modules
            if not model or model == '""' or not serial or serial == '""':
                continue
                
            # Only include modules with real model numbers
            if module_count < 20:  # Limit per device
                transformed.append({
                    'hostname': '',
                    'ip_address': '',
                    'position': 'Module',
                    'model': model,
                    'serial_number': serial,
                    'port_location': module.get('name', ''),
                    'vendor': '',
                    'notes': ''
                })
                module_count += 1
        
        # Process transceivers/SFPs (sample only)
        transceivers = components.get('transceivers', [])
        sfp_count = 0
        for sfp in transceivers:
            model = sfp.get('model_name', '').strip()
            serial = sfp.get('serial_number', '').strip()
            
            # Skip empty SFPs
            if not serial or serial == '""':
                continue
                
            if sfp_count < 10:  # Limit per device
                # Determine vendor from serial prefix
                vendor = ''
                if serial.startswith('AGM') or serial.startswith('AGS'):
                    vendor = 'Avago'
                elif serial.startswith('FNS'):
                    vendor = 'Finisar'
                elif serial.startswith('MTC'):
                    vendor = 'MikroTik'
                
                transformed.append({
                    'hostname': '',
                    'ip_address': '',
                    'position': 'SFP',
                    'model': model if model and model != '""' else 'Unknown',
                    'serial_number': serial,
                    'port_location': sfp.get('name', ''),
                    'vendor': vendor,
                    'notes': ''
                })
                sfp_count += 1
    
    return transformed

def clear_and_reload_database(transformed_data):
    """Clear existing data and reload with transformed data"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Create the table if it doesn't exist
        print("Creating/verifying inventory_web_format table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_web_format (
                id SERIAL PRIMARY KEY,
                hostname VARCHAR(255),
                ip_address VARCHAR(45),
                position VARCHAR(50),
                model VARCHAR(255),
                serial_number VARCHAR(255),
                port_location VARCHAR(255),
                vendor VARCHAR(100),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on serial_number if not exists
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_inventory_web_serial 
            ON inventory_web_format(serial_number)
        """)
        
        # Clear existing data
        print("Clearing existing inventory_web_format data...")
        cursor.execute("TRUNCATE TABLE inventory_web_format RESTART IDENTITY")
        
        # Insert transformed data
        print(f"Inserting {len(transformed_data)} rows...")
        insert_count = 0
        for row in transformed_data:
            cursor.execute("""
                INSERT INTO inventory_web_format 
                (hostname, ip_address, position, model, serial_number, 
                 port_location, vendor, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['hostname'],
                row['ip_address'],
                row['position'],
                row['model'],
                row['serial_number'],
                row['port_location'],
                row['vendor'],
                row['notes']
            ))
            insert_count += 1
            
            if insert_count % 100 == 0:
                print(f"  Inserted {insert_count} rows...")
        
        conn.commit()
        print(f"Successfully inserted {insert_count} rows")
        
        # Show summary
        cursor.execute("""
            SELECT position, COUNT(*) 
            FROM inventory_web_format 
            GROUP BY position 
            ORDER BY position
        """)
        
        print("\nSummary by position:")
        for position, count in cursor.fetchall():
            print(f"  {position}: {count}")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def add_eol_data():
    """Add EOL data to inventory_web_format table"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Add EOL columns if they don't exist
        print("\nAdding EOL columns if needed...")
        cursor.execute("""
            ALTER TABLE inventory_web_format 
            ADD COLUMN IF NOT EXISTS announcement_date DATE,
            ADD COLUMN IF NOT EXISTS end_of_sale DATE,
            ADD COLUMN IF NOT EXISTS end_of_support DATE
        """)
        
        # Update EOL data from datacenter_inventory table
        print("Updating EOL data from datacenter_inventory...")
        cursor.execute("""
            UPDATE inventory_web_format iwf
            SET 
                announcement_date = di.announcement_date,
                end_of_sale = di.end_of_sale_date,
                end_of_support = di.end_of_support_date
            FROM datacenter_inventory di
            WHERE iwf.serial_number = di.serial_number
            AND di.end_of_support_date IS NOT NULL
        """)
        
        updated_count = cursor.rowcount
        print(f"Updated {updated_count} rows with EOL data")
        
        # Show EOL summary
        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE end_of_support IS NOT NULL) as has_eol,
                COUNT(*) FILTER (WHERE end_of_support <= CURRENT_DATE) as past_eol,
                COUNT(*) FILTER (WHERE end_of_support > CURRENT_DATE AND end_of_support <= CURRENT_DATE + INTERVAL '1 year') as eol_soon
            FROM inventory_web_format
        """)
        
        has_eol, past_eol, eol_soon = cursor.fetchone()
        print(f"\nEOL Summary:")
        print(f"  Has EOL data: {has_eol}")
        print(f"  Past EOL: {past_eol}")
        print(f"  EOL within 1 year: {eol_soon}")
        
        conn.commit()
        
    except Exception as e:
        print(f"Error adding EOL data: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    print("=== Inventory Data Cleanup and Re-import ===")
    print(f"Started at: {datetime.now()}")
    
    # Step 1: Export current data
    current_data = export_current_data()
    
    # Step 2: Transform to CSV format
    print(f"\nTransforming {len(current_data)} devices to CSV format...")
    transformed_data = transform_to_csv_format(current_data)
    print(f"Transformed to {len(transformed_data)} rows")
    
    # Step 3: Clear and reload database
    clear_and_reload_database(transformed_data)
    
    # Step 4: Add EOL data
    add_eol_data()
    
    print(f"\nCompleted at: {datetime.now()}")

if __name__ == "__main__":
    main()