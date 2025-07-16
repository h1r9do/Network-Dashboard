#!/usr/bin/env python3
"""
Function to retrieve inventory data from inventory_web_format table
For use in Tab 4 of the inventory page
"""
import psycopg2
from datetime import date
from collections import defaultdict

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsruser'
}

def get_inventory_web_format_db():
    """
    Get inventory data from inventory_web_format table
    Returns hierarchical structure suitable for Tab 4 display
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get all inventory data with EOL information
        cursor.execute("""
            SELECT 
                hostname, ip_address, position, model, serial_number,
                port_location, vendor, notes,
                announcement_date, end_of_sale, end_of_support
            FROM inventory_web_format
            ORDER BY 
                CASE 
                    WHEN hostname != '' THEN hostname
                    ELSE (
                        SELECT i2.hostname 
                        FROM inventory_web_format i2 
                        WHERE i2.hostname != '' 
                        AND i2.ip_address = inventory_web_format.ip_address
                        ORDER BY i2.id 
                        LIMIT 1
                    )
                END,
                CASE 
                    WHEN position IN ('Master', 'Standalone', 'Parent Switch') THEN 1
                    WHEN position = 'Slave' THEN 2
                    WHEN position LIKE 'FEX-%' THEN 3
                    WHEN position = 'Module' THEN 4
                    WHEN position = 'SFP' THEN 5
                END,
                serial_number
        """)
        
        # Process results into hierarchical structure
        inventory = []
        device_components = defaultdict(list)
        device_map = {}
        
        for row in cursor.fetchall():
            hostname, ip, position, model, serial, port_location, vendor, notes, announce, eos, eol = row
            
            # Determine site from hostname or IP
            site = ''
            if hostname:
                if hostname.startswith(('ALA-', 'AL-', 'ala')):
                    site = 'AZ-Alameda-DC'
                elif hostname.startswith(('MDF-', 'N5K-', 'N7K-', '2960')):
                    site = 'AZ-Scottsdale-HQ-Corp'
                elif 'dtc_phx' in hostname:
                    site = 'AZ-Scottsdale-HQ-Corp'
            if not site and ip:
                if ip.startswith('10.0.'):
                    site = 'AZ-Scottsdale-HQ-Corp'
                elif ip.startswith('10.101.'):
                    site = 'AZ-Alameda-DC'
                elif ip.startswith('10.44.'):
                    site = 'Equinix-Seattle'
                elif ip.startswith('10.41.'):
                    site = 'AZ-Desert-Ridge'
                elif ip.startswith('10.42.'):
                    site = 'TX-Dallas-DC'
                elif ip.startswith('10.43.'):
                    site = 'GA-Atlanta-DC'
            
            # Determine device type
            device_type = ''
            if position in ['Master', 'Slave']:
                device_type = 'Stack'
            elif position == 'Standalone':
                device_type = 'Switch'
            elif position == 'Parent Switch':
                device_type = 'Nexus Switch'
            elif position.startswith('FEX-'):
                device_type = 'FEX Module'
            elif position == 'Module':
                device_type = 'Module'
            elif position == 'SFP':
                device_type = 'Transceiver'
            
            device_data = {
                'site': site,
                'hostname': hostname,
                'vendor': vendor or 'Cisco',
                'device_type': device_type,
                'model': model,
                'serial_number': serial,
                'mgmt_ip': ip,
                'port_location': port_location,
                'position': position,
                'notes': notes,
                'end_of_sale': eos,
                'end_of_support': eol,
                'announcement_date': announce
            }
            
            # If it's a main device (has hostname), add to inventory
            if hostname and position in ['Master', 'Standalone', 'Parent Switch']:
                inventory.append(device_data)
                device_map[hostname] = device_data
            else:
                # It's a component - find parent device
                # For now, add all components to inventory for flat display
                inventory.append(device_data)
        
        # Calculate summary statistics
        summary = {
            'total_devices': len([d for d in inventory if d['position'] in ['Master', 'Standalone', 'Parent Switch']]),
            'total_components': len(inventory),
            'sites': len(set(d['site'] for d in inventory if d['site'])),
            'vendors': len(set(d['vendor'] for d in inventory if d['vendor'])),
        }
        
        # EOL summary
        today = date.today()
        eol_count = 0
        eos_count = 0
        
        for device in inventory:
            if device['end_of_support']:
                if device['end_of_support'] <= today:
                    eol_count += 1
            if device['end_of_sale']:
                if device['end_of_sale'] <= today:
                    eos_count += 1
        
        summary['past_eol'] = eol_count
        summary['past_eos'] = eos_count
        
        return {
            'inventory': inventory,
            'summary': summary,
            'data_source': 'inventory_web_format'
        }
        
    except Exception as e:
        print(f"Error getting inventory web format: {e}")
        return {
            'inventory': [],
            'summary': {},
            'data_source': 'error',
            'error': str(e)
        }
    finally:
        cursor.close()
        conn.close()

def get_hierarchical_inventory_web_format_db():
    """
    Get inventory data in hierarchical format (devices with nested components)
    Alternative format for different display options
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get all main devices first
        cursor.execute("""
            SELECT 
                hostname, ip_address, position, model, serial_number,
                port_location, vendor, notes,
                announcement_date, end_of_sale, end_of_support
            FROM inventory_web_format
            WHERE hostname != '' 
            AND position IN ('Master', 'Standalone', 'Parent Switch')
            ORDER BY hostname
        """)
        
        devices = []
        device_map = {}
        
        for row in cursor.fetchall():
            hostname, ip, position, model, serial, port_location, vendor, notes, announce, eos, eol = row
            
            device = {
                'hostname': hostname,
                'ip_address': ip,
                'position': position,
                'model': model,
                'serial_number': serial,
                'vendor': vendor or 'Cisco',
                'notes': notes,
                'end_of_sale': eos,
                'end_of_support': eol,
                'components': []
            }
            
            devices.append(device)
            device_map[hostname] = device
        
        # Get all components
        cursor.execute("""
            SELECT 
                hostname, ip_address, position, model, serial_number,
                port_location, vendor, notes,
                announcement_date, end_of_sale, end_of_support
            FROM inventory_web_format
            WHERE hostname = '' 
            OR position NOT IN ('Master', 'Standalone', 'Parent Switch')
            ORDER BY 
                CASE 
                    WHEN position = 'Slave' THEN 1
                    WHEN position LIKE 'FEX-%' THEN 2
                    WHEN position = 'Module' THEN 3
                    WHEN position = 'SFP' THEN 4
                END,
                serial_number
        """)
        
        # Group components by some logic (this is simplified)
        orphan_components = []
        
        for row in cursor.fetchall():
            hostname, ip, position, model, serial, port_location, vendor, notes, announce, eos, eol = row
            
            component = {
                'position': position,
                'model': model,
                'serial_number': serial,
                'port_location': port_location,
                'vendor': vendor,
                'end_of_sale': eos,
                'end_of_support': eol
            }
            
            # Try to find parent device (simplified logic)
            # In real implementation, you'd need better parent-child mapping
            added = False
            for device in devices:
                # Add component to first device (simplified)
                if len(device['components']) < 10:  # Limit components per device
                    device['components'].append(component)
                    added = True
                    break
            
            if not added:
                orphan_components.append(component)
        
        return {
            'devices': devices,
            'orphan_components': orphan_components,
            'summary': {
                'total_devices': len(devices),
                'total_components': sum(len(d['components']) for d in devices) + len(orphan_components)
            },
            'data_source': 'inventory_web_format_hierarchical'
        }
        
    except Exception as e:
        print(f"Error getting hierarchical inventory: {e}")
        return {
            'devices': [],
            'orphan_components': [],
            'summary': {},
            'data_source': 'error',
            'error': str(e)
        }
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Test the functions
    print("Testing get_inventory_web_format_db()...")
    result = get_inventory_web_format_db()
    print(f"Found {len(result['inventory'])} items")
    print(f"Summary: {result['summary']}")
    
    if result['inventory']:
        print("\nFirst 5 items:")
        for item in result['inventory'][:5]:
            print(f"  {item['hostname'] or item['position']}: {item['model']} ({item['serial_number']})")