#\!/usr/bin/env python3
"""
Standalone function to get collected inventory from database
This will be integrated into corp_network_data_db.py
"""

import psycopg2
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dsrcircuits',
    'user': 'dsruser',
    'password': 'dsrpass123'
}

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def get_collected_inventory_db():
    """Get collected inventory data from SSH collections stored in database"""
    conn = get_db_connection()
    if not conn:
        return {'inventory': [], 'summary': {}}
    
    try:
        cursor = conn.cursor()
        
        # Get latest collection ID
        cursor.execute("""
            SELECT MAX(id) 
            FROM inventory_collections 
            WHERE successful_devices > 0
        """)
        result = cursor.fetchone()
        
        if not result or not result[0]:
            return {'inventory': [], 'summary': {'message': 'No completed collections found'}}
        
        latest_collection_id = result[0]
        
        # Get collection summary
        cursor.execute("""
            SELECT collection_date, collection_date, total_devices, successful_devices
            FROM inventory_collections
            WHERE id = %s
        """, (latest_collection_id,))
        collection_info = cursor.fetchone()
        
        # Get all collected components
        inventory_data = []
        
        # Get chassis components
        cursor.execute("""
            SELECT c.hostname, nd.ip_address, c.name, c.description, c.pid, c.vid, c.serial_number
            FROM collected_chassis c
            LEFT JOIN network_devices nd ON c.hostname = nd.hostname
            WHERE c.collection_id = %s
            ORDER BY c.hostname, c.name
        """, (latest_collection_id,))
        
        for row in cursor.fetchall():
            inventory_data.append({
                'hostname': row[0],
                'ip': row[1] or 'N/A',
                'component_type': 'Chassis',
                'name': row[2],
                'description': row[3],
                'pid': row[4],
                'vid': row[5],
                'serial': row[6]
            })
        
        # Get modules
        cursor.execute("""
            SELECT m.hostname, nd.ip_address, m.module_number, m.module_type, m.model, m.status, m.serial_number
            FROM collected_modules m
            LEFT JOIN network_devices nd ON m.hostname = nd.hostname
            WHERE m.collection_id = %s
            ORDER BY m.hostname, m.module_number
        """, (latest_collection_id,))
        
        for row in cursor.fetchall():
            inventory_data.append({
                'hostname': row[0],
                'ip': row[1] or 'N/A',
                'component_type': 'Module',
                'name': f"Slot {row[2]}",
                'description': row[3],
                'pid': row[4],
                'status': row[5],
                'serial': row[6]
            })
        
        # Get SFPs
        cursor.execute("""
            SELECT s.hostname, nd.ip_address, s.interface, s.type, s.name, s.serial_number, s.cisco_pid
            FROM collected_sfps s
            LEFT JOIN network_devices nd ON s.hostname = nd.hostname
            WHERE s.collection_id = %s
            ORDER BY s.hostname, s.interface
        """, (latest_collection_id,))
        
        for row in cursor.fetchall():
            inventory_data.append({
                'hostname': row[0],
                'ip': row[1] or 'N/A',
                'component_type': 'SFP',
                'name': row[2],
                'description': row[3],
                'pid': row[6] or row[4],
                'serial': row[5],
                'interface': row[2]
            })
        
        # Get FEX modules
        cursor.execute("""
            SELECT f.hostname, nd.ip_address, f.fex_number, f.fex_model, f.fex_serial, f.description, f.state
            FROM collected_fex_modules f
            LEFT JOIN network_devices nd ON f.hostname = nd.hostname
            WHERE f.collection_id = %s
            ORDER BY f.hostname, f.fex_number
        """, (latest_collection_id,))
        
        for row in cursor.fetchall():
            inventory_data.append({
                'hostname': row[0],
                'ip': row[1] or 'N/A',
                'component_type': 'FEX',
                'name': f"FEX-{row[2]}",
                'description': row[5],
                'pid': row[3],
                'serial': row[4],
                'status': row[6]
            })
        
        # Get power supplies
        cursor.execute("""
            SELECT p.hostname, nd.ip_address, p.name, p.description, p.pid, p.vid, p.serial_number
            FROM collected_power_supplies p
            LEFT JOIN network_devices nd ON p.hostname = nd.hostname
            WHERE p.collection_id = %s
            ORDER BY p.hostname, p.name
        """, (latest_collection_id,))
        
        for row in cursor.fetchall():
            inventory_data.append({
                'hostname': row[0],
                'ip': row[1] or 'N/A',
                'component_type': 'Power Supply',
                'name': row[2],
                'description': row[3],
                'pid': row[4],
                'vid': row[5],
                'serial': row[6]
            })
        
        # Get fans
        cursor.execute("""
            SELECT f.hostname, nd.ip_address, f.name, f.description, f.pid, f.vid, f.serial_number
            FROM collected_fans f
            LEFT JOIN network_devices nd ON f.hostname = nd.hostname
            WHERE f.collection_id = %s
            ORDER BY f.hostname, f.name
        """, (latest_collection_id,))
        
        for row in cursor.fetchall():
            inventory_data.append({
                'hostname': row[0],
                'ip': row[1] or 'N/A',
                'component_type': 'Fan',
                'name': row[2],
                'description': row[3],
                'pid': row[4],
                'vid': row[5],
                'serial': row[6]
            })
        
        # Create summary
        component_counts = {}
        device_counts = {}
        
        for item in inventory_data:
            # Count by component type
            comp_type = item['component_type']
            component_counts[comp_type] = component_counts.get(comp_type, 0) + 1
            
            # Count unique devices
            hostname = item['hostname']
            if hostname not in device_counts:
                device_counts[hostname] = {'total': 0, 'by_type': {}}
            device_counts[hostname]['total'] += 1
            device_counts[hostname]['by_type'][comp_type] = device_counts[hostname]['by_type'].get(comp_type, 0) + 1
        
        summary = {
            'collection_id': latest_collection_id,
            'collection_time': collection_info[0].strftime('%Y-%m-%d %H:%M:%S') if collection_info else 'Unknown',
            'devices_attempted': collection_info[2] if collection_info else 0,
            'devices_successful': collection_info[3] if collection_info else 0,
            'total_components': len(inventory_data),
            'unique_devices': len(device_counts),
            'component_counts': component_counts,
            'top_devices': sorted(
                [{'hostname': k, 'total_components': v['total'], 'breakdown': v['by_type']} 
                 for k, v in device_counts.items()],
                key=lambda x: x['total_components'],
                reverse=True
            )[:10]
        }
        
        return {
            'inventory': inventory_data,
            'summary': summary
        }
        
    except Exception as e:
        print(f"❌ Error getting collected inventory from DB: {e}")
        import traceback
        traceback.print_exc()
        return {'inventory': [], 'summary': {'error': str(e)}}
    finally:
        if conn:
            conn.close()

# Test the function
if __name__ == '__main__':
    print("Testing get_collected_inventory_db()...")
    result = get_collected_inventory_db()
    
    summary = result['summary']
    print(f"\nCollection Summary:")
    print(f"  Collection ID: {summary.get('collection_id', 'N/A')}")
    print(f"  Collection Time: {summary.get('collection_time', 'N/A')}")
    print(f"  Devices Attempted: {summary.get('devices_attempted', 0)}")
    print(f"  Devices Successful: {summary.get('devices_successful', 0)}")
    print(f"  Total Components: {summary.get('total_components', 0)}")
    print(f"  Unique Devices: {summary.get('unique_devices', 0)}")
    
    if 'component_counts' in summary:
        print(f"\nComponent Breakdown:")
        for comp_type, count in summary['component_counts'].items():
            print(f"    {comp_type}: {count}")
    
    if 'top_devices' in summary and summary['top_devices']:
        print(f"\nTop Devices by Component Count:")
        for device in summary['top_devices'][:5]:
            print(f"    {device['hostname']}: {device['total_components']} components")
