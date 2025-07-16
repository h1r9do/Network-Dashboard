#!/usr/bin/env python3
"""
Generate formatted CSV output showing stack members and SFPs hierarchically
"""
import json
import csv

def generate_formatted_inventory_csv():
    # Load the processed inventory data
    with open('/usr/local/bin/physical_inventory_stacks_output.json', 'r') as f:
        inventory_data = json.load(f)
    
    # Create formatted CSV
    with open('/usr/local/bin/inventory_formatted.csv', 'w', newline='') as csvfile:
        fieldnames = [
            'hostname', 'ip_address', 'position', 'model', 'serial_number', 'port_location'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for device in inventory_data:
            hostname = device['hostname']
            ip = device['ip']
            chassis_list = device['physical_inventory']['chassis']
            
            # For stacked devices, show each member
            if len(chassis_list) > 1:
                # First member is Master
                writer.writerow({
                    'hostname': hostname,
                    'ip_address': ip,
                    'position': 'Master',
                    'model': chassis_list[0]['model'],
                    'serial_number': chassis_list[0]['serial'],
                    'port_location': ''
                })
                
                # Rest are Slaves
                for i in range(1, len(chassis_list)):
                    writer.writerow({
                        'hostname': '',  # Empty to show hierarchy
                        'ip_address': '',
                        'position': 'Slave',
                        'model': chassis_list[i]['model'],
                        'serial_number': chassis_list[i]['serial'],
                        'port_location': ''
                    })
            else:
                # Single device
                if chassis_list:
                    writer.writerow({
                        'hostname': hostname,
                        'ip_address': ip,
                        'position': 'Standalone',
                        'model': chassis_list[0]['model'],
                        'serial_number': chassis_list[0]['serial'],
                        'port_location': ''
                    })
            
            # List modules/blades for devices that have them
            for module in device['physical_inventory']['modules']:
                writer.writerow({
                    'hostname': '',  # Empty to show these belong to device above
                    'ip_address': '',
                    'position': 'Module',
                    'model': module['model'],
                    'serial_number': module['serial'],
                    'port_location': module['name']  # e.g., module 1, slot 7
                })
            
            # Now list SFPs/Transceivers below
            for sfp in device['physical_inventory']['transceivers']:
                writer.writerow({
                    'hostname': '',  # Empty to show these belong to device above
                    'ip_address': '',
                    'position': 'SFP',
                    'model': sfp['model'],
                    'serial_number': sfp['serial'],
                    'port_location': sfp['name']  # e.g., GigabitEthernet1/0/1
                })
    
    print(f"Formatted CSV generated: /usr/local/bin/inventory_formatted.csv")

if __name__ == "__main__":
    generate_formatted_inventory_csv()