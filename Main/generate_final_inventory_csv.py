#!/usr/bin/env python3
"""
Generate final CSV from deduplicated inventory with all enhancements
"""
import json
import csv
import re

def generate_final_csv():
    """Generate the final inventory CSV with deduplicated data"""
    
    # Load the deduplicated inventory
    try:
        with open('/usr/local/bin/Main/physical_inventory_deduplicated.json', 'r') as f:
            devices = json.load(f)
        print(f"Loaded deduplicated inventory with {len(devices)} devices")
    except FileNotFoundError:
        # Fall back to original if deduplicated doesn't exist
        print("Deduplicated file not found, using original...")
        with open('/usr/local/bin/Main/physical_inventory_stacks_output.json', 'r') as f:
            devices = json.load(f)
    
    # Generate CSV
    with open('/usr/local/bin/Main/inventory_final_check.csv', 'w', newline='') as csvfile:
        fieldnames = [
            'hostname', 'ip_address', 'position', 'model', 
            'serial_number', 'port_location', 'vendor', 'shared_with'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        device_count = 0
        component_count = 0
        
        for device in devices:
            hostname = device['hostname']
            ip = device['ip']
            chassis_list = device['physical_inventory']['chassis']
            
            # Skip if no chassis (shouldn't happen)
            if not chassis_list:
                continue
                
            device_count += 1
            
            # Handle chassis - including FEX as chassis
            if len(chassis_list) > 1:
                # For N5K/N56K, first is main chassis, rest are FEX
                main_chassis = chassis_list[0]
                if 'N5K' in main_chassis['model'] or 'N56' in main_chassis['model']:
                    # Main switch
                    writer.writerow({
                        'hostname': hostname,
                        'ip_address': ip,
                        'position': 'Parent Switch',
                        'model': main_chassis['model'],
                        'serial_number': main_chassis['serial'],
                        'port_location': '',
                        'vendor': 'Cisco',
                        'shared_with': ''
                    })
                    component_count += 1
                    
                    # FEX units
                    for i in range(1, len(chassis_list)):
                        fex = chassis_list[i]
                        fex_id = re.search(r'Fex-(\d+)', fex['name'])
                        fex_num = fex_id.group(1) if fex_id else str(100 + i)
                        
                        # Check for shared_with info
                        shared = ', '.join(fex.get('shared_with', []))
                        
                        writer.writerow({
                            'hostname': '',
                            'ip_address': '',
                            'position': f'FEX-{fex_num}',
                            'model': fex['model'],
                            'serial_number': fex['serial'],
                            'port_location': fex['name'],
                            'vendor': 'Cisco',
                            'shared_with': shared
                        })
                        component_count += 1
                else:
                    # Regular stack
                    writer.writerow({
                        'hostname': hostname,
                        'ip_address': ip,
                        'position': 'Master',
                        'model': chassis_list[0]['model'],
                        'serial_number': chassis_list[0]['serial'],
                        'port_location': '',
                        'vendor': '',
                        'shared_with': ''
                    })
                    component_count += 1
                    
                    for i in range(1, len(chassis_list)):
                        writer.writerow({
                            'hostname': '',
                            'ip_address': '',
                            'position': 'Slave',
                            'model': chassis_list[i]['model'],
                            'serial_number': chassis_list[i]['serial'],
                            'port_location': '',
                            'vendor': '',
                            'shared_with': ''
                        })
                        component_count += 1
            else:
                # Single device
                writer.writerow({
                    'hostname': hostname,
                    'ip_address': ip,
                    'position': 'Standalone',
                    'model': chassis_list[0]['model'],
                    'serial_number': chassis_list[0]['serial'],
                    'port_location': '',
                    'vendor': '',
                    'shared_with': ''
                })
                component_count += 1
            
            # List modules
            for module in device['physical_inventory']['modules']:
                shared = ', '.join(module.get('shared_with', []))
                writer.writerow({
                    'hostname': '',
                    'ip_address': '',
                    'position': 'Module',
                    'model': module['model'],
                    'serial_number': module['serial'],
                    'port_location': module['name'],
                    'vendor': '',
                    'shared_with': shared
                })
                component_count += 1
            
            # List SFPs
            for sfp in device['physical_inventory']['transceivers']:
                shared = ', '.join(sfp.get('shared_with', []))
                writer.writerow({
                    'hostname': '',
                    'ip_address': '',
                    'position': 'SFP',
                    'model': sfp.get('model', 'Unknown'),
                    'serial_number': sfp['serial'],
                    'port_location': sfp['name'],
                    'vendor': sfp.get('vendor', ''),
                    'shared_with': shared
                })
                component_count += 1
    
    print(f"\nFinal inventory CSV generated:")
    print(f"  File: /usr/local/bin/Main/inventory_final_check.csv")
    print(f"  Devices: {device_count}")
    print(f"  Total components: {component_count}")
    
    # Show sample of the CSV
    print("\nFirst 20 lines of CSV:")
    with open('/usr/local/bin/Main/inventory_final_check.csv', 'r') as f:
        for i, line in enumerate(f):
            if i < 20:
                print(f"  {line.strip()}")
            else:
                break
    
    # Show specific examples
    print("\n=== Checking specific cases ===")
    
    # Check for FEX entries
    print("\nFEX entries:")
    with open('/usr/local/bin/Main/inventory_final_check.csv', 'r') as f:
        reader = csv.DictReader(f)
        fex_count = 0
        for row in reader:
            if 'FEX' in row['position'] and fex_count < 5:
                print(f"  {row['position']}: {row['model']} (Serial: {row['serial_number']})")
                if row['shared_with']:
                    print(f"    Shared with: {row['shared_with']}")
                fex_count += 1
    
    # Check for enhanced SFPs
    print("\nEnhanced SFPs (non-Unspecified):")
    with open('/usr/local/bin/Main/inventory_final_check.csv', 'r') as f:
        reader = csv.DictReader(f)
        sfp_count = 0
        for row in reader:
            if row['position'] == 'SFP' and row['model'] != 'Unspecified' and sfp_count < 5:
                print(f"  {row['model']} - {row['vendor']} (Port: {row['port_location']})")
                sfp_count += 1
    
    # Check for stacks
    print("\nStacked devices:")
    with open('/usr/local/bin/Main/inventory_final_check.csv', 'r') as f:
        reader = csv.DictReader(f)
        current_stack = None
        stack_count = 0
        for row in reader:
            if row['position'] == 'Master':
                current_stack = row['hostname']
                stack_count += 1
                if stack_count <= 3:
                    print(f"\n  {row['hostname']}:")
                    print(f"    Master: {row['model']} ({row['serial_number']})")
            elif row['position'] == 'Slave' and current_stack and stack_count <= 3:
                print(f"    Slave: {row['model']} ({row['serial_number']})")

if __name__ == "__main__":
    generate_final_csv()