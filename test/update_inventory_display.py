#!/usr/bin/env python3
"""
Update the inventory display to include collected inventory data
"""

import psycopg2
import json
from datetime import date

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

def get_latest_collected_inventory():
    """Get the latest collected inventory from database"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get latest collection
        cursor.execute("""
            SELECT id, collection_date, total_devices, successful_devices
            FROM inventory_collections
            WHERE successful_devices > 0
            ORDER BY collection_date DESC
            LIMIT 1
        """)
        
        latest = cursor.fetchone()
        if not latest:
            return None
            
        collection_id, collection_date, total_devices, successful_devices = latest
        
        print(f"Latest collection: ID {collection_id} from {collection_date}")
        print(f"  Devices: {successful_devices}/{total_devices}")
        
        # Get collected inventory
        inventory = {
            'collection_id': collection_id,
            'collection_date': collection_date,
            'devices': {}
        }
        
        # Get chassis
        cursor.execute("""
            SELECT hostname, name, description, pid, serial_number
            FROM collected_chassis
            WHERE collection_id = %s
        """, (collection_id,))
        
        for hostname, name, description, pid, serial_number in cursor.fetchall():
            if hostname not in inventory['devices']:
                inventory['devices'][hostname] = {
                    'chassis': [],
                    'modules': [],
                    'sfps': [],
                    'fex': []
                }
            
            inventory['devices'][hostname]['chassis'].append({
                'name': name,
                'description': description,
                'pid': pid,
                'serial_number': serial_number
            })
        
        # Get modules
        cursor.execute("""
            SELECT hostname, module_number, module_type, model, serial_number
            FROM collected_modules
            WHERE collection_id = %s
        """, (collection_id,))
        
        for hostname, module_number, module_type, model, serial_number in cursor.fetchall():
            if hostname not in inventory['devices']:
                inventory['devices'][hostname] = {
                    'chassis': [],
                    'modules': [],
                    'sfps': [],
                    'fex': []
                }
            
            inventory['devices'][hostname]['modules'].append({
                'module_number': module_number,
                'module_type': module_type,
                'model': model,
                'serial_number': serial_number
            })
        
        # Get SFPs
        cursor.execute("""
            SELECT hostname, interface, sfp_type, vendor, part_number, serial_number
            FROM collected_sfps
            WHERE collection_id = %s
        """, (collection_id,))
        
        for hostname, interface, sfp_type, vendor, part_number, serial_number in cursor.fetchall():
            if hostname not in inventory['devices']:
                inventory['devices'][hostname] = {
                    'chassis': [],
                    'modules': [],
                    'sfps': [],
                    'fex': []
                }
            
            inventory['devices'][hostname]['sfps'].append({
                'interface': interface,
                'type': sfp_type,
                'vendor': vendor,
                'part_number': part_number,
                'serial_number': serial_number
            })
        
        # Get FEX modules
        cursor.execute("""
            SELECT parent_hostname, fex_number, description, model, serial_number, state
            FROM collected_fex_modules
            WHERE collection_id = %s
        """, (collection_id,))
        
        for parent_hostname, fex_number, description, model, serial_number, state in cursor.fetchall():
            if parent_hostname not in inventory['devices']:
                inventory['devices'][parent_hostname] = {
                    'chassis': [],
                    'modules': [],
                    'sfps': [],
                    'fex': []
                }
            
            inventory['devices'][parent_hostname]['fex'].append({
                'fex_number': fex_number,
                'description': description,
                'model': model,
                'serial_number': serial_number,
                'state': state
            })
        
        # Summary
        print("\nCollected inventory summary:")
        for hostname, components in inventory['devices'].items():
            chassis_count = len(components['chassis'])
            module_count = len(components['modules'])
            sfp_count = len(components['sfps'])
            fex_count = len(components['fex'])
            
            if any([chassis_count, module_count, sfp_count, fex_count]):
                print(f"  {hostname}:")
                if chassis_count: print(f"    Chassis: {chassis_count}")
                if module_count: print(f"    Modules: {module_count}")
                if sfp_count: print(f"    SFPs: {sfp_count}")
                if fex_count: print(f"    FEX: {fex_count}")
        
        return inventory
        
    finally:
        cursor.close()
        conn.close()

def update_inventory_json():
    """Update the comprehensive_network_inventory.json with collected data"""
    
    # Get latest collected inventory
    collected = get_latest_collected_inventory()
    if not collected:
        print("No collected inventory found")
        return
    
    # Load existing inventory
    inventory_file = '/var/www/html/meraki-data/comprehensive_network_inventory.json'
    try:
        with open(inventory_file, 'r') as f:
            existing = json.load(f)
    except:
        existing = {}
    
    # Update with collected data
    updated_count = 0
    for hostname, components in collected['devices'].items():
        # Find matching device by hostname
        for ip, device_data in existing.items():
            if device_data.get('ssh_data', {}).get('basic_info', {}).get('hostname') == hostname:
                # Update components
                if components['chassis']:
                    device_data['ssh_data']['chassis_blades'] = components['chassis']
                if components['modules']:
                    device_data['ssh_data']['hardware_inventory'] = components['modules']
                if components['sfps']:
                    device_data['ssh_data']['sfp_modules'] = components['sfps']
                if components['fex']:
                    device_data['ssh_data']['fex_modules'] = components['fex']
                
                updated_count += 1
                break
    
    # Save updated inventory
    output_file = '/var/www/html/meraki-data/comprehensive_network_inventory_updated.json'
    with open(output_file, 'w') as f:
        json.dump(existing, f, indent=2)
    
    print(f"\nUpdated {updated_count} devices with collected inventory")
    print(f"Saved to: {output_file}")
    
    # Also create a simpler format for the web interface
    simple_inventory = {}
    for hostname, components in collected['devices'].items():
        if any([components['chassis'], components['modules'], components['sfps'], components['fex']]):
            simple_inventory[hostname] = components
    
    simple_file = '/var/www/html/meraki-data/collected_inventory_simple.json'
    with open(simple_file, 'w') as f:
        json.dump({
            'collection_date': collected['collection_date'].isoformat() if hasattr(collected['collection_date'], 'isoformat') else str(collected['collection_date']),
            'devices': simple_inventory
        }, f, indent=2)
    
    print(f"Saved simple format to: {simple_file}")

if __name__ == "__main__":
    print("Updating inventory display with collected data...")
    update_inventory_json()