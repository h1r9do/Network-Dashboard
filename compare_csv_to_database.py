#!/usr/bin/env python3
"""
Compare inventory_ultimate_final.csv with database content
"""
import csv
import psycopg2
import json
from collections import defaultdict

def get_db_connection():
    """Connect to database"""
    return psycopg2.connect(
        host="localhost",
        database="dsrcircuits",
        user="dsruser",
        password="dsruser"
    )

def load_csv_data():
    """Load CSV data"""
    csv_data = {
        'devices': {},
        'components': defaultdict(list),
        'all_serials': set()
    }
    
    current_device = None
    
    with open('/usr/local/bin/Main/inventory_ultimate_final.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            serial = row['serial_number']
            csv_data['all_serials'].add(serial)
            
            if row['hostname']:  # Main device row
                current_device = row['hostname']
                csv_data['devices'][current_device] = {
                    'ip': row['ip_address'],
                    'position': row['position'],
                    'model': row['model'],
                    'serial': serial,
                    'vendor': row['vendor'],
                    'notes': row['notes']
                }
            else:  # Component row
                if current_device:
                    csv_data['components'][current_device].append({
                        'position': row['position'],
                        'model': row['model'],
                        'serial': serial,
                        'port_location': row['port_location'],
                        'vendor': row['vendor']
                    })
    
    return csv_data

def check_database_tables(csv_data):
    """Check various database tables for the data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    results = {}
    
    # Check comprehensive_device_inventory
    print("\n=== Checking comprehensive_device_inventory ===")
    cursor.execute("SELECT COUNT(*) FROM comprehensive_device_inventory")
    results['comprehensive_count'] = cursor.fetchone()[0]
    print(f"Total records: {results['comprehensive_count']}")
    
    # Check physical_device_inventory_v2
    print("\n=== Checking physical_device_inventory_v2 ===")
    cursor.execute("SELECT COUNT(*) FROM physical_device_inventory_v2")
    results['physical_v2_count'] = cursor.fetchone()[0]
    print(f"Total records: {results['physical_v2_count']}")
    
    # Check datacenter_inventory
    print("\n=== Checking datacenter_inventory ===")
    cursor.execute("SELECT COUNT(*) FROM datacenter_inventory")
    results['datacenter_count'] = cursor.fetchone()[0]
    print(f"Total records: {results['datacenter_count']}")
    
    # Check for specific devices from CSV
    print("\n=== Checking for specific CSV devices in database ===")
    sample_devices = list(csv_data['devices'].keys())[:5]
    
    for device in sample_devices:
        print(f"\nChecking {device}:")
        
        # Check comprehensive_device_inventory
        cursor.execute("""
            SELECT hostname, ip_address, 
                   jsonb_array_length(physical_components->'chassis') as chassis_count,
                   jsonb_array_length(physical_components->'modules') as module_count
            FROM comprehensive_device_inventory 
            WHERE hostname = %s
        """, (device,))
        comp_result = cursor.fetchone()
        if comp_result:
            print(f"  Found in comprehensive_device_inventory: {comp_result[2]} chassis, {comp_result[3]} modules")
        
        # Check physical_device_inventory_v2
        cursor.execute("""
            SELECT hostname, chassis_model, chassis_serial, module_count
            FROM physical_device_inventory_v2 
            WHERE hostname = %s
        """, (device,))
        phys_result = cursor.fetchone()
        if phys_result:
            print(f"  Found in physical_device_inventory_v2: {phys_result[1]} ({phys_result[2]}), {phys_result[3]} modules")
        
        # Check datacenter_inventory
        cursor.execute("""
            SELECT hostname, model, serial_number 
            FROM datacenter_inventory 
            WHERE hostname = %s
        """, (device,))
        dc_result = cursor.fetchone()
        if dc_result:
            print(f"  Found in datacenter_inventory: {dc_result[1]} ({dc_result[2]})")
    
    # Check for serials in various tables
    print("\n=== Checking serial numbers ===")
    sample_serials = list(csv_data['all_serials'])[:10]
    
    for serial in sample_serials:
        found_in = []
        
        # Check datacenter_inventory
        cursor.execute("SELECT COUNT(*) FROM datacenter_inventory WHERE serial_number = %s", (serial,))
        if cursor.fetchone()[0] > 0:
            found_in.append('datacenter_inventory')
        
        # Check physical_device_inventory_v2
        cursor.execute("SELECT COUNT(*) FROM physical_device_inventory_v2 WHERE chassis_serial = %s", (serial,))
        if cursor.fetchone()[0] > 0:
            found_in.append('physical_device_inventory_v2')
        
        if found_in:
            print(f"  Serial {serial}: found in {', '.join(found_in)}")
        else:
            print(f"  Serial {serial}: NOT FOUND in database")
    
    cursor.close()
    conn.close()
    
    return results

def main():
    print("Loading CSV data...")
    csv_data = load_csv_data()
    
    print(f"\nCSV Summary:")
    print(f"  Devices: {len(csv_data['devices'])}")
    print(f"  Total serials: {len(csv_data['all_serials'])}")
    print(f"  Total rows: {len(csv_data['all_serials'])}")
    
    # Show sample data
    print("\nSample CSV data:")
    for i, (hostname, device) in enumerate(csv_data['devices'].items()):
        if i < 3:
            print(f"  {hostname}: {device['model']} ({device['serial']})")
            components = csv_data['components'].get(hostname, [])
            for comp in components[:2]:
                print(f"    - {comp['position']}: {comp['model']} ({comp['serial']})")
    
    # Check database
    results = check_database_tables(csv_data)
    
    print("\n=== SUMMARY ===")
    print(f"CSV has {len(csv_data['devices'])} devices with {len(csv_data['all_serials'])} total components")
    print(f"Database tables:")
    print(f"  comprehensive_device_inventory: {results['comprehensive_count']} records")
    print(f"  physical_device_inventory_v2: {results['physical_v2_count']} records")
    print(f"  datacenter_inventory: {results['datacenter_count']} records")

if __name__ == "__main__":
    main()