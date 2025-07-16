#!/usr/bin/env python3
"""
Add function to get collected inventory from database
"""

# Function to add to corp_network_data_db.py

def get_collected_inventory_db():
    """Get the latest collected inventory from database"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get latest successful collection
        cursor.execute("""
            SELECT id, collection_date, total_devices, successful_devices
            FROM inventory_collections
            WHERE successful_devices > 0
            ORDER BY collection_date DESC
            LIMIT 1
        """)
        
        latest = cursor.fetchone()
        if not latest:
            return {'collection_date': None, 'devices': {}}
        
        collection_id, collection_date, total_devices, successful_devices = latest
        
        devices = {}
        
        # Get all devices with collected components
        cursor.execute("""
            WITH device_components AS (
                SELECT DISTINCT hostname FROM (
                    SELECT hostname FROM collected_chassis WHERE collection_id = %s
                    UNION
                    SELECT hostname FROM collected_modules WHERE collection_id = %s
                    UNION 
                    SELECT hostname FROM collected_sfps WHERE collection_id = %s
                    UNION
                    SELECT parent_hostname as hostname FROM collected_fex_modules WHERE collection_id = %s
                ) AS all_hosts
            )
            SELECT dc.hostname
            FROM device_components dc
            ORDER BY dc.hostname
        """, (collection_id, collection_id, collection_id, collection_id))
        
        for (hostname,) in cursor.fetchall():
            devices[hostname] = {
                'chassis': [],
                'modules': [],
                'sfps': [],
                'fex': []
            }
        
        # Get chassis
        cursor.execute("""
            SELECT hostname, name, description, pid, serial_number
            FROM collected_chassis
            WHERE collection_id = %s
            ORDER BY hostname, name
        """, (collection_id,))
        
        for hostname, name, description, pid, serial_number in cursor.fetchall():
            if hostname in devices:
                devices[hostname]['chassis'].append({
                    'name': name or '',
                    'description': description or '',
                    'pid': pid or '',
                    'serial_number': serial_number or ''
                })
        
        # Get modules
        cursor.execute("""
            SELECT hostname, module_number, module_type, model, serial_number
            FROM collected_modules
            WHERE collection_id = %s
            ORDER BY hostname, module_number
        """, (collection_id,))
        
        for hostname, module_number, module_type, model, serial_number in cursor.fetchall():
            if hostname in devices:
                devices[hostname]['modules'].append({
                    'module_number': module_number or '',
                    'module_type': module_type or '',
                    'model': model or '',
                    'serial_number': serial_number or ''
                })
        
        # Get SFPs
        cursor.execute("""
            SELECT hostname, interface, sfp_type, vendor, part_number, serial_number
            FROM collected_sfps
            WHERE collection_id = %s
            ORDER BY hostname, interface
        """, (collection_id,))
        
        for hostname, interface, sfp_type, vendor, part_number, serial_number in cursor.fetchall():
            if hostname in devices:
                devices[hostname]['sfps'].append({
                    'interface': interface or '',
                    'type': sfp_type or '',
                    'vendor': vendor or '',
                    'part_number': part_number or '',
                    'serial_number': serial_number or ''
                })
        
        # Get FEX modules
        cursor.execute("""
            SELECT parent_hostname, fex_number, description, model, serial_number, state
            FROM collected_fex_modules
            WHERE collection_id = %s
            ORDER BY parent_hostname, fex_number
        """, (collection_id,))
        
        for parent_hostname, fex_number, description, model, serial_number, state in cursor.fetchall():
            if parent_hostname in devices:
                devices[parent_hostname]['fex'].append({
                    'fex_number': fex_number or '',
                    'description': description or '',
                    'model': model or '',
                    'serial_number': serial_number or '',
                    'state': state or ''
                })
        
        return {
            'collection_id': collection_id,
            'collection_date': collection_date,
            'total_devices': total_devices,
            'successful_devices': successful_devices,
            'devices': devices
        }
        
    except Exception as e:
        print(f"❌ Error getting collected inventory: {e}")
        return {'collection_date': None, 'devices': {}}
    finally:
        if conn:
            conn.close()

# Usage example
if __name__ == "__main__":
    import psycopg2
    from datetime import date
    
    DB_CONFIG = {
        'host': 'localhost',
        'database': 'dsrcircuits',
        'user': 'dsruser',
        'password': 'dsrpass123'
    }
    
    # Test the function
    inventory = get_collected_inventory_db()
    
    print(f"Collection Date: {inventory.get('collection_date')}")
    print(f"Total Devices: {inventory.get('total_devices')}")
    print(f"Successful: {inventory.get('successful_devices')}")
    print(f"Devices with components: {len(inventory['devices'])}")
    
    for hostname, components in inventory['devices'].items():
        print(f"\n{hostname}:")
        print(f"  Chassis: {len(components['chassis'])}")
        print(f"  Modules: {len(components['modules'])}")
        print(f"  SFPs: {len(components['sfps'])}")
        print(f"  FEX: {len(components['fex'])}")