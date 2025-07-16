#!/usr/bin/env python3
"""
Generate CSV output of physical inventory data
Shows line-by-line how each device/component is parsed
"""
import json
import csv

def generate_inventory_csv():
    # Load the processed inventory data
    with open('/usr/local/bin/physical_inventory_stacks_output.json', 'r') as f:
        inventory_data = json.load(f)
    
    # Create CSV with detailed component breakdown
    with open('/usr/local/bin/physical_inventory_parsed.csv', 'w', newline='') as csvfile:
        fieldnames = [
            'hostname', 'ip_address', 'component_type', 'model', 
            'serial_number', 'description', 'name', 'stack_position'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for device in inventory_data:
            hostname = device['hostname']
            ip = device['ip']
            
            # Write chassis entries (one line per stack member)
            for i, chassis in enumerate(device['physical_inventory']['chassis']):
                writer.writerow({
                    'hostname': hostname,
                    'ip_address': ip,
                    'component_type': 'Chassis',
                    'model': chassis['model'],
                    'serial_number': chassis['serial'],
                    'description': chassis['description'],
                    'name': chassis['name'],
                    'stack_position': f"Member {i+1}" if len(device['physical_inventory']['chassis']) > 1 else "Standalone"
                })
            
            # Write modules
            for module in device['physical_inventory']['modules']:
                writer.writerow({
                    'hostname': hostname,
                    'ip_address': ip,
                    'component_type': 'Module',
                    'model': module['model'],
                    'serial_number': module['serial'],
                    'description': module['description'],
                    'name': module['name'],
                    'stack_position': ''
                })
            
            # Write power supplies
            for psu in device['physical_inventory']['power_supplies']:
                writer.writerow({
                    'hostname': hostname,
                    'ip_address': ip,
                    'component_type': 'Power Supply',
                    'model': psu['model'],
                    'serial_number': psu['serial'],
                    'description': psu['description'],
                    'name': psu['name'],
                    'stack_position': ''
                })
            
            # Write fans
            for fan in device['physical_inventory']['fans']:
                writer.writerow({
                    'hostname': hostname,
                    'ip_address': ip,
                    'component_type': 'Fan',
                    'model': fan['model'],
                    'serial_number': fan['serial'],
                    'description': fan['description'],
                    'name': fan['name'],
                    'stack_position': ''
                })
            
            # Write transceivers/SFPs
            for sfp in device['physical_inventory']['transceivers']:
                writer.writerow({
                    'hostname': hostname,
                    'ip_address': ip,
                    'component_type': 'SFP/Transceiver',
                    'model': sfp['model'],
                    'serial_number': sfp['serial'],
                    'description': sfp['description'],
                    'name': sfp['name'],
                    'stack_position': ''
                })
    
    print(f"CSV generated: /usr/local/bin/physical_inventory_parsed.csv")
    
    # Also create a summary CSV focusing on 3750 stacks
    with open('/usr/local/bin/3750_stacks_summary.csv', 'w', newline='') as csvfile:
        fieldnames = [
            'hostname', 'ip_address', 'stack_size', 'models', 'serial_numbers', 'sfp_count'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for device in inventory_data:
            if '3750' in device['hostname'] or '3750' in str(device['physical_inventory']):
                writer.writerow({
                    'hostname': device['hostname'],
                    'ip_address': device['ip'],
                    'stack_size': device['summary']['chassis_count'],
                    'models': device['summary']['chassis_model'],
                    'serial_numbers': device['summary']['chassis_serial'],
                    'sfp_count': device['summary']['transceiver_count']
                })
    
    print(f"3750 summary CSV generated: /usr/local/bin/3750_stacks_summary.csv")

if __name__ == "__main__":
    generate_inventory_csv()