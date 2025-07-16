#!/usr/bin/env python3
"""
Generate inventory data in the format needed for web display
Matches the CSV format: hostname, ip, position, model, serial, port_location, vendor
"""
import json
import re
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_db_connection

def generate_web_format_data():
    """Generate inventory data formatted for web display"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all devices with inventory data
        cursor.execute("""
            SELECT device_name, ip_address, physical_inventory
            FROM comprehensive_device_inventory
            WHERE physical_inventory IS NOT NULL
            ORDER BY device_name
        """)
        
        all_devices = cursor.fetchall()
        web_data = []
        
        for device_name, ip_address, physical_inv in all_devices:
            device_entries = []
            chassis_list = physical_inv.get('chassis', [])
            
            # Handle chassis entries
            if len(chassis_list) > 1:
                # Check if this is N5K with FEX or regular stack
                main_chassis = chassis_list[0]
                if 'N5K' in main_chassis.get('model', '') or 'N56' in main_chassis.get('model', ''):
                    # Parent switch with FEX
                    device_entries.append({
                        'hostname': device_name,
                        'ip_address': str(ip_address),
                        'position': 'Parent Switch',
                        'model': main_chassis.get('model', ''),
                        'serial_number': main_chassis.get('serial', ''),
                        'port_location': '',
                        'vendor': 'Cisco'
                    })
                    
                    # FEX units
                    for i in range(1, len(chassis_list)):
                        fex = chassis_list[i]
                        fex_id_match = re.search(r'Fex-(\d+)', fex.get('name', ''))
                        fex_num = fex_id_match.group(1) if fex_id_match else str(100 + i)
                        
                        device_entries.append({
                            'hostname': '',
                            'ip_address': '',
                            'position': f'FEX-{fex_num}',
                            'model': fex.get('model', ''),
                            'serial_number': fex.get('serial', ''),
                            'port_location': fex.get('name', ''),
                            'vendor': 'Cisco'
                        })
                else:
                    # Regular stack (3750, etc)
                    device_entries.append({
                        'hostname': device_name,
                        'ip_address': str(ip_address),
                        'position': 'Master',
                        'model': chassis_list[0].get('model', ''),
                        'serial_number': chassis_list[0].get('serial', ''),
                        'port_location': '',
                        'vendor': ''
                    })
                    
                    # Slave units
                    for i in range(1, len(chassis_list)):
                        device_entries.append({
                            'hostname': '',
                            'ip_address': '',
                            'position': 'Slave',
                            'model': chassis_list[i].get('model', ''),
                            'serial_number': chassis_list[i].get('serial', ''),
                            'port_location': '',
                            'vendor': ''
                        })
            else:
                # Single device
                if chassis_list:
                    device_entries.append({
                        'hostname': device_name,
                        'ip_address': str(ip_address),
                        'position': 'Standalone',
                        'model': chassis_list[0].get('model', ''),
                        'serial_number': chassis_list[0].get('serial', ''),
                        'port_location': '',
                        'vendor': ''
                    })
            
            # Add modules
            for module in physical_inv.get('modules', []):
                device_entries.append({
                    'hostname': '',
                    'ip_address': '',
                    'position': 'Module',
                    'model': module.get('model', ''),
                    'serial_number': module.get('serial', ''),
                    'port_location': module.get('name', ''),
                    'vendor': ''
                })
            
            # Add SFPs/Transceivers
            for sfp in physical_inv.get('transceivers', []):
                device_entries.append({
                    'hostname': '',
                    'ip_address': '',
                    'position': 'SFP',
                    'model': sfp.get('model', 'Unknown'),
                    'serial_number': sfp.get('serial', ''),
                    'port_location': sfp.get('name', ''),
                    'vendor': sfp.get('vendor', '')
                })
            
            web_data.extend(device_entries)
        
        # Store in a format-specific table or return as JSON
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Clear existing data
        cursor.execute("TRUNCATE TABLE inventory_web_format")
        
        # Insert new data
        for entry in web_data:
            cursor.execute("""
                INSERT INTO inventory_web_format 
                (hostname, ip_address, position, model, serial_number, port_location, vendor)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                entry['hostname'],
                entry['ip_address'],
                entry['position'],
                entry['model'],
                entry['serial_number'],
                entry['port_location'],
                entry['vendor']
            ))
        
        conn.commit()
        
        print(f"Generated {len(web_data)} inventory entries for web display")
        print(f"Data stored in inventory_web_format table")
        
        # Show sample data
        cursor.execute("""
            SELECT * FROM inventory_web_format 
            WHERE hostname != '' 
            LIMIT 5
        """)
        
        print("\nSample entries:")
        for row in cursor.fetchall():
            print(f"  {row[1]} - {row[3]} - {row[4]} ({row[5]})")
            
    except Exception as e:
        print(f"Error generating web format: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    generate_web_format_data()