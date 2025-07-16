#!/usr/bin/env python3
"""
Get inventory data in EXACT CSV format with hierarchical structure
"""
import psycopg2
from datetime import date
from collections import OrderedDict

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsruser'
}

def get_inventory_csv_format_db():
    """
    Get inventory data in exact CSV format with hierarchical structure
    Returns data exactly as it appears in inventory_ultimate_final.csv
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get all inventory data ordered properly
        cursor.execute("""
            SELECT 
                hostname, ip_address, position, model, serial_number,
                port_location, vendor, notes,
                announcement_date, end_of_sale, end_of_support,
                parent_hostname, relationship, site
            FROM inventory_web_format
            ORDER BY 
                site,
                COALESCE(parent_hostname, hostname),
                CASE 
                    WHEN position IN ('Master', 'Standalone', 'Parent Switch') THEN 1
                    WHEN position = 'Slave' THEN 2
                    WHEN position LIKE 'FEX-%' THEN 3
                    WHEN position = 'Module' THEN 4
                    WHEN position = 'SFP' THEN 5
                    ELSE 6
                END,
                serial_number
        """)
        
        # Build hierarchical inventory matching CSV format exactly
        inventory = []
        current_device = None
        
        for row in cursor.fetchall():
            hostname, ip, position, model, serial, port_location, vendor, notes, announce, eos, eol, parent_hostname, relationship, site = row
            
            # Create row data matching CSV columns exactly
            row_data = {
                'site': site or 'Unknown',
                'hostname': hostname or '',
                'ip_address': ip or '',
                'position': position,
                'model': model,
                'serial_number': serial,
                'port_location': port_location or '',
                'vendor': vendor or '',
                'notes': notes or '',
                # Add EOL data for display
                'announcement_date': announce,
                'end_of_sale': eos,
                'end_of_support': eol,
                # Add new fields
                'parent_hostname': parent_hostname or hostname or '',
                'relationship': relationship or position
            }
            
            # Track current device for component grouping
            if hostname and position in ['Master', 'Standalone', 'Parent Switch']:
                current_device = hostname
                row_data['is_device'] = True
            else:
                row_data['is_device'] = False
                row_data['parent_device'] = current_device
            
            inventory.append(row_data)
        
        # Calculate summary statistics
        device_count = len([d for d in inventory if d.get('is_device')])
        component_count = len(inventory) - device_count
        
        # EOL summary
        today = date.today()
        eol_count = 0
        eos_count = 0
        
        for item in inventory:
            if item['end_of_support'] and item['end_of_support'] <= today:
                eol_count += 1
            if item['end_of_sale'] and item['end_of_sale'] <= today:
                eos_count += 1
        
        summary = {
            'total_rows': len(inventory),
            'total_devices': device_count,
            'total_components': component_count,
            'past_eol': eol_count,
            'past_eos': eos_count,
            'positions': {
                'Standalone': len([i for i in inventory if i['position'] == 'Standalone']),
                'Master': len([i for i in inventory if i['position'] == 'Master']),
                'Slave': len([i for i in inventory if i['position'] == 'Slave']),
                'Parent Switch': len([i for i in inventory if i['position'] == 'Parent Switch']),
                'FEX': len([i for i in inventory if i['position'].startswith('FEX-')]),
                'Module': len([i for i in inventory if i['position'] == 'Module']),
                'SFP': len([i for i in inventory if i['position'] == 'SFP'])
            }
        }
        
        return {
            'inventory': inventory,
            'summary': summary,
            'data_source': 'inventory_web_format_csv'
        }
        
    except Exception as e:
        print(f"Error getting CSV format inventory: {e}")
        return {
            'inventory': [],
            'summary': {},
            'data_source': 'error',
            'error': str(e)
        }
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Test the function
    print("Testing CSV format inventory...")
    result = get_inventory_csv_format_db()
    print(f"Found {len(result['inventory'])} rows")
    print(f"Summary: {result['summary']}")
    
    if result['inventory']:
        print("\nFirst 10 rows (CSV format):")
        print("hostname,ip_address,position,model,serial_number,port_location,vendor,notes")
        for item in result['inventory'][:10]:
            print(f"{item['hostname']},{item['ip_address']},{item['position']},{item['model']},{item['serial_number']},{item['port_location']},{item['vendor']},{item['notes']}")